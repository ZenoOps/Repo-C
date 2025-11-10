from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from dateutil import parser
from structlog import get_logger

from agentric.config.app import alchemy
from agentric.db.models.enums import ClaimStatus, SubmissionStatus
from agentric.domain.chats.deps import provide_chats_service
from agentric.domain.requests.deps import (
    provide_extraction_service,
    provide_request_attachment_service,
    provide_request_service,
)
from agentric.domain.requests.utils import (
    check_missing_covermore_documents,
    check_missing_travelguard_documents,
    classified_covermore_docs,
    classified_travelguard_docs,
    evaluate_claim_status,
    extract_all_info,
    generate_data_structure,
    generate_data_structure_missing_case,
    handle_missing,
    mapped_missing_case_covermore,
)
from agentric.domain.requests.utils import (
    handle_claims as extract_claim_form,
)

from .rule_sets import travel_guard_required_files

if TYPE_CHECKING:
    from saq.types import Context

logger = get_logger()


# Travelguard document types
class TGDocumentType(StrEnum):
    FULL_POLICY = "full_policy"
    HOTEL_BOOKING = "hotel_booking"
    CLAIM_SUMMARY = "claim_summary"
    EVIDENCES = "evidences"
    SUMMARY_POLICY = "policy_summary"


async def process_travelguard_claims(
    ctx: "Context", *, request_id: str, session_id: str, user_email: str, user_id: str
) -> None:
    async with alchemy.get_session() as db_session:
        request_attachment_service = await anext(
            provide_request_attachment_service(db_session)
        )
        requests_service = await anext(provide_request_service(db_session))
        chat_service = await anext(provide_chats_service(db_session))
        chat_obj = await chat_service.get_one_or_none(request_id=request_id)
        if chat_obj is None:
            raise Exception(f"Chat not found assoicated with request {request_id}")
        request_attachments = await request_attachment_service.list(chat_id=chat_obj.id)

        try:
            updated_request = {}
            classified_docs = await classified_travelguard_docs(
                attachments=list(request_attachments)
            )

            # Collect all attachment files and map them to their respective document types
            input_classified_files = {
                TGDocumentType.FULL_POLICY: None,
                TGDocumentType.SUMMARY_POLICY: None,
                TGDocumentType.CLAIM_SUMMARY: None,
                TGDocumentType.HOTEL_BOOKING: [],
                TGDocumentType.EVIDENCES: [],
            }

            for doc in classified_docs:
                classifed_doc_filename = doc.filename.replace(" ", "").lower()
                selected_file = next(
                    (
                        file
                        for file in request_attachments
                        if file.file_name.replace(" ", "").lower()
                        == classifed_doc_filename
                    ),
                    None,
                )

                if selected_file is None:
                    alert_mesg = (
                        f"🚨 File {doc.filename} not found in request attachments"
                    )
                    logger.info(alert_mesg)
                    continue

                match doc.file_type:
                    case TGDocumentType.SUMMARY_POLICY:
                        input_classified_files[TGDocumentType.SUMMARY_POLICY] = (
                            selected_file
                        )
                    case TGDocumentType.FULL_POLICY:
                        input_classified_files[TGDocumentType.FULL_POLICY] = (
                            selected_file
                        )
                    case TGDocumentType.CLAIM_SUMMARY:
                        input_classified_files[TGDocumentType.CLAIM_SUMMARY] = (
                            selected_file
                        )
                    case TGDocumentType.HOTEL_BOOKING:
                        input_classified_files[TGDocumentType.HOTEL_BOOKING].append(
                            selected_file
                        )
                    case TGDocumentType.EVIDENCES:
                        input_classified_files[TGDocumentType.EVIDENCES].append(
                            selected_file
                        )

            # DATA Extraction based on the available files

            extracted_data = await extract_all_info(
                hotel_doc=input_classified_files[TGDocumentType.HOTEL_BOOKING],
                claim_summary_doc=input_classified_files[TGDocumentType.CLAIM_SUMMARY],
                policy_summary_doc=input_classified_files[TGDocumentType.SUMMARY_POLICY],
                session_id=session_id,
                email=user_email,
                user_id=user_id,
            )

            # Missing file check
            missing_file_list = []
            required_file_check_list = []

            if input_classified_files[TGDocumentType.FULL_POLICY] is None:
                policy_entry = {
                    "filename": "policy_detail",
                    "is_missing": True,
                    "verdict": "Policy detail document not found",
                }
                missing_file_list.append(policy_entry)
                required_file_check_list.append(policy_entry)

            if input_classified_files[TGDocumentType.CLAIM_SUMMARY] is None:
                summary_entry = {
                    "filename": "claim_summary",
                    "is_missing": True,
                    "verdict": "Claim summary document not found",
                }
                missing_file_list.append(summary_entry)
                required_file_check_list.append(summary_entry)

            if input_classified_files[TGDocumentType.SUMMARY_POLICY] is None:
                summary_entry = {
                    "filename": "policy_summary",
                    "is_missing": True,
                    "verdict": "Policy summary document not found",
                }
                missing_file_list.append(summary_entry)
                required_file_check_list.append(summary_entry)

            ### all attachment files except the policy detail file
            filtered_files = []
            if input_classified_files[TGDocumentType.FULL_POLICY] is None:
                filtered_files = list(request_attachments)
            else:
                filtered_files = [
                    file
                    for file in request_attachments
                    if file.file_name
                    != input_classified_files[TGDocumentType.FULL_POLICY].file_name
                ]
            check_file_list = []

            claim_type = extracted_data["claim_data"]["claim_reason"]["claim_type"]
            claim_status = extracted_data["claim_data"]["claim_reason"][
                "claim_reason_type"
            ]

            check_file_list = travel_guard_required_files[claim_type][claim_status]

            analysis_outcome, thoughts = await check_missing_travelguard_documents(
                attachments=filtered_files, check_file_list=check_file_list
            )

            for key, val in analysis_outcome.missing_status.items():
                item = {
                    "filename": key,
                    "is_missing": val.missing,
                    "verdict": val.reason,
                }
                if val.missing:
                    missing_file_list.append(item)
                required_file_check_list.append(item)
            decision_thoughts = ""
            if len(missing_file_list) == 0:
                decision_data, decision_thoughts = await evaluate_claim_status(
                    extracted_data=extracted_data,
                    user_id=user_id,
                    email=user_email,
                    session_id=session_id,
                    full_policy=input_classified_files[TGDocumentType.FULL_POLICY],
                    evidences=input_classified_files[TGDocumentType.EVIDENCES],
                )
                extracted_data["decision_data"] = decision_data

            updated_request = await _process_request_info(
                extracted_data=extracted_data,
                missing_documents=[
                    file["filename"].replace("_", " ") for file in missing_file_list
                ],
            )
            if decision_thoughts != "":
                updated_request["generated_thoughts"] = decision_thoughts

            updated_request["generated_file_check_summary"] = thoughts
            if len(missing_file_list) > 0:
                updated_request["generated_decision_summary"] = analysis_outcome.generated_decision_summary
            elif extracted_data["decision_data"] is not None:
                updated_request["generated_decision_summary"] = extracted_data["decision_data"]["summary_of_findings"]

            await requests_service.update(
                item_id=request_id, data=updated_request, auto_commit=True
            )
            extractions_service = await anext(provide_extraction_service(db_session))

            extracted_data["required_document_check"] = required_file_check_list

            await extractions_service.create(
                data={
                    "request_id": request_id,
                    "extracted_data": extracted_data,
                },
                auto_commit=True,
            )

        except Exception as e:
            logger.exception(
                "Extraction failed",
                request_id=request_id,
                error=str(e),
            )

            await requests_service.update(
                item_id=request_id,
                data={
                    "status": ClaimStatus.CLOSED,
                    "submission_status": SubmissionStatus.ERROR,
                },
                auto_commit=True,
                auto_refresh=True,
            )

