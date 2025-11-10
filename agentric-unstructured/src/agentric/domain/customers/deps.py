"""Chat Controllers."""

from __future__ import annotations

from agentric.domain.customers.services import CustomerService
from agentric.lib.deps import create_service_provider

__all__ = ["provide_customer_service"]


provide_customer_service = create_service_provider(
    CustomerService,
    error_messages={
        "duplicate_key": "This customer already exists.",
        "integrity": "Customer operation failed.",
    },
)
