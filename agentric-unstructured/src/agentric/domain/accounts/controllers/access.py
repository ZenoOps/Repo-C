"""User Account Controllers."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated

from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body

from agentric.domain.accounts import urls
from agentric.domain.accounts.deps import provide_users_service
from agentric.domain.accounts.guards import (
    auth,
    requires_active_user,
    requires_superuser,
)
from agentric.domain.accounts.schemas import (
    AccountLogin,
    AccountRegister,
    User,
    UserDetail,
)
from agentric.domain.accounts.services import RoleService
from agentric.domain.teams.deps import provide_team_service
from agentric.domain.teams.services import TeamService
from agentric.lib.deps import create_service_provider

if TYPE_CHECKING:
    from litestar.security.jwt import OAuth2Login

    from agentric.db import models as m
    from agentric.domain.accounts.services import UserService


class AccessController(Controller):
    """User login and registration."""

    tags = ["Access"]
    dependencies = {
        "users_service": Provide(provide_users_service),
        "roles_service": Provide(create_service_provider(RoleService)),
        "team_service": Provide(provide_team_service)
    }

    @post(operation_id="AccountLogin", path=urls.ACCOUNT_LOGIN, exclude_from_auth=True)
    async def login(
        self,
        users_service: UserService,
        data: Annotated[
            AccountLogin,
            Body(title="OAuth2 Login", media_type=RequestEncodingType.URL_ENCODED),
        ],
    ) -> Response[OAuth2Login]:
        """Authenticate a user."""
        user = await users_service.authenticate(data.username, data.password)
        jti_value = str(uuid.uuid4())

        return auth.login(user.email, token_unique_jwt_id=jti_value)

    @post(
        operation_id="AccountLogout", path=urls.ACCOUNT_LOGOUT, exclude_from_auth=True
    )
    async def logout(self, request: Request) -> Response:
        """Account Logout"""
        request.cookies.pop(auth.key, None)
        request.clear_session()

        response = Response(
            {"message": "OK"},
            status_code=200,
        )
        response.delete_cookie(auth.key)

        return response

    @post(
        operation_id="AccountRegister",
        path=urls.ACCOUNT_REGISTER,
        guards=[requires_superuser],
    )
    async def signup(
        self,
        request: Request,
        users_service: UserService,
        team_service: TeamService,
        data: AccountRegister,
    ) -> User:
        """User Signup."""
        user_data = data.to_dict()
        assigned_team = await team_service.get_one_or_none(id=data.team_id)

        if not assigned_team:
            msg = "The designated team not found in database"
            raise ValueError(msg)

        user_data["is_verified"] = True
        user_data["is_active"] = True
        user = await users_service.create(user_data)
        request.app.emit(event_id="user_created", user_id=user.id)
        return users_service.to_schema(user, schema_type=User)

    @get(
        operation_id="AccountProfile",
        path=urls.ACCOUNT_PROFILE,
        guards=[requires_active_user],
    )
    async def profile(
        self, current_user: m.User, users_service: UserService
    ) -> UserDetail:
        """User Profile."""
        roles = current_user.roles
        user_role = roles[0].role.name if roles else ""
        team_id = current_user.teams[0].team_id if current_user.teams else None
        team_name = current_user.teams[0].team_name if current_user.teams else None

        return UserDetail(
            id=current_user.id,
            email=current_user.email,
            role=user_role,
            name=current_user.name,
            team_id=team_id,
            team_name=team_name,
            is_superuser=current_user.is_superuser
        )
