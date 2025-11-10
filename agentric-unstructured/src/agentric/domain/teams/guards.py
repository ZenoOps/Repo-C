from uuid import UUID

from litestar.connection import ASGIConnection
from litestar.exceptions import PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler

from agentric.config import constants
from agentric.db.models.enums import TeamRoles

__all__ = ["requires_team_admin", "requires_team_membership", "requires_team_ownership"]


def requires_has_one_team(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user has one team.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    if len(connection.user.teams) > 0:
        return
    if connection.user.is_superuser or (connection.user.teams and len(connection.user.teams) > 0):
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access this operation.")

def requires_team_membership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a member of the team.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    value = connection.path_params["team_id"]
    team_id = value if isinstance(value, UUID) else UUID(value)


    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name in {constants.SUPERUSER_ACCESS_ROLE}
    )
    has_team_role = any(
        membership.team.id == team_id for membership in connection.user.teams
    )
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify the connection user is a team admin.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    value = connection.path_params["team_id"]
    team_id = value if isinstance(value, UUID) else UUID(value)
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name in {constants.SUPERUSER_ACCESS_ROLE}
    )
    has_team_role = any(
        membership.team.id == team_id and membership.role == TeamRoles.ADMIN.value
        for membership in connection.user.teams
    )
    if connection.user.is_superuser or has_system_role or has_team_role:
        return
    raise PermissionDeniedException(detail="Insufficient permissions to access team.")


def requires_team_admin_or_ownership(
    connection: ASGIConnection, _: BaseRouteHandler
) -> None:
    """Verify that the connection user is the team admin or owner.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    value = connection.path_params["team_id"]
    team_id = value if isinstance(value, UUID) else UUID(value)
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name in {constants.SUPERUSER_ACCESS_ROLE}
    )
    is_team_owner = False
    is_team_admin = False
    for membership in connection.user.teams:

        if membership.team.id == team_id and membership.is_owner:
            is_team_owner = True
            break

        if membership.team.id == team_id and membership.role == TeamRoles.ADMIN.value:
            is_team_admin = True
            break

    if (
        connection.user.is_superuser
        or has_system_role
        or is_team_owner
        or is_team_admin
    ):
        return

    msg = "Insufficient permissions to access team."
    raise PermissionDeniedException(detail=msg)


def requires_team_ownership(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Verify that the connection user is the team owner.

    Args:
        connection (ASGIConnection): _description_
        _ (BaseRouteHandler): _description_

    Raises:
        PermissionDeniedException: _description_
    """
    team_id = UUID(connection.path_params["team_id"])
    has_system_role = any(
        assigned_role.role_name
        for assigned_role in connection.user.roles
        if assigned_role.role_name in {constants.SUPERUSER_ACCESS_ROLE}
    )
    has_team_role = any(
        membership.team.id == team_id and membership.is_owner
        for membership in connection.user.teams
    )
    if connection.user.is_superuser or has_system_role or has_team_role:
        return

    msg = "Insufficient permissions to access team."
    raise PermissionDeniedException(detail=msg)
