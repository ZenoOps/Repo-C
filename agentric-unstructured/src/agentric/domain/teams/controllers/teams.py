"""User Account Controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.service import FilterTypeT  # noqa: TC002
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from agentric.db import models as m
from agentric.domain.accounts.guards import requires_superuser
from agentric.domain.teams import urls
from agentric.domain.teams.guards import requires_team_admin_or_ownership
from agentric.domain.teams.schemas import Team, TeamCreate, TeamUpdate
from agentric.domain.teams.services import TeamService
from agentric.lib.deps import create_service_dependencies

if TYPE_CHECKING:
    from advanced_alchemy.service.pagination import OffsetPagination


class TeamController(Controller):
    """Teams."""

    tags = ["Teams"]
    dependencies = create_service_dependencies(
        TeamService,
        key="teams_service",
        load=[m.Team.members],
        filters={"id_filter": UUID},
    )

    @get(operation_id="ListTeams", path=urls.TEAM_LIST, guards = [requires_superuser])
    async def list_team(
        self,
        teams_service: TeamService,
        filters: Annotated[list[FilterTypeT], Dependency(skip_validation=True)],
    ) -> OffsetPagination[Team]:
        """List teams that user account is currently a member of.."""
        results, total = await teams_service.list_and_count(*filters)
        return teams_service.to_schema(data=results, total=total, schema_type=Team, filters=filters)


    @post(operation_id="CreateTeam", path=urls.TEAM_CREATE, guards = [requires_superuser])
    async def create_team(self, teams_service: TeamService, current_user: m.User, data: TeamCreate) -> Team:
        """Create a new team."""
        obj = data.to_dict()
        obj.update({"owner_id": current_user.id, "owner": current_user})
        db_obj = await teams_service.create(obj)
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @get(operation_id="GetTeam", path=urls.TEAM_DETAIL,  guards=[requires_team_admin_or_ownership])
    async def get_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to retrieve.")],
    ) -> Team:
        """Get details about a team."""
        db_obj = await teams_service.get(team_id)
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @patch(operation_id="UpdateTeam", path=urls.TEAM_UPDATE, guards=[requires_team_admin_or_ownership])
    async def update_team(
        self,
        data: TeamUpdate,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to update.")],
    ) -> Team:
        """Update a migration team."""
        db_obj = await teams_service.update(
            item_id=team_id,
            data=data.to_dict(),
        )
        return teams_service.to_schema(schema_type=Team, data=db_obj)

    @delete(operation_id="DeleteTeam", path=urls.TEAM_DELETE,  guards=[requires_team_admin_or_ownership])
    async def delete_team(
        self,
        teams_service: TeamService,
        team_id: Annotated[UUID, Parameter(title="Team ID", description="The team to delete.")],
    ) -> None:
        """Delete a team."""
        _ = await teams_service.delete(team_id)