async def process_covermore_claims(
    ctx: "Context", *, request_id: str, session_id: str, user_email: str, user_id: str
) -> None:
    async with alchemy.get_session() as db_session:
        request_attachment_service = await anext(
            provide_request_attachment_service(db_session)
        )
        requests_service = await anext(provide_request_service(db_session))
        chat_service = await anext(provide_chats_service(db_session))
        chat_obj = await chat_service.get_one_or_none(request_id=request_id)
        if chat_obj is None:
            raise Exception(f"Chat not found assoicated with request {request_id}")
        request_attachments = await request_attachment_service.list(chat_id=chat_obj.id)

        try:
            updated_request = {}
            extraction_data = {}
            request = await requests_service.get(item_id=request_id)

            classified_docs = await classified_covermore_docs(
                attachments=list(request_attachments)
            )
            filtered_files = []

            policy_detail_file = None
            for doc in classified_docs:
                if doc.file_type == "full_policy":
                    policy_filename = doc.filename.replace(" ", "").lower()
                    for file in request_attachments:
                        base_filename = file.file_name.replace(" ", "").lower()
                        if base_filename == policy_filename:
                            policy_detail_file = file
                            break
                    continue

                chosen_one = [
                    file
                    for file in request_attachments
                    if file.file_name.replace(" ", "").lower()
                    == doc.filename.replace(" ", "").lower()
                ]
                filtered_files.append(chosen_one[0])
            required_file_check_list = []
            missing_file_list = []
            if policy_detail_file is None:
                policy_entry = {
                    "filename": "policy_detail",
                    "is_missing": True,
                    "verdict": "Policy detail document not found",
                }
                missing_file_list.append(policy_entry)
                required_file_check_list.append(policy_entry)

                required_files = await check_missing_covermore_documents(
                    attachments=filtered_files
                )
                analysis_outcome = await mapped_missing_case_covermore(
                    attachments=filtered_files, required_files=required_files
                )
                for item in analysis_outcome:
                    for key, val in item.items():
                        entry = {
                            "filename": key,
                            "is_missing": val.missing,
                            "verdict": val.reason,
                        }
                        if val.missing:
                            missing_file_list.append(entry)
                        required_file_check_list.append(entry)

            if len(missing_file_list) > 0:
                extraction_data = await handle_missing(
                    attachments=filtered_files,
                    missing_list=missing_file_list,
                    user_id=user_id,
                    email=user_email,
                    session_id=session_id,
                )
                structed_extraction = await generate_data_structure_missing_case(
                    data=extraction_data,
                    user_id=user_id,
                    email=user_email,
                    session_id=session_id,
                    missing_file_list=missing_file_list,
                )

            else:
                extraction_data = await extract_claim_form(
                    attachments=filtered_files,
                    user_id=user_id,
                    email=user_email,
                    session_id=session_id,
                )

                structed_extraction = await generate_data_structure(
                    data=extraction_data,
                    policy_detail_file=policy_detail_file,
                    user_id=user_id,
                    email=user_email,
                    session_id=session_id,
                )
            if extraction_data and structed_extraction:
                updated_request = _process_extraction_data(
                    extraction_data=structed_extraction
                )
                updated_request.update(
                    {
                        "generated_decisions": extraction_data["decision"],
                        "generated_thoughts": extraction_data["thoughts"],
                    }
                )
                if len(missing_file_list) > 0:
                    updated_request["missing_documents"] = [
                        file["filename"] for file in missing_file_list
                    ]
                    updated_request["status"] = ClaimStatus.MISSING

                    if (
                        extraction_data["extracted"].get("decision", {}).get("status")
                        is not None
                    ):
                        extraction_data["extracted"]["decision"][
                            "status"
                        ] = ClaimStatus.MISSING.value

                extractions_service = await anext(
                    provide_extraction_service(db_session)
                )
                request = await requests_service.get(item_id=request_id)
                extraction_data["extracted"][
                    "required_document_check"
                ] = required_file_check_list

                await extractions_service.create(
                    data={
                        "request_id": request.id,
                        "extracted_data": extraction_data["extracted"],
                    }
                )

                await requests_service.update(
                    item_id=request_id,
                    data=updated_request,
                    auto_commit=True,
                )

            else:
                raise Exception("Unable to extract")

        except Exception as e:
            logger.error(
                "Extraction failed",
                request_id=request_id,
                error=str(e),
                exc_info=True,
            )

            await requests_service.update(
                item_id=request_id,
                data={
                    "status": ClaimStatus.CLOSED,
                    "submission_status": SubmissionStatus.ERROR,
                },
                auto_commit=True,
                auto_refresh=True,
            )


