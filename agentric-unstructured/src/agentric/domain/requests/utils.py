from __future__ import annotations

import io
import json
import mimetypes
import os
from collections.abc import Sequence
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from json import JSONDecodeError
from pathlib import Path
import pathlib
from typing import Any

import aiofile
import mammoth
import structlog
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader, select_autoescape
from opentelemetry import trace
from PyPDF2 import PdfReader

# from weasyprint import HTML
from agentric.config.base import get_settings
from agentric.db.models.enums import ClaimStatus
from agentric.db import models as m
from agentric.domain.chats.schemas import ToolResultReponse
from agentric.domain.requests import schemas as s
from agentric.domain.requests.rule_sets import (
    cover_more_document_check,
)

logger = structlog.get_logger()


__all__ = [
    "clean_llm_output",
    "extract_first_page_text",
    "generate_data_structure",
    "generate_decision_summary",
    "generate_decline_email_template",
    "generate_missing_email_template",
    "read_async_json",
]

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger()
settings = get_settings()
template_dir = os.path.join("templates")

env = Environment(
    loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
)

EXT_MIME_MAP = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".html": "text/html",
    ".htm": "text/html",
    ".eml": "message/rfc822",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def get_classification(request: m.Request) -> ToolResultReponse:
    extraction = s.Extraction.model_validate(request.extraction)
    extraction_data = extraction.extracted_data
    data = get_main_fields(request, extraction_data)

    return ToolResultReponse(
        type="CLASSIFICATION_REQUEST",
        results=[data],
    )


def get_main_fields(
    request: m.Request, all_extracted_data: dict[str, Any]
) -> dict[str, Any]:
    airline_refund_case = "N/A"
    data = all_extracted_data["claim_form"]

    return {
        "type_of_claim": request.type_of_claim,
        "submission_method": data["claim_info"]["submission_method"],
        "policy_number": request.policy_number,
        "client_name": request.client_name,
        "client_email": request.client_email_address,
        "mobile_phone": request.client_phone_number,
        "insurance_agency_name": "N/A",  # request.broker_name,
        "initial_deposit_date": data["claimer_info"]["initial_deposit_date"] or "N/A",
        "case_description": request.description,
        "date_of_loss": data["claim_details"]["date_of_loss"],
        "requested_reimbursement_amount": request.requested_reimbursement_amount,
        "request_airline_refunds": airline_refund_case,
    }


async def extract_first_page_text(content_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(content_bytes))
    first_page = reader.pages[0]
    return first_page.extract_text() or ""


async def nested_dict_from_flat(flat_fields: dict) -> dict[str, Any]:
    """Convert flattened field keys into a nested JSON object."""
    nested = {}
    for full_key, meta in flat_fields.items():
        parts = full_key.split(".")
        cur = nested
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = "example_value" if meta["required"] else "optional_value"
    return nested


async def read_async_json(filepath: str) -> dict:
    async with aiofile.async_open(filepath, "r", encoding="utf-8") as f:
        schema_content = await f.read()
        return json.loads(schema_content)


async def handle_claims(
    attachments: Sequence[m.RequestAttachment],
    user_id: str,
    email: str,
    session_id: str,
    model_name: str = "gemini-2.5-pro",
) -> dict[str, Any]:
    from agentric.lib.utils import read_minio_file

    with tracer.start_as_current_span("claim_extraction") as span:

        span.set_attribute("function.name", "handle_claims")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)

        uploaded_files = []
        failed_files = []
        prompt = """
    - You are a Claim Adjuster working for an Insurance company.
    Your job is to analyze Claim Submission and determine whether the claim is covered by the attached policy.
    If it is covered, determine whether there is enough supplemental attachments to determine the validity of the Claim.
    If the Claim is valid and is covered by the policy, then using the attached receipts and Policy limits, calculate the amount payable. 
    If the claim is not covered, provide an excerpt from the policy stating why the claim is not covered.
    Assume that the attached policy is a purchased policy by the claimant. You can use markdown here.

    - Include Extracted Structured data in Correct JSON format in below <script> tag.
    Fill Structured JSON EXTRACTION RESULT BELOW in Valid JSON Values. Avoid Markdown inside.

    <script language="json">
    {
    "policy_data" : {},
    "claims_data" : {},
    "
    }
    </script>

    """
        for attachment in attachments:
            # Detect mime type (fallback to octet-stream if unknown)
            mime_type, _ = mimetypes.guess_type(attachment.file_name)
            if mime_type is None:
                mime_type = "application/octet-stream"

            try:
                content_bytes = await read_minio_file(attachment.url)
                file_bytes = io.BytesIO(content_bytes)
                uploaded = client.files.upload(
                    file=file_bytes, config={"mime_type": mime_type}
                )
                uploaded_files.append(uploaded)
            except Exception as e:
                failed_files.append(
                    {"filename": str(attachment.file_name), "reason": str(e)}
                )

        if failed_files:
            logger.debug("⚠️ Some files could not be uploaded")
            logger.debug(failed_files)
        if not uploaded_files:
            msg = "No files are uploaded!"
            raise RuntimeError(msg)
        response = client.models.generate_content(
            model=model_name,
            contents=[*uploaded_files, prompt],
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(include_thoughts=True),
                temperature=0,
            ),
        )

        thoughts = ""
        results = ""
        assert response.candidates is not None

        content = response.candidates[0].content

        assert content is not None
        assert content.parts is not None

        input_tokens = response.usage_metadata.prompt_token_count or 0  # type: ignore
        output_tokens = response.usage_metadata.candidates_token_count or 0  # type: ignore
        total_tokens = response.usage_metadata.total_token_count or 0  # type: ignore

        span.set_attribute("genai.request_token_usage", input_tokens)
        span.set_attribute("genai.response_token_usage", output_tokens)
        span.set_attribute("genai.total_token_usage", total_tokens)
        span.set_attribute("genai.model", model_name)

        for part in content.parts:
            if not part.text:
                continue
            if hasattr(part, "thought") and part.thought:
                thoughts += part.text
            else:
                results += part.text
        logger.info("Stage 1: Finished data extraction from claim form")
        logger.info(thoughts)
        logger.info(results)
        extracted = {}
        soup = BeautifulSoup(results, "html.parser")

        # Find the <extraction> tag
        extraction_tag = soup.find("script")
        if extraction_tag:
            try:
                extracted = json.loads(extraction_tag.get_text(strip=True))
                extraction_tag.decompose()
                results = soup.get_text()
            except:
                extracted = {}

        return {"decision": results, "thoughts": thoughts, "extracted": extracted}


