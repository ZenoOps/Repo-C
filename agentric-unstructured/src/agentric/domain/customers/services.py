from __future__ import annotations

from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
)
from advanced_alchemy.service import ModelDictT, SQLAlchemyAsyncRepositoryService, is_dict, schema_dump
from litestar.exceptions import PermissionDeniedException

from agentric.db import models as m
from agentric.lib import crypt


class CustomerService(SQLAlchemyAsyncRepositoryService[m.Customer]):
    """Handles database operations for Customer"""

    class Repository(SQLAlchemyAsyncRepository[m.Customer]):
        """Customer SQLAlchemy Repository."""

        model_type = m.Customer

    repository_type = Repository


    async def to_model_on_create(
        self, data: ModelDictT[m.Customer]
    ) -> ModelDictT[m.Customer]:
        """Prepare and transform input data for creating a new Customer record.

        Ensures that all necessary fields are populated.
        """
        return await self._populate_model(data)

    async def to_model_on_update(
        self, data: ModelDictT[m.Customer]
    ) -> ModelDictT[m.Customer]:
        """Prepare and transform input data for updating an existing Customer record.

        Ensures that updated fields are handled correctly.
        """
        return await self._populate_model(data)

    async def to_model_on_upsert(
        self, data: ModelDictT[m.Customer]
    ) -> ModelDictT[m.Customer]:
        """Prepare and transform input data for upserting (create or update) a Customer record.

        Ensures that all necessary fields are handled.
        """
        return await self._populate_model(data)

    async def authenticate(self, username: str, password: bytes | str) -> m.Customer:
        """Authenticate a customer user by verifying the provided credentials.

        Args:
            username: The customer's email address.
            password: The plaintext or byte-encoded password to verify.

        Returns:
            The authenticated Customer object if credentials are valid.

        Raises:
            PermissionDeniedException: If the customer is not found or the password is invalid.
        """
        db_obj = await self.get_one_or_none(email_address=username)
        if db_obj is None:
            msg = "Customer not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        if not await crypt.verify_password(password, db_obj.hashed_password):
            msg = "Customer not found or password invalid"
            raise PermissionDeniedException(detail=msg)
        return db_obj

    async def update_password(self, data: dict[str, str], db_obj: m.Customer) -> None:
        """Update the password for an existing customer user after verifying the current password.

        Args:
            data: Dictionary containing 'current_password' and 'new_password'.
            db_obj: The Analyst object whose password is to be updated.

        Raises:
            PermissionDeniedException: If the current password is invalid.
        """
        if not await crypt.verify_password(
            data["current_password"], db_obj.hashed_password
        ):
            msg = "Customer not found or password invalid."
            raise PermissionDeniedException(detail=msg)
        db_obj.hashed_password = await crypt.get_password_hash(data["new_password"])
        await self.repository.update(db_obj)

    async def _populate_model(
        self, data: ModelDictT[m.Customer]
    ) -> ModelDictT[m.Customer]:
        """Internal helper to prepare model data, including schema dumping and password hashing."""
        data = schema_dump(data)
        return await self._populate_with_hashed_password(data)

    async def _populate_with_hashed_password(
        self, data: ModelDictT[m.Customer]
    ) -> ModelDictT[m.Customer]:
        """Internal helper to hash the password if present in the input data."""
        if is_dict(data) and (password := data.pop("password", None)) is not None:
            data["hashed_password"] = await crypt.get_password_hash(password)
        return data

