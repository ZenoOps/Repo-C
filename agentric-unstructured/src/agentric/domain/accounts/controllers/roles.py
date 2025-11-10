"""Role Routes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from litestar import Controller, get
from litestar.di import Provide

from agentric.domain.accounts.deps import provide_role_service
from agentric.domain.accounts.guards import requires_superuser
from agentric.domain.accounts.services import RoleService
from pydantic import BaseModel

class Role(BaseModel):
    id: UUID
    name: str


class RoleController(Controller):
    """Handles the adding and removing of new Roles."""
    path = "/api/roles"

    tags = ["Roles"]
    guards = [requires_superuser]
    dependencies = {"roles_service": Provide(provide_role_service)}

    @get("/list")
    async def list_roles(self, roles_service: RoleService) -> list[Role]:
        """List all roles."""
        roles = await roles_service.list()
        result = []
        for role in roles:
            data = roles_service.to_schema(role, schema_type=Role)
            if data.name == "CUSTOMER":
                continue
            result.append(data)
        return result
