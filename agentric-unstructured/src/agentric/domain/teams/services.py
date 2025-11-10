from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.repository import (
    SQLAlchemyAsyncRepository,
    SQLAlchemyAsyncSlugRepository,
)
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    is_dict_with_field,
    is_dict_without_field,
    schema_dump,
)
from uuid_utils.compat import uuid4

from agentric.config import constants
from agentric.db import models as m
from agentric.db.models.enums import TeamRoles

if TYPE_CHECKING:
    from uuid import UUID

    from advanced_alchemy.service import ModelDictT

__all__ = (
    "TeamMemberService",
    "TeamService",
)


class TeamService(SQLAlchemyAsyncRepositoryService[m.Team]):
    """Team Service."""

    class TeamRepository(SQLAlchemyAsyncSlugRepository[m.Team]):
        """Team Repository."""

        model_type = m.Team

    repository_type = TeamRepository
    match_fields = ["name"]

    async def to_model_on_create(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner(data, "create")

    async def to_model_on_update(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner(data, "update")

    async def to_model_on_upsert(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        data = schema_dump(data)
        data = await self._populate_slug(data)
        return await self._populate_with_owner(data, "upsert")

    @staticmethod
    def can_view_all(user: m.User) -> bool:
        return bool(
            user.is_superuser
            or any(
                assigned_role.role.name
                for assigned_role in user.roles
                if assigned_role.role.name in {constants.SUPERUSER_ACCESS_ROLE}
            ),
        )

    async def _populate_slug(self, data: ModelDictT[m.Team]) -> ModelDictT[m.Team]:
        if is_dict_without_field(data, "slug") and is_dict_with_field(data, "name"):
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return data

    async def _populate_with_owner(
        self,
        data: ModelDictT[m.Team],
        operation: str | None,
    ) -> ModelDictT[m.Team]:
        if operation == "create" and is_dict(data):
            owner_id: UUID | None = data.pop("owner_id", None)
            owner: m.User | None = data.pop("owner", None)

            data["id"] = data.get("id", uuid4())
            data = await super().to_model(data)

            if owner:
                data.members.append(m.TeamMember(user=owner, role=TeamRoles.ADMIN, is_owner=True))
            elif owner_id:
                data.members.append(m.TeamMember(user_id=owner_id, role=TeamRoles.ADMIN, is_owner=True))

        if operation == "update" and is_dict(data):
            data = await super().to_model(data)

        return data


class TeamMemberService(SQLAlchemyAsyncRepositoryService[m.TeamMember]):
    """Team Member Service."""

    class TeamMemberRepository(SQLAlchemyAsyncRepository[m.TeamMember]):
        """Team Member Repository."""

        model_type = m.TeamMember

    repository_type = TeamMemberRepository