async def extract_all_info(
    hotel_doc: list[m.RequestAttachment] | None,
    claim_summary_doc: m.RequestAttachment | None,
    policy_summary_doc: m.RequestAttachment | None,
    session_id: str,
    email: str,
    user_id: str,
    model_name: str = "gemini-2.5-pro",
):
    from agentric.lib.utils import read_minio_file

    with tracer.start_as_current_span("claim_extraction") as span:
        span.set_attribute("function.name", "extract_all_info")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)
        schema_text = Path("schema/claim_info.json").read_text(encoding="utf-8")
        prompt = """
        You are an Insurance Information Extractor.

        GOAL
        Read ALL pages/content of the attached file and extract fields defined in the JSON schema below.
        Return EXACTLY ONE JSON object that VALIDATES against the schema.


        <schema>
        {JSON_SCHEMA}
        </schema>

        NORMALIZATION
        - Dates: use ISO `YYYY-MM-DD` (schema uses "format": "date", not date-time).
        - Email: plain lowercase address (no labels).
        - Strings: trim whitespace; keep plain text (no labels).
        - Currency/limits in coverages: keep them AS SHOWN (e.g., "$150 Per Insured", "100% Per Booking").

        CONFLICTS OR MISSING VALUES
        - If truly not found for a REQUIRED field, return an empty string "" to preserve the JSON shape (but search thoroughly first).

        STRICT OUTPUT
        - Return ONLY the JSON object that conforms to the schema.
        - No code fences, no explanations, no extra keys.
        """.replace(
            "{JSON_SCHEMA}", schema_text
        )

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)
        uploaded_files = []
        attachments = []

        if claim_summary_doc:
            attachments.append(claim_summary_doc)
        if policy_summary_doc:
            attachments.append(policy_summary_doc)
        if hotel_doc:
            attachments.extend(hotel_doc)
        for attachment in attachments:
            mime_type, _ = mimetypes.guess_type(attachment.file_name)
            if mime_type is None:
                mime_type = "application/octet-stream"

            try:
                content_bytes = await read_minio_file(attachment.url)
                file_bytes = io.BytesIO(content_bytes)
                uploaded = client.files.upload(
                    file=file_bytes, config={"mime_type": mime_type}
                )
                uploaded_files.append(uploaded)
            except Exception as e:
                alert_mesg = (
                    f"⚠️ Some files {attachment.file_name} could not be uploaded"
                )
                logger.debug(alert_mesg)
                logger.debug(e)
                continue

        response = client.models.generate_content(
            model=model_name,
            contents=[uploaded_files, prompt],
            config=genai.types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        um = response.usage_metadata
        input_tokens = um.prompt_token_count or 0  # type: ignore
        output_tokens = um.candidates_token_count or 0  # type: ignore
        total_tokens = um.total_token_count or 0  # type: ignore

        span.set_attribute("genai.request_token_usage", input_tokens)
        span.set_attribute("genai.response_token_usage", output_tokens)
        span.set_attribute("genai.total_token_usage", total_tokens)
        span.set_attribute("genai.model", model_name)

        if response.text is None:
            msg = "Response text is None!"
            raise RuntimeError(msg)

        data = json.loads(response.text)

        # If there is no provided file for corresponding data, overrride it with empty value to nevigate AI Hallucination
        nullify_sections = []
        if hotel_doc is None:
            nullify_sections.append("hotel_data")

        if claim_summary_doc is None:
            nullify_sections.append("claim_data")

        if policy_summary_doc is None:
            nullify_sections.append("policy_data")

        return (
            data
            if nullify_sections
            else override_sections_with_none(data, nullify_sections)
        )


def _nullify_structure(value: Any) -> Any:
    """Recursively replace leaf values with None, preserving dict/list shape."""
    if isinstance(value, dict):
        return {k: _nullify_structure(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_nullify_structure(v) for v in value]
    # primitives (str, int, float, bool, None, etc.)
    return None


def override_sections_with_none(
    data: dict[str, Any], section_keys: list[str]
) -> dict[str, Any]:
    """For each top-level `<name>_data` in `data`, if corresponding `<name>_doc` is falsy (None/empty),
    replace that section with a shape-preserving version where all leaves are None.
    """
    for section_key in section_keys:
        section_value = data.get(section_key)
        data[section_key] = _nullify_structure(section_value)
    return data


async def handle_missing(
    attachments: Sequence[m.RequestAttachment],
    missing_list: list[dict],
    user_id: str,
    email: str,
    session_id: str,
    model_name: str = "gemini-2.5-pro",
) -> dict[str, Any]:
    from agentric.lib.utils import read_minio_file

    with tracer.start_as_current_span("claim_extraction") as span:

        span.set_attribute("function.name", "handle_missing")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)

        uploaded_files = []
        failed_files = []

        prompt = f"""
        - You are a Claim Adjuster AI Agent Assisting Claim Handler who is working for an Insurance company. You've found out that required filed are missing.
         According to the data {missing_list}  explain which files are missing files and their reasons to Claims Handler. Be short and consise.
        - Then from remaining files , Include Extracted Structured data in STRICTLY CORRECT JSON format in below <script> tag.
        Fill Structured JSON EXTRACTION RESULT BELOW in Valid JSON Values. Avoid Markdown inside. DO NOT PUT ANY EXTRA TEXT , JUST JSON.

        <script language="json">
        {{
        "policy_data" : {{}},
        "claims_data" : {{}}
        }}
        </script>
        """
        for attachment in attachments:
            # Detect mime type (fallback to octet-stream if unknown)
            mime_type, _ = mimetypes.guess_type(attachment.file_name)
            if mime_type is None:
                mime_type = "application/octet-stream"

            try:
                content_bytes = await read_minio_file(attachment.url)
                file_bytes = io.BytesIO(content_bytes)
                uploaded = client.files.upload(
                    file=file_bytes, config={"mime_type": mime_type}
                )
                uploaded_files.append(uploaded)
            except Exception as e:
                failed_files.append(
                    {"filename": str(attachment.file_name), "reason": str(e)}
                )

        if failed_files:
            logger.debug("⚠️ Some files could not be uploaded")
            logger.debug(failed_files)
        if not uploaded_files:
            msg = "No files are uploaded!"
            raise RuntimeError(msg)
        response = client.models.generate_content(
            model=model_name,
            contents=[*uploaded_files, prompt],
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(include_thoughts=True),
                temperature=0,
            ),
        )

        thoughts = ""
        results = ""
        assert response.candidates is not None

        content = response.candidates[0].content

        assert content is not None
        assert content.parts is not None

        input_tokens = response.usage_metadata.prompt_token_count or 0  # type: ignore
        output_tokens = response.usage_metadata.candidates_token_count or 0  # type: ignore
        total_tokens = response.usage_metadata.total_token_count or 0  # type: ignore

        span.set_attribute("genai.request_token_usage", input_tokens)
        span.set_attribute("genai.response_token_usage", output_tokens)
        span.set_attribute("genai.total_token_usage", total_tokens)
        span.set_attribute("genai.model", model_name)

        for part in content.parts:
            if not part.text:
                continue
            if hasattr(part, "thought") and part.thought:
                thoughts += part.text
            else:
                results += part.text
        logger.info("Stage 1: Finished data extraction from claim form")
        logger.info(thoughts)
        logger.info(results)
        extracted = {}
        soup = BeautifulSoup(results, "html.parser")

        # Find the <extraction> tag
        extraction_tag = soup.find("script")
        if extraction_tag:
            try:
                extracted = json.loads(extraction_tag.get_text(strip=True))
                extraction_tag.decompose()
                results = soup.get_text()
            except:
                extracted = {}

        return {"decision": results, "thoughts": thoughts, "extracted": extracted}


async def generate_decision_summary(
    request: m.Request,
    attachments: list[m.RequestAttachment],
) -> str:
    client = genai.Client(api_key=settings.app.AGENT_API_KEY)
    gen_decision = request.generated_decisions
    prompt = "Generate Decision Summary for insurance claims based upon input"
    if gen_decision:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[gen_decision, prompt],
            config={"response_mime_type": "text/plain", "temperature": 0.0, "seed": 42},
        )

        return response.text or ""
    return ""


async def generate_followup_question(
    status: str,
) -> str:
    match status:
        case ClaimStatus.APPROVED.value:
            response = "Your claim got approved. What would you like to do next?"
        case ClaimStatus.DECLINED.value:
            response = "The claim got declined. What would you like to do next?"
        case ClaimStatus.PARTIAL_PAYMENT.value:
            response = "The claim got partial payment due to coverage gap. What would you like to do next?"
        case ClaimStatus.MISSING.value:
            response = "The claim is missing information required for claim review. What would you like to do next?"
        case _:
            response = "Your claim status {status}. What would you like to do next?"

    return response


