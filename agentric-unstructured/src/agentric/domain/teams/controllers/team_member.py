"""User Account Controllers."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.exceptions import IntegrityError, RepositoryError
from advanced_alchemy.service import FilterTypeT  # noqa: TC002
from litestar import Controller, get, post, put
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Dependency, Parameter
from sqlalchemy.orm import selectinload

from agentric.db import models as m
from agentric.db.models.enums import TeamRoles
from agentric.domain.accounts.deps import provide_users_service
from agentric.domain.teams import urls
from agentric.domain.teams.deps import provide_team_service
from agentric.domain.teams.guards import (
    requires_team_admin_or_ownership,
    requires_team_membership,
)
from agentric.domain.teams.schemas import Team, TeamMember, TeamMemberModify, TeamMemberRemove
from agentric.domain.teams.services import TeamMemberService, TeamService
from agentric.lib.deps import create_filter_dependencies, create_service_provider

if TYPE_CHECKING:

    from advanced_alchemy.service.pagination import OffsetPagination

    from agentric.domain.accounts.services import UserService

logger = getLogger()

class TeamMemberController(Controller):
    """Team Members."""

    tags = ["Team Members"]
    dependencies = {
        "teams_service": Provide(provide_team_service),
        "team_members_service": create_service_provider(
            TeamMemberService,
            load=[
                selectinload(m.TeamMember.team),
                selectinload(m.TeamMember.user),
            ],
        ),
        "users_service": Provide(provide_users_service),
    } | create_filter_dependencies(
        {
            "id_filter": UUID,
            "search": "name,email",
            "pagination_type": "limit_offset",
            "pagination_size": 20,
            "created_at": True,
            "updated_at": True,
            "sort_field": "name",
            "sort_order": "asc",
        },
    )

    @get(
        operation_id="ListMyTeamMembers",
        path=urls.TEAM_MEMBER_LIST,
        guards=[requires_team_membership],
    )
    async def list_team_members(
        self,
        team_members_service: TeamMemberService,
        current_user: m.User,
        team_id: Annotated[
            UUID, Parameter(title="Team ID", description="The team to retrieve.")
        ],
        filters: Annotated[list[FilterTypeT], Dependency(skip_validation=True)],
    ) -> OffsetPagination[TeamMember]:
        """List teams that user account is currently a member of.."""
        message = "Unknown error"
        try:
            results, total = await team_members_service.list_and_count(
                *filters, team_id=team_id
            )
            return team_members_service.to_schema(
                data=results, total=total, schema_type=TeamMember, filters=filters
            )

        except IntegrityError:
            logger.info("IntegrityError")
            message =  "IntegrityError: Please use the right filter parameters"
            raise HTTPException(detail=message, status_code=400)
        except RepositoryError:
            message = "RepositoryError: Please check the field name are correct"
        raise HTTPException(detail=message, status_code=500)

    @post(
        operation_id="AddMemberToTeam",
        path=urls.TEAM_ADD_MEMBER,
        guards=[requires_team_admin_or_ownership],
    )
    async def add_member_to_team(
        self,
        teams_service: TeamService,
        users_service: UserService,
        data: TeamMemberModify,
        team_id: UUID = Parameter(title="Team ID", description="The team to update."),
    ) -> Team:
        """Add a member to a team."""
        team_obj = await teams_service.get(team_id)
        user_obj = await users_service.get_one(email=data.member_email)
        is_member = any(membership.team.id == team_id for membership in user_obj.teams)
        if is_member:
            msg = "User is already a member of the team."
            raise IntegrityError(msg)
        team_obj.members.append(
            m.TeamMember(user_id=user_obj.id, team_id=team_id, role=TeamRoles.MEMBER)
        )
        team_obj = await teams_service.update(item_id=team_id, data=team_obj)
        return teams_service.to_schema(schema_type=Team, data=team_obj)

    @post(
        operation_id="RemoveMemberFromTeam",
        path=urls.TEAM_REMOVE_MEMBER,
        guards=[requires_team_admin_or_ownership],
    )
    async def remove_member_from_team(
        self,
        teams_service: TeamService,
        team_members_service: TeamMemberService,
        users_service: UserService,
        data: TeamMemberRemove,
        team_id: UUID = Parameter(title="Team ID", description="The team to delete."),
    ) -> Team:
        """Revoke a members access to a team."""
        user_obj = await users_service.get_one(email=data.member_email)
        removed_member = False
        for membership in user_obj.teams:
            if membership.user_id == user_obj.id:
                _ = await team_members_service.delete(membership.id)
                removed_member = True
                break
        if not removed_member:
            msg = "User is not a member of this team."
            raise IntegrityError(msg)
        team_obj = await teams_service.get(team_id)
        return teams_service.to_schema(schema_type=Team, data=team_obj)

    @put(
        operation_id="UpdateTeamMember",
        path=urls.TEAM_MEMBER_ROLE_UPDATE,
        guards=[requires_team_admin_or_ownership],
    )
    async def update_team_member_role(
        self,
        data: TeamMemberModify,
        team_members_service: TeamMemberService,
        users_service: UserService,
        current_user: m.User,
        team_id: UUID = Parameter(title="Team ID", description="The team to update."),
    ) -> TeamMember:
        """Update the role of a team member."""
        user_obj = await users_service.get_one(email=data.member_email)
        team_member_obj = await team_members_service.get_one_or_none(
            team_id=team_id, user_id=user_obj.id
        )

        if team_member_obj is None:
            msg = "User is not a member of this team."
            raise NotFoundException(msg)
        if data.role is not None:
            team_member_obj.role = data.role

        team_member_obj = await team_members_service.update(
            item_id=team_member_obj.id, data=team_member_obj
        )

        return team_members_service.to_schema(
            schema_type=TeamMember, data=team_member_obj
        )
