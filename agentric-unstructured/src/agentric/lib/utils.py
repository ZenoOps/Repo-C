from __future__ import annotations

import hashlib
import json
import mimetypes
import uuid
from datetime import datetime
from typing import cast

import aioboto3
from anthropic import AsyncAnthropic
from botocore.config import Config
from litestar import Litestar
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import getLogger

from agentric.config import constants, get_settings
from agentric.config.app import alchemy as alchemy_config
from agentric.db import models as m
from agentric.domain.customers.services import CustomerService
from agentric.domain.requests.services import RequestService
from agentric.lib import crypt

from .naming_convention import document_mapping

__all__ = [
    "classify_document_type",
    "get_email_send_date",
    "get_file_path",
    "handle_customer_relationship_request",
]
setting = get_settings()

MINIO_ENDPOINT_URL = setting.minio.ENDPOINT_URL
MINIO_PUBLIC_ENDPOINT_URL = setting.minio.PUBLIC_ENDPOINT_URL
MINIO_ROOT_USER = setting.minio.ROOT_USER
MINIO_ROOT_PASSWORD = setting.minio.ROOT_PASSWORD
BUCKET = setting.minio.BUCKET
COOKIE = setting.app.CSRF_COOKIE_NAME

logger = getLogger()


async def validate_claim(request: m.Request) -> tuple[bool, str]: ...


async def handle_customer_relationship_request(
    db_session: AsyncSession, new_request: m.Request, customer_service: CustomerService
) -> m.Customer | None:
    customer_name = new_request.client_name
    if customer_name is None:
        raise ValueError("Customer name is required")

    unique = customer_name.lower().strip().replace(" ", "")
    unique_customer_check = hashlib.sha256(unique.encode("utf-8")).hexdigest()
    existing_customer = await customer_service.get_one_or_none(hashed_name=unique_customer_check)

    if existing_customer:
        return existing_customer

    new_customer = await customer_service.create(data={"name": new_request.client_name})
    await db_session.commit()
    return new_customer