async def generate_data_structure(
    data: dict,
    user_id: str,
    policy_detail_file: m.RequestAttachment | None,
    email: str,
    session_id: str,
    model_name: str = "gemini-2.5-pro",
) -> dict[str, Any]:
    from agentric.lib.utils import read_minio_file

    with tracer.start_as_current_span("claim_extraction") as span:
        span.set_attribute("function.name", "generate_data_structure")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)

        schema_filename = "general_claim.json"
        schema_text = Path("schema/" + schema_filename).read_text(encoding="utf-8")

        prompt = f"""You are an expert data extraction AI specializing in insurance claims processing. Your task is to meticulously analyze the provided set of documents, which may include claim forms, receipts, and insurance policy details.

        From these documents, you must extract the specified information and perform a basic analysis to populate the decision-related fields. Your output must be a single, valid JSON object that strictly conforms to the JSON schema provided below.

        **Instructions:**
        1.  **Analyze All Documents:** Carefully read through all provided input to find the required information.
        2.  **Handle Missing Information:** If a piece of information cannot be found in the input for a specific field, use `null` as the value. Do not invent or infer data for non-analytical fields.
        3.  **Analytical Fields:** For fields like `status`, `generated_decision_summary`, and `decision_reason`, you must perform a brief analysis based on the claim details and the policy coverage.
            *   `status`: Determine if the claim must be one of these statuses: 'APPROVED' or 'DENIED', , based on the policy terms.
            *   `submission_status`: If a decision can be made, set this to 'COMPLETED'. Otherwise, 'PROCESSING'.
            *   `generated_decision_summary`: Write a concise, one or two-sentence summary explaining the outcome of the claim analysis.
        4.  **Data Formatting:**
            *   **Dates:** Format all dates and datetimes as ISO 8601 strings (e.g., "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS").
            *   **Amounts:** Extract monetary values as strings, preserving the currency symbol if present (e.g., "$251.51").

        ### Schema
        {schema_text}

        ### Analysis outcome
        {json.dumps(data)}
        """

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)
        uploaded = None
        if policy_detail_file is not None:
            content_bytes = await read_minio_file(policy_detail_file.url)
            file_bytes = io.BytesIO(content_bytes)
            mime_type, _ = mimetypes.guess_type(policy_detail_file.file_name)

            uploaded = client.files.upload(
                file=file_bytes, config={"mime_type": mime_type}
            )

        contents = [prompt]

        if uploaded is not None:
            contents = [uploaded, prompt]
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(),
                temperature=1,
                response_mime_type="application/json",
            ),
        )
        um = response.usage_metadata

        input_tokens = um.prompt_token_count or 0  # type: ignore
        output_tokens = um.candidates_token_count or 0  # type: ignore
        total_tokens = um.total_token_count or 0  # type: ignore

        span.set_attribute("genai.request_token_usage", input_tokens)
        span.set_attribute("genai.response_token_usage", output_tokens)
        span.set_attribute("genai.total_token_usage", total_tokens)
        span.set_attribute("genai.model", model_name)

        results = ""
        assert response.candidates is not None

        content = response.candidates[0].content

        assert content is not None and content.parts is not None
        for part in content.parts:
            if not part.text:
                continue
            results += part.text
        return json.loads(results)


async def generate_data_structure_missing_case(
    data: dict[str, Any],
    user_id: str,
    email: str,
    session_id: str,
    missing_file_list: list,
    model_name: str = "gemini-2.5-pro",
) -> dict[str, Any]:

    with tracer.start_as_current_span("claim_extraction") as span:
        span.set_attribute("function.name", "generate_data_structure")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)

        schema_filename = "general_claim.json"
        schema_text = Path("schema/" + schema_filename).read_text(encoding="utf-8")
        prompt = f"""
            You are an expert data extraction AI specializing in insurance claims processing. Your task is to meticulously analyze the provided set of documents, which may include claim forms, receipts, and insurance policy details.

            From these documents, you must extract the specified information and perform a basic analysis to populate the decision-related fields. Your output must be a single, valid JSON object that strictly conforms to the JSON schema provided below.

            **Instructions:**
            1.  **Analyze All Documents:** Carefully read through all provided input to find the required information.
            2.  **Handle Missing Information:** If a piece of information cannot be found in the input for a specific field, use `null` as the value. Do not invent or infer data for non-analytical fields.
            3.  **Analytical Fields:** For fields like `status`, `generated_decision_summary`, `missing_documents`, and `decision_reason`, you must perform a brief analysis based on the claim details and the policy coverage.
                *   `status`:  'MISSING'.
                *   `submission_status`: If a decision can be made, set this to 'COMPLETED'. Otherwise, 'PROCESSING'.
                *   `missing_documents`: List any documents that are required by the policy for approval but are not present (e.g., "Physician's report certifying the injury").
                *   `generated_decision_summary`: Write a concise, one or two-sentence summary explaining the outcome of the claim analysis.
            4.  **Data Formatting:**
                *   **Dates:** Format all dates and datetimes as ISO 8601 strings (e.g., "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS").
                *   **Amounts:** Extract monetary values as strings, preserving the currency symbol if present (e.g., "$251.51").

            ### Schema
            {schema_text}

            ### Missing file list
            {missing_file_list}

            ### Analysis outcome
            {json.dumps(data)}

            """

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                thinking_config=genai.types.ThinkingConfig(),
                temperature=1,
                response_mime_type="application/json",
            ),
        )
        um = response.usage_metadata

        input_tokens = um.prompt_token_count or 0  # type: ignore
        output_tokens = um.candidates_token_count or 0  # type: ignore
        total_tokens = um.total_token_count or 0  # type: ignore

        span.set_attribute("genai.request_token_usage", input_tokens)
        span.set_attribute("genai.response_token_usage", output_tokens)
        span.set_attribute("genai.total_token_usage", total_tokens)
        span.set_attribute("genai.model", model_name)

        results = ""
        assert response.candidates is not None

        content = response.candidates[0].content

        assert content is not None and content.parts is not None
        for part in content.parts:
            if not part.text:
                continue
            results += part.text
        return json.loads(results)


async def clean_llm_output(llm_response: dict) -> dict:
    """Removes any fields from Claude's response that say 'No information found in document.'

    Args:
        llm_response (dict): Full response from Claude.

    Returns:
        dict: Filtered dictionary with only valid coverage recommendations.
    """
    return {
        key: value
        for key, value in llm_response.items()
        if isinstance(value, str) and "no information found" not in value.lower()
    }


async def flatten_schema_for_prompt(schema: dict, parent_key="") -> dict:
    """Flatten nested JSON schema fields into dot notation with descriptions."""
    flat_fields = {}
    for key, val in schema.get("properties", {}).items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if val.get("type") == "object" and "properties" in val:
            data = await flatten_schema_for_prompt(val, full_key)
            flat_fields.update(data)
        else:
            description = val.get("description", "No description provided")
            flat_fields[full_key] = description
    return flat_fields


async def generate_decline_email_template(
    reasoning: str,
    from_email: str,
    to_email: str,
    broker_name: str,
    request_id: str,
) -> MIMEMultipart:
    template = env.get_template("decline_email.html")

    print("--- Generating Decline Email (Property Condition) ---")
    context = {
        "request_id": request_id,
        "decline_reason": reasoning,
        "broker_name": broker_name,
        "to_email": to_email,
        "from_email": from_email,
    }
    html_body = template.render(context)
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "Decline Email for Zurich Travel Insurance Application"
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


async def generate_policy_documentation_email(
    policy_details: dict, from_email: str, to_email: str, request_id: str
) -> MIMEMultipart:
    template = env.get_template("policy_documentation.html")

    context = {
        "request_id": request_id,
        "policy_details": policy_details,
        "to_email": to_email,
        "from_email": from_email,
    }

    html_body = template.render(context)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email

    msg["Subject"] = " Policy Documentation for Zurich Travel Insurance"

    msg.attach(MIMEText(html_body, "html"))

    return msg