def parse_datetime(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        # fromisoformat is robust for ISO 8601 strings (e.g., "2023-05-15T00:00:00")
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        # Fallback for simple date format if needed
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None


async def _process_request_info(
    extracted_data: dict, missing_documents: list[str]
) -> dict:

    policy_data = extracted_data["policy_data"]
    claim_data = extracted_data["claim_data"]
    decision_data = extracted_data.get("decision_data", {})

    client_name = claim_data["claim_details"]["first_name"]
    last_name = claim_data["claim_details"]["last_name"]
    phone_number = claim_data["claim_details"]["phone_number"]
    mobile_number = claim_data["claim_details"]["mobile_number"]

    client_name = (
        f"{client_name} {last_name}".strip() if client_name or last_name else None
    )

    if phone_number is not None:
        phone_number = mobile_number

    request_data = {
        "missing_documents": missing_documents,
        # Claim Info
        "claim_number": claim_data["claim_details"]["claim_number"],
        "type_of_claim": claim_data["claim_reason"]["claim_type"],
        "requested_reimbursement_amount": str(
            claim_data["claimants_expense"]["total_expected_refunds"]
        ),
        "claim_amount": str(claim_data["claimants_expense"]["total_claimed_amount"]),
        # Contact Info
        "client_name": client_name,
        "business_number": claim_data["claim_details"]["business_number"],
        "client_phone_number": phone_number,
        "client_post_code": claim_data["claim_details"]["zip_postal_code"],
        # Decision Info
    }

    if decision_data:
        fraud_reasons = decision_data["fraud_and_amount_check"]["fraud_reasons"]
        premium_amount = decision_data["premium_amount_check"]["premium_amount"]
        if premium_amount and not isinstance(premium_amount, str):
            premium_amount = str(premium_amount)

        if isinstance(fraud_reasons, list):
            fraud_reasons = ". \n".join(str(reason) for reason in fraud_reasons if reason)
        elif fraud_reasons is None:
            fraud_reasons = ""
        else:
            fraud_reasons = str(fraud_reasons)
        decision_info = {
            "generated_decision": decision_data["decision_reason"],
            "decision_confidence_level": decision_data["confidence_level"],
            "is_fraud_suspected": decision_data["fraud_and_amount_check"][
                "is_fraud_suspected"
            ],
            "payment_reason": decision_data["payment_check"]["payment_reason"],
            "fraud_reasons": fraud_reasons,
            "summary_of_findings": decision_data["summary_of_findings"],
            "case_description": decision_data["case_description"],
            "approved_amount": f"{decision_data['fraud_and_amount_check']['approved_amount']}",
            "premium_amount": premium_amount,
        }

        # Fraud detection
        matched_coverage_label = decision_data["refunds_check"].get(
            "matched_coverage_label"
        )
        matched_coverage_terms = decision_data["refunds_check"].get(
            "matched_coverage_terms"
        )

        if matched_coverage_label and matched_coverage_terms:
            matched_coverage_label = matched_coverage_label.capitalize().replace(
                "_", " "
            )
            request_data["matched_coverage_terms"] = (
                f"{matched_coverage_label}: {matched_coverage_terms}"
            )
        request_data = {**request_data, **decision_info}

    if policy_data:
        policy_info = {
            # Policy Info
            "policy_number": policy_data["policy_info"]["policy_number"],
            "policy_holder_name": policy_data["contact_info"]["policy_holder_name"],
            "policy_total_cost": policy_data["policy_info"]["policy_total_cost"],
            # trip info
            "trip_cost": policy_data["trip_details"]["trip_cost"],
            "destination": policy_data["trip_details"]["trip_destination"],
            "client_email_address": policy_data["contact_info"]["email"],
        }
        request_data = {**request_data, **policy_info}

        departure_date_str = policy_data["trip_details"]["departure_date"]
        return_date_str = policy_data["trip_details"]["return_date"]
        policy_effective_date_str = policy_data["policy_info"][
            "coverage_effective_date"
        ]
        policy_expiration_date_str = policy_data["policy_info"][
            "coverage_expiration_date"
        ]
        if departure_date_str:
            departure_date = parser.parse(departure_date_str).replace(tzinfo=None)
            request_data["trip_start_date"] = departure_date

        if return_date_str:
            return_date = parser.parse(return_date_str).replace(tzinfo=None)
            request_data["trip_return_date"] = return_date

        if policy_effective_date_str:
            policy_effective_date = parser.parse(policy_effective_date_str).replace(
                tzinfo=None
            )
            request_data["policy_effective_date"] = policy_effective_date

        if policy_expiration_date_str:
            policy_expiration_date = parser.parse(policy_expiration_date_str).replace(
                tzinfo=None
            )
            request_data["policy_expiration_date"] = policy_expiration_date

    is_duplicated = False

    # REQUEST APPETITE STATUS
    if is_duplicated:
        request_data["submission_status"] = SubmissionStatus.DUPLICATE
    else:
        request_data["submission_status"] = SubmissionStatus.INREVIEW

    if len(missing_documents) > 0:
        request_data["missing_documents"] = missing_documents
        request_data["status"] = ClaimStatus.MISSING
    elif decision_data is not None:
        appetite_status = decision_data["appetite"]
        if appetite_status == "approve":
            payment_status = decision_data["payment_check"]["payment_status"]
            if payment_status == "partial_payment":
                request_data["status"] = ClaimStatus.PARTIAL_PAYMENT
            elif payment_status == "full_payment":
                request_data["status"] = ClaimStatus.APPROVED
            else:
                request_data["status"] = ClaimStatus.APPROVED
        else:
            request_data["status"] = ClaimStatus.DECLINED
    return request_data


def _process_extraction_data(extraction_data: dict) -> dict:
    """Processes the extracted JSON data and maps it to the format
    required for the Request database model.
    """
    if not extraction_data:
        return {}

    policy_info = extraction_data.get("policy_info", {})
    trip_info = extraction_data.get("trip_info", {})
    claim_info = extraction_data.get("claim_info", {})
    client_info = extraction_data.get("client_info", {})

    return {
        # Top-level and Analytical Fields
        "status": (
            ClaimStatus(extraction_data.get("status"))
            if extraction_data.get("status")
            else ClaimStatus.DECIDING
        ),
        "submission_status": SubmissionStatus.INREVIEW,
        "missing_documents": extraction_data.get("missing_documents", []),
        "generated_decision_summary": extraction_data.get("generated_decision_summary"),
        "is_medical_claim": extraction_data.get("is_medical_claim", False),
        "decision_reason": extraction_data.get("decision_reason"),
        "payment_status": extraction_data.get("payment_status"),
        "payment_reason": extraction_data.get("payment_reason"),
        # Claim Info
        "claim_number": claim_info.get("claim_number"),
        "claim_amount": claim_info.get("total_claimed_amount"),
        "approved_amount": claim_info.get("approved_amount"),
        "type_of_claim": claim_info.get("type_of_claim"),
        "requested_reimbursement_amount": claim_info.get(
            "requested_reimbursement_amount"
        ),
        "insurance_agency_name": claim_info.get("insurance_agency_name"),
        "premium_amount": claim_info.get("premium_amount"),
        # Trip info
        "trip_cost": trip_info.get("trip_cost"),
        "trip_start_date": parse_datetime(trip_info.get("trip_start_date")),
        "trip_return_date": parse_datetime(trip_info.get("trip_return_date")),
        "destination": trip_info.get("destination"),
        # Client Info
        "client_name": client_info.get("client_name"),
        "client_email_address": client_info.get("client_email_address"),
        "client_phone_number": client_info.get("client_phone_number"),
        "client_post_code": client_info.get("client_post_code"),
        "description": client_info.get("description"),
        # Policy Info
        "policy_holder": policy_info.get("policy_holder"),
        "policy_number": policy_info.get("policy_number"),
        "policy_effective_date": parse_datetime(
            policy_info.get("policy_effective_date")
        ),
        "policy_expiration_date": parse_datetime(
            policy_info.get("policy_expiration_date")
        ),
        "maximum_coverage_amount": policy_info.get("maximum_coverage_amount"),
        "coverage_limits": policy_info.get("coverage_limits"),
    }