async def classify_document_type(content: str, client: AsyncAnthropic, model:str="claude-3-5-sonnet-20241022") -> str:
    document_types = [
        "broker_correspondence",
        "internal_correspondence",
        "letter_of_appointment",
        "letter_of_authority",
        "file_notes",
        "renewal_new_business_strategy",
        "renewal_slip",
        "new_business_slip",
        "endorsement_slip",
        "endorsement_information",
        "asset_schedule",
        "business_income_worksheet",
        "business_income_information",
        "limit_of_liability_calculation",
        "claims_history",
        "company_information",
        "flood_maps_and_reports",
        "ides_worksheet",
        "actuarial_pricing",
        "aggregate_deductible",
        "rating_model",
        "renewal_quotation",
        "new_business_quotation",
        "endorsement_quotation",
        "policy_wording",
        "renewal_schedule",
        "new_business_schedule",
        "endorsement_schedule",
        "certificate_of_currency",
        "placing_slip",
        "closing",
        "tur_peer_review",
        "stamp_duty_exceptions",
        "riqa_correspondence",
        "claims_report_mid_term",
        "third_party_survey",
        "broker_survey",
        "reinsurance_correspondence",
        "reinsurance_certificate",
    ]

    prompt = f"""
You are an insurance document classification assistant.

Your task is to identify the document type based on the content. Below is a list of valid document types :

{", ".join(document_types)}

**Instructions:**
- Do NOT include explanations, comments, or notes.
- Carefully read the document below.
- Choose the single best matching document type from the list.
- Only return one type.
- Respond ONLY in this JSON format:
```json
{{ "document_type": "your_selected_type_here" }}
```
<Document> {content} </Document> """.strip()
    logger.info("Identifying document type")
    response = await client.messages.create(
        model=model,
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_output = response.content[0].text.strip()
    try:
        response = json.loads(raw_output)
        return response["document_type"]

    except Exception as e:
        print("Claude returned unexpected output:\n", raw_output)
        raise e


async def get_email_send_date(content: str, client: AsyncAnthropic, model:str="claude-3-5-sonnet-20241022") -> str:
    prompt = f"""
You are an insurance document classification assistant.

Your task is to identify the sent date based on the content.  
**Instructions:**
- Do NOT include explanations, comments, or notes.
- Carefully read the document below.
- Return the email sent date in the format YYYYMMDD.
  for example: 20250606
- Only return one date.
- Respond ONLY in this JSON format:
```json
{{ "email_send_date": "your_selected_date_here" }}
```
<Document> {content} </Document> """.strip()

    response = await client.messages.create(
        model=model,
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_output = response.content[0].text.strip()
    try:
        response = json.loads(raw_output)
        return response["email_send_date"]

    except Exception as e:
        print("Claude returned unexpected output:\n", raw_output)
        raise e


async def get_file_path(
    document_type: str,
    send_date: str,
    customer_name: str,
    line_of_business: str,
    request_service: RequestService,
) -> dict:
    document_type_info = document_mapping.get(document_type)
    if document_type_info is None:
        raise ValueError("Invalid document type")

    current_year = datetime.now().year
    absolute_folder_path = f"{customer_name}/{current_year}/{line_of_business}/{document_type_info['sub_folder']}"

    document_name = f"{document_type_info['doc_naming_convention']} {customer_name} {send_date}"

    absolute_file_path = f"{absolute_folder_path}/{document_name}"

    same_file_path_count = await request_service.count(document_file_path=absolute_file_path)

    version_number = same_file_path_count + 1

    return {
        "document_file_path": absolute_file_path,
        "file_version_number": version_number,
    }


async def seed_db(app: Litestar) -> None:
    from agentric.config import get_settings

    settings = get_settings()

    admin_paswds = settings.app.ADMIN_PASSWORDS

    admin_accs = settings.app.ADMIN_ACCOUNTS
    admin_paswds = settings.app.ADMIN_PASSWORDS
    user_accs=settings.app.USER_ACCOUNTS
    user_paswds = settings.app.USER_PASWDS

    travel_guard_team_id=uuid.uuid4()
    cover_more_team_id=uuid.uuid4()

    async def hash_password(password: str) -> str:
        return await crypt.get_password_hash(password)

    async with alchemy_config.get_session() as db_session:
        team_exists = await db_session.scalar(select(exists().select_from(m.Team)))

        if team_exists:
            return

        domains: dict ={
            "travelguard":[],
            "covermore":[],
            "customer":[],
            "admin":[]
        }

        for idx, user_account in enumerate(user_accs):

            name_part, email_part=user_account.split("@")
            name=" ".join([word.capitalize() for word in name_part.split(".")])

            email=user_account

            user=m.User(
                    id=uuid.uuid4(),
                    name=name,
                    email=email,
                    hashed_password=await hash_password(user_paswds[idx]),
                    is_active=True,
                    is_superuser=False,
                    is_verified=True,
                )

            if email_part=="travelguard.com":
                domains["travelguard"].append(user)
            elif email_part in ("covermore.com", "zurich.com"):
                domains["covermore"].append(user)
            else:
                domains["customer"].append(user)


        for idx, admin_account in enumerate(admin_accs):

            name_part=admin_account.split("@")[0]
            name=" ".join([word.capitalize() for word in name_part.split(".")])

            email=admin_account


            user=m.User(
                    id=uuid.uuid4(),
                    name=name,
                    email=email,
                    hashed_password=await hash_password(admin_paswds[idx]),
                    is_active=True,
                    is_superuser=True,
                    is_verified=True,
                )

            domains["admin"].append(user)

        request_role_list = [
            m.Team(
                id=travel_guard_team_id,
                name=constants.travel_guard_team,
                is_active=True,
                slug=constants.travel_guard_team.lower(),
            ),
            m.Team(
                id=cover_more_team_id,
                name=constants.cover_more_team,
                is_active=True,
                slug=constants.cover_more_team.lower(),
            )
        ]

        db_session.add_all(request_role_list)
        await db_session.commit()

        request_user_list = [user for group in domains.values() for user in group]
        db_session.add_all(request_user_list)
        await db_session.commit()

 
        team_member_list= [
            m.TeamMember(
                user_id=user_obj.id,
                team_id=travel_guard_team_id
            )
            for user_obj in domains["travelguard"]
        ]

        team_member_list.extend(
            [
                m.TeamMember(
                    user_id=user_obj.id,
                    team_id=cover_more_team_id
                )
                for user_obj in domains["covermore"]
            ]
        )

        db_session.add_all(team_member_list)
        await db_session.commit()

def parse_minio_url(s3_url: str) -> tuple[str, str]:
    """Parse MinIO-style S3 URL into bucket name and key
    Args:
        s3_url (str): AWS S3 URL style `BUCKET/KEY`

    Returns:
        tuple: (bucket_name, key)
    """
    parts = s3_url.split("/", 1)
    if len(parts) != 2:
        error_mesg = "Invalid MinIO URL format. Expected 'BUCKET/KEY'."
        raise ValueError(error_mesg)
    return parts[0], parts[1]


async def read_minio_file(s3_url: str) -> bytes:
    """Read file content from MinIO.

    Args:
        s3_url (str): AWS S3 URL style `BUCKET/KEY`

    Returns:
        bytes: File content
    """
    bucket_name, key = parse_minio_url(s3_url)

    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
    ) as s3_client:  # type: ignore
        response = await s3_client.get_object(Bucket=bucket_name, Key=key)
        return await response["Body"].read()


async def delete_minio_file(s3_url: str) -> None:
    """Delete a file from MinIO.

    Args:
        s3_url (str): AWS S3 URL style `BUCKET/KEY`

    Raises:
        Exception: If deletion fails.
    """
    bucket_name, key = parse_minio_url(s3_url)

    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
    ) as s3_client:  # type: ignore
        response = await s3_client.delete_object(Bucket=bucket_name, Key=key)

        status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code not in {204, 200}:
            msg = f"Failed to delete {s3_url}, status code: {status_code}"
            raise Exception(msg)


async def save_file_to_minio(filename: str, content: bytes, content_type: str | None = None) -> str:
    """Save file content to MinIO.

    Args:
        filename (str): File name
        content (bytes): File content
        content_type (str): File content type (optional)

    Returns:
        str: minio url of the saved file
    """

    key = filename

    s3_url = f"{BUCKET}/{key}"
    if content_type is None:
        content_type, _ = mimetypes.guess_type(filename)

    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT_URL,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
        config=Config(signature_version="s3v4"),
    ) as s3_client:  # type: ignore
        existing_buckets = await s3_client.list_buckets()
        if not any(b["Name"] == BUCKET for b in existing_buckets["Buckets"]):
            await s3_client.create_bucket(Bucket=BUCKET)
        await s3_client.put_object(Bucket=BUCKET, Key=key, Body=content, ContentType=content_type)
        return s3_url