async def generate_missing_email_template(
    missing_files: list[str],
    from_email: str,
    to_email: str,
    broker_name: str,
    request: m.Request,
) -> MIMEMultipart:
    """Generates an email to a broker requesting missing information for a Zurich Travel insurance application.

    Args:
        missing_files (dict): A dictionary where keys are the names of the missing files
                               and values are descriptions of what is needed.
        from_email (str): The sender's email address.
        to_email (str): The recipient's (broker's) email address.
        request_id (str): The unique identifier for the insurance application.

    Returns:
        MIMEMultipart: The fully formed email object.
    """

    template = env.get_template("missing_email.html")

    context = {
        "client_name": request.client_name or "[CLIENT_NAME]",
        "request_id": str(request.id),
        "missing_files": missing_files,
        "to_email": to_email,
        "from_email": from_email,
        "broker_name": broker_name,
    }

    html_body = template.render(context)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email

    msg["Subject"] = "Travel claim information request"

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


async def generate_approved_email_template(
    from_email: str,
    to_email: str,
    request: m.Request,
) -> MIMEMultipart:
    """Generates an email to a broker for approving information for a Zurich travel insurance application.

    Args:
        decision_reason: str
        from_email (str): The sender's email address.
        to_email (str): The recipient's (broker's) email address.
        request_id (str): The unique identifier for the insurance application.

    Returns:
        MIMEMultipart: The fully formed email object.
    """

    template = env.get_template("approve_email.html")

    context = {
        "client_name": request.client_name or "N/A",
        "broker_name": "N/A",  # request.broker_name
        "policy_holder": request.policy_holder or "N/A",
        "claim_number": request.claim_number or "N/A",
        "policy_number": request.policy_number or "N/A",
        "decision_date": request.updated_at or "[DECISION_DATE]",
        "claim_type": request.type_of_claim or "[CLAIM_TYPE]",
        "claim_type_reason": request.description or "[CLAIM_TYPE_REASON]",
        "claim_amount": request.requested_reimbursement_amount or "N/A",
        "approved_amount": request.approved_amount or "N/A",
        "covered_areas": [
            {"name": "Airline cancellation penalties", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Hotel cancellation fees:", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Tour cancellation charges", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Insurance premium", "amount": "[SAMPLE_AMOUNT]"},
        ],
        "insurance_premium": request.premium_amount or "[INSURANCE_PREMIUM]",
        "to_email": to_email,
        "from_email": from_email,
    }

    html_body = template.render(context)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email

    msg["Subject"] = " Information for Zurich Travel Insurance"

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


async def generate_partial_payment_email_template(
    from_email: str,
    to_email: str,
    request: m.Request,
) -> MIMEMultipart:
    """Generates an email to a client for partial payment information for a Zurich travel insurance application.

    Args:
        decision_reason: str
        from_email (str): The sender's email address.
        to_email (str): The recipient's (broker's) email address.
        request_id (str): The unique identifier for the insurance application.

    Returns:
        MIMEMultipart: The fully formed email object.
    """

    template = env.get_template("partial_payment.html")

    context = {
        "client_name": request.client_name or "[CLIENT_NAME]",
        "broker_name": "[BROKER_NAME]",  # request.broker_name
        "policy_holder": request.policy_holder or "[POLICY_HOLDER]",
        "claim_number": request.claim_number or "[CLAIM_NUMBER]",
        "policy_number": request.policy_number or "[POLICY_NUMBER]",
        "decision_date": request.updated_at or "[DECISION_DATE]",
        "claim_type": request.type_of_claim or "[CLAIM_TYPE]",
        "claim_type_reason": request.decision_reason or "[CLAIM_TYPE_REASON]",
        "claim_amount": request.requested_reimbursement_amount or "[CLAIM_AMOUNT]",
        "total_requested_amount": request.requested_reimbursement_amount
        or "[TOTAL_REQUESTED_AMOUNT]",
        "approved_amount": request.approved_amount or "[APPROVED_AMOUNT]",
        "covered_areas": [
            {"name": "Airline cancellation penalties", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Hotel cancellation fees:", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Tour cancellation charges", "amount": "[SAMPLE_AMOUNT]"},
            {"name": "Insurance premium", "amount": "[SAMPLE_AMOUNT]"},
        ],
        "insurance_premium": request.premium_amount or "[INSURANCE_PREMIUM]",
        "to_email": to_email,
        "from_email": from_email,
    }

    html_body = template.render(context)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email

    msg["Subject"] = " Information for Zurich Travel Insurance"

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


def extract_first_two_pages(pdf_content_bytes: bytes) -> str:

    reader = PdfReader(BytesIO(pdf_content_bytes))
    pages = min(2, len(reader.pages))
    text = ""
    for i in range(pages):
        page = reader.pages[i]
        text += (page.extract_text() or "") + "\n"
    return " ".join(text.split())


async def classified_travelguard_docs(
    attachments: list[m.RequestAttachment], model_name: str = "gemini-2.5-flash"
) -> list[s.ClassifedDocument]:
    from agentric.lib.utils import read_minio_file

    parts = []
    for attachment in attachments:
        suffix = attachment.file_name.split(".")[-1]
        content_bytes = await read_minio_file(attachment.url)
        if suffix.lower() == ".pdf":
            txt = extract_first_two_pages(content_bytes)
            data = txt.encode()
            mime_type = "text/plain"

        else:
            mime_type, _ = mimetypes.guess_type(attachment.file_name)
            if mime_type is None:
                mime_type = "application/octet-stream"
            data = await read_minio_file(attachment.url)
        parts.append({"text": f"[FILENAME:{attachment.file_name}]"})
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    system_prompt = """
    You are a STRICT file-type classifier for Zurich travel-insurance-related claim documents.
    Return results using the 'classify_files' tool. Output EXACTLY one label per file from:

    - full_policy
    - policy_summary
    - claim_summary
    - hotel_booking
    - evidences

    CLASSIFICATION PRIORITY (stop at first match):
    1) Full insurance policy document → full_policy
    2) Summary of policy → policy_summary
    3) Claim form or structured claim summary → claim_summary
    4) Hotel booking confirmation, itinerary, or receipt → hotel_booking
    5) Otherwise → evidences

    DEFINITIONS

    full_policy
    - Complete “Policy of Insurance” or certificate containing:
    • Legal wording and clauses (sections like: GENERAL EXCLUSIONS, BENEFITS, DEFINITIONS, PAYMENT OF CLAIMS)
    • Tables of contents or section numbering
    • Mentions of insurer (Zurich, GoReady, National Union Fire Insurance Company)
    • Coverage terms, claim procedures, or contract details
    • Usually multi-page, formal wording booklet format

    policy_summary
    - A concise confirmation/summary page for a purchased (or quoted) travel insurance plan.
    - Typically shows plan/product name, policy number or ID, coverage effective date,
    trip dates, total cost, trip cost, contact/policy holder info, and
    a section like "Coverages and Benefit Limits".

    claim_summary
    - Official claim or summary forms that include structured fields such as:
    • Claimant name, policy number, claim type (Trip Interruption, Cancellation, etc.)
    • Dates of travel, date of loss, description of event or illness
    • Expense breakdowns (“Breakdown of Claimant's Expense”, “Claim Amount”, “Total Expected Refunds”)
    • Illness/medical sections (“Who became ill?”, “Symptom onset date”, etc.)
    • Fraud statement, declaration, or signature area

    hotel_booking
    - Hotel reservation confirmations, booking receipts, or pricing summaries (from Expedia, Booking.com, etc.).
    - Characteristic cues:
    • “Check in” / “Check out” dates
    • “Nights • Adults • Rooms” summary lines
    • Property name or address
    • Room type and total price (e.g. “Total $296.27 Paid”)
    • Reservation / confirmation numbers
    - These documents show travel arrangements, not insurance or claim content.
    evidences
    - Any supporting documents that are NOT policy, claim form, or hotel booking, such as:
    • Receipts, invoices, doctor letters, refund messages, transport cancellations
    • Screenshots or email correspondence used as proof
    • Bank transaction statements or supporting proof of payment

    CHECKLIST (apply in order; stop at first YES):
    [ ] Does the file contain policy terms, benefits, exclusions, or insurer clauses? → full_policy
    [ ] Does the file contain a concise summary of a purchased travel insurance plan? → policy_summary
    [ ] Does the file have structured claim fields (policy number, claim reason, expense breakdown)? → claim_summary
    [ ] Does the file describe a hotel reservation or accommodation stay (check-in/out, nights, room info, total)? → hotel_booking
    [ ] Otherwise → evidences

    OUTPUT FORMAT
    Return ONLY a JSON object exactly as below:
    {"filename": "<exact name>", "file_type": "<one of: full_policy | policy_summary | claim_summary | hotel_booking | evidences>"}

    Note: Each attachment is preceded by a marker like [FILENAME:example.txt]. Use that exact filename in the output.
    """.strip()
    client = genai.Client(api_key=settings.app.AGENT_API_KEY)
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": system_prompt}, *parts]}],
        config=types.GenerateContentConfig(
            temperature=0.0,
            seed=42,
            response_mime_type="application/json",
        ),
    )
    if resp.text is None:
        logger.exception("Empty response from classify_travelguard_files")
        return []
    try:
        parsed = json.loads(resp.text)
        logger.info("Classified files: ☀️")
        logger.info(parsed)
        return [s.ClassifedDocument(**classified_doc) for classified_doc in parsed]
    except Exception:
        logger.exception("⚠️ Could not parse JSON. Raw response:\n")
        logger.exception(resp.text)
        return []


