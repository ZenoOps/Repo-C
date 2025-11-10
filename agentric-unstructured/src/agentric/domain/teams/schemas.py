from __future__ import annotations

from uuid import UUID  # noqa: TC003

import msgspec

from agentric.db.models.enums import TeamRoles
from agentric.lib.schema import CamelizedBaseStruct


class TeamMember(CamelizedBaseStruct):
    id: UUID
    user_id: UUID
    email: str | msgspec.UnsetType = msgspec.UNSET
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False


class TeamBrief(CamelizedBaseStruct):
    id: UUID
    name: str

class Team(CamelizedBaseStruct):
    id: UUID
    name: str
    description: str | None = None
    members: list[TeamMember] = []


class TeamCreate(CamelizedBaseStruct):
    """Team Create."""
    name: str
    description: str | None = None

class TeamUpdate(CamelizedBaseStruct, omit_defaults=True):
    name: str | None | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET


class TeamMemberModify(CamelizedBaseStruct):
    """Team Member Modify."""

    member_email: str
    role: TeamRoles | None = TeamRoles.MEMBER
    is_owner: bool | None = False

class TeamMemberRemove(CamelizedBaseStruct):
    """Team Member Remove."""
    member_email: str