async def classified_covermore_docs(
    attachments: list[m.RequestAttachment],
) -> list[s.ClassifedDocument]:
    from agentric.lib.utils import read_minio_file

    pdf_texts = []
    for attachment in attachments:
        cotent_bytes = await read_minio_file(attachment.url)
        mime_type, _ = mimetypes.guess_type(attachment.file_name)
        if mime_type != "application/pdf":
            continue
        text = extract_first_two_pages(cotent_bytes)
        pdf_texts.append(f"{attachment.file_name}: {text}")

    system_prompt = f"""
    You are a STRICT file-type classifier for Zurich travel-insurance-related claim documents.
    Return results using the 'classify_files' tool. Output EXACTLY one label per file from:

    - full_policy
    - policy_summary
    - claim_summary
    - hotel_booking
    - evidences

    CLASSIFICATION PRIORITY (stop at first match):
    1) Full insurance policy document → full_policy
    2) Summary of policy → policy_summary
    3) Claim form or structured claim summary → claim_summary
    4) Hotel booking confirmation, itinerary, or receipt → hotel_booking
    5) Otherwise → evidences

    DEFINITIONS

    full_policy
    - Complete “Policy of Insurance” or certificate containing:
    • Legal wording and clauses (sections like: GENERAL EXCLUSIONS, BENEFITS, DEFINITIONS, PAYMENT OF CLAIMS)
    • Tables of contents or section numbering
    • Mentions of insurer (Zurich, GoReady, National Union Fire Insurance Company)
    • Coverage terms, claim procedures, or contract details
    • Usually multi-page, formal wording booklet format

    policy_summary
    - A concise confirmation/summary page for a purchased (or quoted) travel insurance plan.
    - Typically shows plan/product name, policy number or ID, coverage effective date,
    trip dates, total cost, trip cost, contact/policy holder info, and
    a section like "Coverages and Benefit Limits".

    claim_summary
    - Official claim or summary forms that include structured fields such as:
    • Claimant name, policy number, claim type (Trip Interruption, Cancellation, etc.)
    • Dates of travel, date of loss, description of event or illness
    • Expense breakdowns (“Breakdown of Claimant's Expense”, “Claim Amount”, “Total Expected Refunds”)
    • Illness/medical sections (“Who became ill?”, “Symptom onset date”, etc.)
    • Fraud statement, declaration, or signature area

    hotel_booking
    - Hotel reservation confirmations, booking receipts, or pricing summaries (from Expedia, Booking.com, etc.).
    - Characteristic cues:
    • “Check in” / “Check out” dates
    • “Nights • Adults • Rooms” summary lines
    • Property name or address
    • Room type and total price (e.g. “Total $296.27 Paid”)
    • Reservation / confirmation numbers
    - These documents show travel arrangements, not insurance or claim content.
    evidences
    - Any supporting documents that are NOT policy, claim form, or hotel booking, such as:
    • Receipts, invoices, doctor letters, refund messages, transport cancellations
    • Screenshots or email correspondence used as proof
    • Bank transaction statements or supporting proof of payment

    CHECKLIST (apply in order; stop at first YES):
    [ ] Does the file contain policy terms, benefits, exclusions, or insurer clauses? → full_policy
    [ ] Does the file contain a concise summary of a purchased travel insurance plan? → policy_summary
    [ ] Does the file have structured claim fields (policy number, claim reason, expense breakdown)? → claim_summary
    [ ] Does the file describe a hotel reservation or accommodation stay (check-in/out, nights, room info, total)? → hotel_booking
    [ ] Otherwise → evidences

    OUTPUT FORMAT
    Return ONLY a JSON object EXACTLY AS BELOW:
    {{"filename": "<exact name>", "file_type": "<one of: full_policy | policy_summary | claim_summary | hotel_booking | evidences>"}}

    Below are the PDF files and their first two pages of text:

    {chr(10).join(pdf_texts)}
    """

    client = genai.Client(api_key=settings.app.AGENT_API_KEY)
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[{"role": "user", "parts": [{"text": system_prompt}]}],
        config=types.GenerateContentConfig(
            temperature=0.0,
            seed=42,
            response_mime_type="application/json",
        ),
    )
    if resp is None or resp.text is None:
        msg = "⚠️ Could not generate response."
        raise Exception(msg)

    data = []
    try:
        results = json.loads(resp.text)
        data = [s.ClassifedDocument(**result) for result in results]

    except Exception:
        logger.exception("⚠️ Could not parse JSON. Raw response:\n")
        logger.info(resp.text)
    return data


async def check_missing_travelguard_documents(
    attachments: list[m.RequestAttachment], check_file_list: list[str]
) -> tuple[s.MissingCheckOutcome, str]:
    from agentric.lib.utils import read_minio_file

    system_prompt = """
    You are an insurance document checker.

    You will receive:
    - Multiple attached claim-related files (any format).
    - REQUIRED_FILES: a JSON array of document labels.

    Goal:
    For EACH label in REQUIRED_FILES, determine if at least one attached file clearly satisfies that label based on its content (not only the filename).

    Output (STRICT JSON, no prose, no extra keys):
    {
    "final_missing_status": true,
    "missing_status": {
        "<label_1>": {
        "missing": true,
        "reason": "<short explanation>"
        },
        "<label_2>": {
        "missing": false,
        "reason": "<short explanation>"
        }
    }
    // If and only if final_missing_status == true, also include BOTH fields below:
    // "generated_decision_summary": "<1-2 sentence summary explaining the missing documents and impact>",
    }

    Rules:
    - Include EVERY label from REQUIRED_FILES exactly once under "missing_status".
    - "missing" must be strictly boolean:
    - true  = missing (no attached file clearly satisfies the label)
    - false = not missing (at least one attached file clearly satisfies the label)
    - "reason" must be a single short sentence (e.g., "found Expedia booking with check-in/out dates", "no medical report showing diagnosis dates").
    - If you truly cannot determine from content, set missing = true and give a concise reason like "no evidence found".
    - Set "final_missing_status" to:
    - true  if ANY label in REQUIRED_FILES is missing (i.e., any missing_status[*].missing == true)
    - false if NONE are missing.
    - Conditional fields:
    - If final_missing_status == true:
        - Include "generated_decision_summary": 1-2 sentences summarizing what's missing and how it affects the claim.
    - If final_missing_status == false: DO NOT include "generated_decision_summary".
    - Do NOT add labels that are not present in REQUIRED_FILES.
    - Do NOT include any other fields, comments, or explanations.

    REQUIRED_FILES:
    <json>
    {req_files}
    </json>
    """.replace(
        "{req_files}", json.dumps(check_file_list, ensure_ascii=False, indent=2)
    )

    client = genai.Client(api_key=settings.app.AGENT_API_KEY)

    uploaded_files = []
    for attachment in attachments:

        mime_type, _ = mimetypes.guess_type(attachment.file_name)
        mime_type = mime_type or "application/octet-stream"
        content_bytes = await read_minio_file(attachment.url)
        uploaded = client.files.upload(
            file=io.BytesIO(content_bytes),
            config={"mime_type": mime_type},
        )
        uploaded_files.append(uploaded)

    if not uploaded_files:
        raise RuntimeError("No files uploaded")

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[*uploaded_files, system_prompt],
        config=types.GenerateContentConfig(
            temperature=0.0,
            seed=42,
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(include_thoughts=True),
        ),
    )
    if response is None or response.text is None:
        raise Exception("⚠️ Could not generate response.")

    try:
        thoughts = []
        assert response.candidates is not None

        for candidate in response.candidates:
            assert candidate.content is not None
            assert candidate.content.parts is not None

            for part in candidate.content.parts:
                if getattr(part, "thought", False):
                    thoughts.append(part.text.strip())

        outcome = json.loads(response.text)

        thoughts = thoughts[0] if len(thoughts) > 0 else "No thoughts."

        return s.MissingCheckOutcome(**outcome), thoughts

    except Exception:
        logger.exception(
            "⚠️ Could not parse JSON from missing docs check in tg. Raw response:\n"
        )
        raise ValueError(response.text)


async def check_missing_covermore_documents(
    attachments: list[m.RequestAttachment],
) -> dict[str, Any]:
    from agentric.lib.utils import read_minio_file

    req_files = json.dumps(cover_more_document_check)
    system_prompt = """
    You are an insurance claim triage assistant.

    You will receive:
    - Multiple attached claim-related files (any format).
    - REQUIRED_DOCS: JSON mapping categories to a list of required document names (strings).

    Your task:
    1) Read the attached files (content-based, not just filenames).
    2) For EACH category in REQUIRED_DOCS, and for EACH document item (string) in that category's list,
    decide whether the document is present or missing across the provided files:
    - missing = true  → no attached file clearly satisfies that document item
    - missing = false → at least one attached file clearly satisfies that document item
    3) Provide a short one-sentence "reason" for each item explaining your decision
    (e.g., "found itinerary with flight and hotel details" or "no medical report or diagnosis document detected").

    STRICT OUTPUT (MUST be valid JSON; no prose, no markdown, no extra keys):
    {
    "result": {
        "missing_by_category": {
        "<Category 1>": {
            "<Document Item A>": { "missing": true,  "reason": "<short explanation>" },
            "<Document Item B>": { "missing": false, "reason": "<short explanation>" }
        },
        "<Category 2>": {
            "<Document Item C>": { "missing": true,  "reason": "<short explanation>" }
        }
        // Include EVERY document item from REQUIRED_DOCS for EVERY category — no more, no less.
        }
    }
    }

    Rules:
    - You MUST include all categories and all document items exactly as listed in REQUIRED_DOCS.
    - "missing" must be a boolean; "reason" must be a short sentence.
    - Do NOT invent categories or document items.
    - Output ONLY the JSON object above (no additional fields).

    REQUIRED_DOCS:
    <json>
    {{req_files}}
    </json>
    """.replace(
        "{req_files}", req_files
    )

    client = genai.Client(api_key=settings.app.AGENT_API_KEY)

    uploaded_files = []
    for attachment in attachments:

        mime_type, _ = mimetypes.guess_type(attachment.file_name)
        mime_type = mime_type or "application/octet-stream"
        content_bytes = await read_minio_file(attachment.url)
        uploaded = client.files.upload(
            file=io.BytesIO(content_bytes),
            config={"mime_type": mime_type},
        )
        uploaded_files.append(uploaded)

    if not uploaded_files:
        raise RuntimeError("No files uploaded")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": system_prompt}]}],
        config=types.GenerateContentConfig(
            temperature=0.0,
            seed=42,
            response_mime_type="application/json",
        ),
    )
    if response is None or response.text is None:
        raise Exception("⚠️ Could not generate response.")

    try:
        return json.loads(response.text)

    except Exception:
        logger.error("⚠️ Could not parse JSON. Raw response:\n")
        raise ValueError(response.text)


def extract_missing_documents(data: dict[str, Any]) -> list[dict[str, s.MissingStatus]]:
    """Extract all missing documents from nested claim data."""
    results: list[dict[str, s.MissingStatus]] = []

    missing_by_category = data.get("result", {}).get("missing_by_category", {})

    for category_name, documents in missing_by_category.items():
        for doc_name, doc_info in documents.items():
            if doc_info.get("missing") is not None:
                results.append(
                    {
                        doc_name: s.MissingStatus(
                            missing=doc_info["missing"], reason=doc_info["reason"]
                        )
                    }
                )
    return results


async def mapped_missing_case_covermore(
    attachments: list[m.RequestAttachment], required_files: dict
) -> list[dict[str, s.MissingStatus]]:
    from agentric.lib.utils import read_minio_file

    system_prompt = """
    You are an Insurance Evidence Auditor.

    INPUTS YOU WILL RECEIVE
    1) <files>: a set of attached user files (PDFs, images, emails/EML, markdown, spreadsheets, etc.).
    2) <incoming_requirements>: a JSON object that already contains categories and evidence items with provisional
    {missing:boolean, reason:string} values. Treat this as the REQUIREMENTS SET to be verified and pruned.

    YOUR GOALS
    - Determine which requirement items actually apply to THIS case based on the files.
    - Keep only applicable categories/items; remove all non-applicable items. If a category becomes empty, remove the category.
    - For every kept item, verify presence in the files and set:
    - "missing": true | false
    - "reason": 1–2 factual sentences that reference the specific supporting file(s) (filename, page, brief quote/date) or explain what is absent.
    - Do not rely on the provisional values in <incoming_requirements>; re-evaluate from the files.

    APPLICABILITY RULES
    - Keep an item only if it logically pertains to THIS case (e.g., dental-only items are not applicable for a fractured arm; cruise-only items are not applicable to a flight/hotel trip; domestic-flight items not applicable to international trips, etc.).
    - Prefer explicit evidence in files (claim form, medical notes, receipts, cancellation emails, itineraries, policies, etc.).
    - If the files clearly show the case context (e.g., health-related additional expenses), keep only those items relevant to that context.
    - If unsure about applicability, keep the item and mark "missing" based on evidence check.

    EVIDENCE MATCHING RULES
    - Accept reasonable naming/format variants (e.g., "itinerary", "booking confirmation", "travel summary").
    - A partial but sufficient document counts as present (e.g., confirmation email without letterhead).
    - Only cite files that truly exist. Quote short phrases only when necessary.
    - For page references, state the exact page number (1-based) only if you verified it.

    SPECIAL RULE: CONDITIONAL ITEMS (CASE-WIDE)
    - For items whose text includes a condition (e.g., "(if required documents are missing)", "(if due to health)", "(for domestic flights)", "(for cruises)"):
    1) Evaluate the condition ACROSS THE ENTIRE CASE (all categories), unless the item explicitly limits scope.
    2) For “Letter of explanation (if required documents are missing)”:
        - If NO other evidence item ANYWHERE in the case is missing → set missing=false and reason="All required documents were provided; a letter of explanation is not required."
        - If ANY other evidence item anywhere in the case is missing and no letter is found → set missing=true with a clear absence reason.
        - If ANY other item is missing and a letter is found → set missing=false and cite the file that contains the letter.

    STRICT OUTPUT RULES
    - Output ONLY valid JSON. No extra text, no comments, no trailing commas.
    - Preserve the same high-level shape as the input (result → missing_by_category → {Category} → {Item}).
    - Include only the KEPT categories/items (pruned result).
    - Do not invent filenames or facts.

    VALIDATION (MUST DO BEFORE OUTPUT)
    - Compute missing_count_casewide = total number of items with missing=true ACROSS ALL CATEGORIES, excluding any item whose name contains "Letter of explanation (if required documents are missing)".
    - If missing_count_casewide == 0:
    - For every “Letter of explanation (if required documents are missing)” item: set missing=false and reason="All required documents were provided; a letter of explanation is not required."
    - If missing_count_casewide > 0:
    - For every such “Letter of explanation” item with no found letter evidence: set missing=true with a concise absence reason.

    OUTPUT SHAPE
    {
    "result": {
        "missing_by_category": {
        "<Kept Category>": {
            "<Kept Item>": {
            "missing": true|false,
            "reason": "<concise factual justification with file references, or why absent/not required>"
            }
        }
        }
    }
    }

    BEGIN.

    <incoming_requirements>
    {{INCOMING_REQUIREMENTS_JSON}}
    </incoming_requirements>

    <files>
    Read and analyze ALL provided files. Use their contents to determine applicability, presence/absence, and case-wide conditional requirements.
    </files>
    """.replace(
        "{{INCOMING_REQUIREMENTS_JSON}}", json.dumps(required_files, ensure_ascii=False)
    )

    client = genai.Client(api_key=settings.app.AGENT_API_KEY)

    uploaded_files = []
    for attachment in attachments:

        mime_type, _ = mimetypes.guess_type(attachment.file_name)
        mime_type = mime_type or "application/octet-stream"
        content_bytes = await read_minio_file(attachment.url)
        uploaded = client.files.upload(
            file=io.BytesIO(content_bytes),
            config={"mime_type": mime_type},
        )
        uploaded_files.append(uploaded)

    if not uploaded_files:
        raise RuntimeError("No files uploaded")
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=uploaded_files + [system_prompt],
        config=types.GenerateContentConfig(
            temperature=0.0,
            seed=42,
            response_mime_type="application/json",
        ),
    )

    raw = response.text
    if not raw:
        raise RuntimeError("Failed to mapped missing case for Covermore claims")
    result = json.loads(raw)
    return extract_missing_documents(result)


def convert_docx_bytes_to_pdf_bytes(byte_content: bytes) -> bytes:

    with io.BytesIO(byte_content) as byte_stream:
        html_result = mammoth.convert_to_html(byte_stream)
        html_content = html_result.value.strip()

    # Wrap in full HTML structure (for WeasyPrint)
    full_html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{
            font-family: "DejaVu Sans", sans-serif;
            margin: 40px;
            line-height: 1.5;
          }}
          h1, h2, h3 {{
            color: #333;
          }}
        </style>
      </head>
      <body>
        {html_content}
      </body>
    </html>
    """

    # pdf_buffer = io.BytesIO()
    # HTML(string=full_html).write_pdf(target=pdf_buffer)
    # pdf_buffer.seek(0)

    # return pdf_buffer.read()

    return html_content


async def evaluate_claim_status(
    extracted_data: dict[str, Any],
    evidences: list[m.RequestAttachment],
    full_policy: m.RequestAttachment,
    user_id: str,
    email: str,
    session_id: str,
    model_name: str = "gemini-2.5-flash",
) -> tuple[dict[str, Any], str]:
    from agentric.lib.utils import read_minio_file

    with tracer.start_as_current_span("claim_extraction") as span:

        span.set_attribute("function.name", "handle_claims")
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.email", email)
        span.set_attribute("session.id", session_id)

        client = genai.Client(api_key=settings.app.AGENT_API_KEY)
        schema_text = Path("schema/claim_decision.json").read_text(encoding="utf-8")
        policy_data = extracted_data["policy_data"]
        claim_data = extracted_data["claim_data"]
        hotel_data = extracted_data["hotel_data"]

        prompt = (
            """
        You will receive MULTIPLE uploaded files (policy + evidences), ONE JSON Schema, and THREE JSON objects:
        1) policy_data — summarized extracted policy info.
        2) claim_data — structured claim details.
        3) hotel_data — extracted lodging and trip delay information.

        <policy_data>
        {{POLICY_DATA}}
        </policy_data>

        <claim_data>
        {{CLAIM_DATA}}
        </claim_data>

        <hotel_data>
        {{HOTEL_DATA}}
        </hotel_data>

        ROLE
        You are a Travel Guard Claim Decision AI. Among the attached files, IDENTIFY the ONE file that is the full Travel Guard policy wording (authoritative source). Other attached files are evidences (e.g., medical reports, receipts, invoices, correspondence). Use the JSONs for facts and return ONE JSON that validates against the schema.

        POLICY FILE VALIDATION (MANDATORY)
        - Among the attached files, IDENTIFY the ONE that is the full Travel Guard policy wording (authoritative source).
        - Validate it using BOTH:
        (A) the file's text, and
        (B) fields in <policy_data> (e.g., policy_info.issuer_name, product_name, policy_number, coverages_and_benefit_limits).
        - Strong indicators that it IS a Travel Guard policy (need at least ONE indicator):
        • Mentions of "Travel Guard", "Hotel Booking Protection Plan", or similar coverage headings/sections
        • Presence of policy sections typical of policy wordings: Schedule of Benefits, Definitions, Exclusions, Claims, General Provisions
        - Negative indicators that it is NOT a valid Travel Guard policy (any → treat as invalid):
        • Mentions of unrelated insurers/brands (e.g., AIG, Allianz, AXA, Chubb, Generali, FWD, World Nomads)
        • File is a claim form, itinerary, email, invoice, receipt, or medical report (not policy wording)
        • Lacks policy-type sections (definitions, benefits, exclusions, claims process)

        DECISION GATE (FILE VALIDATION):
        - If NO attached file is a valid Travel Guard policy document:
            • appetite = "decline"
            • decision_reason = "Declined: no valid Travel Guard policy document among attachments"
            • confidence_level = 0.90
            • fraud_and_amount_check.is_fraud_suspected = false
            • Set all policy-derived numeric fields you cannot validate to null
            • payment_check.payment_status = "not_resolved"
            • Return a valid JSON per schema and STOP further computations.

        POLICY-GROUNDED DECISION RULES (MANDATORY)
        - Source of truth: The selected policy file is authoritative over <policy_data>, <claim_data>, and <hotel_data>.
        - Coverage applicability: Only treat a benefit as covered if you can explicitly confirm it from the policy file text.
        If you cannot find the relevant coverage or it is excluded, set appetite = "decline" with a concise policy-based reason.
        - Limits & conditions: All limits (per-day, per-person, per-trip caps, waiting times/minimum delay hours, exclusions)
        MUST be read from the policy file. If a needed number/condition is not present in the uploaded policy file, leave it null and do not approve beyond what can be verified.
        - Conflicts: When JSON facts conflict with the policy text, the policy text wins. Explain the conflict briefly in summary_of_findings.

        EVIDENCE CHECK (MANDATORY BEFORE DECLINE FOR MISSING EVIDENCE)
        - Non-policy attachments may include medical reports, test results, invoices, receipts, or correspondence.
        - BEFORE declining for missing evidence, you MUST check all attached evidence files for the required item(s).
        - If the required evidence is still missing, explicitly list which filenames were checked and why they were insufficient or irrelevant.

        EXTRACTION PRINCIPLES
        - Follow the schema strictly (keys, types).
        - Extract only what is present; set unknowns to null.
        - No extra keys, no fabrication.

        GOALS
        1) Detect claim_type and relevant coverage.
        Additionally, map claim_type to policy_data.coverages_and_benefit_limits.standard_packages.
        Populate:
        - refunds_check.matched_coverage_label (the matched key name, e.g., "trip_cancellation")
        - refunds_check.matched_coverage_terms (the raw text value, e.g., "100% Per Booking").
        (Confirm both directly from the policy file whenever possible; if not visible in the file, leave unknown/null.)
        2) Derive policy limits from the policy text (per_day_limit, overall_cap_per_person, overall_cap_per_trip, minimum_delay_hours).
        3) Compute payout eligibility, fraud risk, and payment status — ONLY within limits verified in the policy file.
        4) Decide appetite (approve/decline) with decision_reason and confidence_level — grounded in policy wording.

        *** MEDICAL / FRAUD CHECK ***
        If claim_reason mentions illness/Covid/infection/sick:
        - Require medical proof (test result, doctor letter) among the attached evidence files.
        - If none found:
            fraud_and_amount_check.is_fraud_suspected = true
            fraud_and_amount_check.fraud_reasons = ["missing medical proof for illness"]
            fraud_and_amount_check.approved_amount = 0
            payment_check.payment_status = "not_resolved"
            appetite = "decline"
            decision_reason = "Missing medical evidence in attachments for illness-based claim"
            confidence_level <= 0.70

        BENEFIT LIMITS (Policy-driven) — EXPECTED REFUND FIRST
        - Normalize numeric inputs (strip symbols/commas).
        - Let:
            insured_trip_cost   = numeric(policy_data.trip_detail.trip_cost) or null
            expected_refund     = numeric(claim_data.claimants_expense.total_expected_refunds) or null
            premium_amount      = numeric(policy_data.policy_info.policy_total_cost) or null
        - Extract from the policy file (if present/confirmable):
            per_day_limit, overall_cap_per_person, overall_cap_per_trip, minimum_delay_hours

        - Determine policy_claimable_max with this precedence (respecting only values verified in the policy file or the provided JSONs when policy allows):
        1) If expected_refund is present → base_cap = expected_refund
        2) Else if overall_cap_per_trip is present → base_cap = overall_cap_per_trip
        3) Else if insured_trip_cost is present AND the policy states trip_cancellation covers “100% of Insured Trip Cost” → base_cap = insured_trip_cost
        4) Else → base_cap = null

        - If per-day logic is relevant (e.g., Trip Delay):
            compute gross_daily = per_day_limit x eligible_days x eligible_persons
            base_cap = min_non_null(base_cap, gross_daily, overall_cap_per_person x eligible_persons, overall_cap_per_trip)

        - Set:
            fraud_and_amount_check.policy_claimable_max = base_cap
            fraud_and_amount_check.approved_amount = min(claim_total, base_cap) when both not null and no fraud
            fraud_and_amount_check.within_limit = (claim_total <= base_cap) when both not null
            fraud_and_amount_check.delta = claim_total - base_cap when both not null
            fraud_and_amount_check.capped_payout = base_cap when claim_total > base_cap

        COVERAGE MATCH STRINGS (for refunds_check.*)
        - matched_coverage_label = the selected key in standard_packages (e.g., "trip_cancellation", "trip_delay").
        - matched_coverage_terms = the raw value string from that key (e.g., "100% Per Booking", "$150 Per Insured").
        Example mapping:
        * trip_cancellation → "100% Per Booking" or "100% of Insured Trip Cost"
        * trip_delay → "$150 Per Insured"
        * baggage_delay → "$150 Per Insured"

        REFUNDS VIEW (populate refunds_check)
        - refunds_check.expected_refund = expected_refund (from claim_data)
        - refunds_check.protection_plan_cost = premium_amount (from policy_data/policy file)
        - refunds_check.refund_net_of_premium = expected_refund - premium_amount (null if either is null)
        - refunds_check.matched_coverage_label = detected coverage key (policy-confirmed where possible).
        - refunds_check.matched_coverage_terms = raw coverage description string (policy-confirmed where possible).

        PAYMENT STATUS
        - If fraud or missing medical proof → not_resolved.
        - Else if approved_amount == claim_total (>0) → full_payment
        - Else if 0 <= approved_amount < claim_total → partial_payment
        - Else → not_known / not_resolved (pick most accurate).

        APPETITE
        - "approve" when covered by the policy file, valid, and supported by attached evidence.
        - "decline" when required evidence is missing (after checking attachments), fraudulent, excluded, or out-of-scope per the policy file.
        - decision_reason = one concise sentence grounded in the policy wording or explicit lack of evidence in attachments.

        CONFIDENCE
        - 0.9-1.0 when policy terms + numbers + evidence are explicit in the policy file.
        - ≤0.7 when key evidence/terms are missing or inferred.

        OUTPUT (in below schema)
        <schema>
        {{JSON_SCHEMA}}
        </schema>

        Rules:
        - Return exactly ONE JSON that validates against the schema.
        - Include decision_reason, confidence_level, summary_of_findings, and case_description.
        - Use null/[] when not found. No markdown.
        """.replace(
                "{{JSON_SCHEMA}}", schema_text
            )
            .replace("{{POLICY_DATA}}", json.dumps(policy_data))
            .replace("{{CLAIM_DATA}}", json.dumps(claim_data))
            .replace("{{HOTEL_DATA}}", json.dumps(hotel_data))
        )

        uploaded_files = []
        logger.info("Uploading Evidence files...")
        for evidence in evidences:
            logger.info(evidence.file_name)
            mime_type, _ = mimetypes.guess_type(evidence.file_name)

            content_bytes = await read_minio_file(evidence.url)
            uploaded = client.files.upload(
                file=io.BytesIO(content_bytes),
                config={"mime_type": mime_type},
            )
            uploaded_files.append(uploaded)

        full_policy_content_bytes = await read_minio_file(full_policy.url)

        mimetype, _ = mimetypes.guess_type(full_policy.file_name)
        full_policy_file = client.files.upload(
            file=io.BytesIO(full_policy_content_bytes),
            config={"mime_type": mimetype},
        )
        uploaded_files.append(full_policy_file)
        parsed = {}
        thought = ""
        try:

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    *uploaded_files,
                    prompt,
                ],  # Attachment full policy file + evidence
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    seed=42,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(include_thoughts=True),
                ),
            )
            um = response.usage_metadata
            input_tokens = um.prompt_token_count or 0  # type: ignore
            output_tokens = um.candidates_token_count or 0  # type: ignore
            total_tokens = um.total_token_count or 0  # type: ignore

            span.set_attribute("genai.request_token_usage", input_tokens)
            span.set_attribute("genai.response_token_usage", output_tokens)
            span.set_attribute("genai.total_token_usage", total_tokens)
            span.set_attribute("genai.model", model_name)
            result = response.text or "{}"
            parsed = json.loads(result)
            thoughts = []

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if getattr(part, "thought", False):  # Only collect reasoning parts
                        thoughts.append(part.text.strip())

            thought = thoughts[0] if len(thoughts) > 0 else ""

        except JSONDecodeError as e:
            logger.info(f"⚠️ JSON decode failed: {e}")
        except Exception as e:
            logger.info(f"⚠️ Batch failed: {e}")

        return parsed, thought
