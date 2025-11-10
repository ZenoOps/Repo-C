# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from litestar.config.response_cache import (
    ResponseCacheConfig,
    default_cache_key_builder,
)
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.security.jwt import OAuth2Login
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry

from agentric.config.app import open_telemetry_config
from agentric.domain.accounts.services import UserRoleService
from agentric.lib.utils import seed_db

if TYPE_CHECKING:
    from click import Group
    from litestar import Request
    from litestar.config.app import AppConfig
    from redis.asyncio import Redis


T = TypeVar("T")


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Application core configuration plugin.

    This class is responsible for configuring the main Litestar application with our routes, guards, and various plugins

    """

    __slots__ = ("app_slug", "redis")
    redis: Redis
    app_slug: str

    def on_cli_init(self, cli: Group) -> None:
        from agentric.cli.commands import user_management_group
        from agentric.config import get_settings

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        cli.add_command(user_management_group)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <litestar.config.app.AppConfig>` instance.
        """

        from uuid import UUID

        from advanced_alchemy.exceptions import RepositoryError
        from litestar.enums import RequestEncodingType
        from litestar.params import Body
        from litestar.security.jwt import Token

        from agentric.__about__ import __version__ as current_version
        from agentric.config import app as config
        from agentric.config import constants, get_settings
        from agentric.db import models as m
        from agentric.domain.accounts import signals as account_signals
        from agentric.domain.accounts.controllers import (
            AccessController,
            RoleController,
            UserController,
            UserRoleController,
        )
        from agentric.domain.accounts.deps import provide_user
        from agentric.domain.accounts.guards import auth as jwt_auth
        from agentric.domain.accounts.services import RoleService, UserService
        from agentric.domain.chats.controller import ChatController
        from agentric.domain.customers.controller import CustomerController
        from agentric.domain.requests.controller import RequestController
        from agentric.domain.system.controllers import SystemController
        from agentric.domain.teams.controllers.team_member import TeamMemberController
        from agentric.domain.teams.controllers.teams import TeamController
        from agentric.lib.exceptions import ApplicationError, exception_to_http_response
        from agentric.server import plugins

        settings = get_settings()
        self.redis = settings.redis.get_client()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        # openapi
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=current_version,
            components=[jwt_auth.openapi_components],
            security=[jwt_auth.security_requirement],
            use_handler_docstrings=True,
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        # jwt auth (updates openapi config)
        app_config = jwt_auth.on_app_init(app_config)
        # security
        app_config.cors_config = config.cors
        # templates
        # plugins
        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
                plugins.saq,
                plugins.problem_details,
                plugins.oauth,
                plugins.otel
            ],
        )

        # routes
        app_config.route_handlers.extend(
            [
                SystemController,
                RequestController,
                TeamController,
                TeamMemberController,
                AccessController,
                UserController,
                UserRoleController,
                RoleController,
                ChatController,
                CustomerController,
            ],
        )
        # signatures
        app_config.signature_namespace.update(
            {
                "Token": Token,
                "OAuth2Login": OAuth2Login,
                "RequestEncodingType": RequestEncodingType,
                "Body": Body,
                "m": m,
                "UUID": UUID,
                "UserService": UserService,
                "RoleService": RoleService,
                "UserRoleService": UserRoleService,
            },
        )
        # exception handling
        app_config.exception_handlers = {
            ApplicationError: exception_to_http_response,
            RepositoryError: exception_to_http_response,
        }
        # caching & redis
        app_config.response_cache_config = ResponseCacheConfig(
            default_expiration=constants.CACHE_EXPIRATION,
            key_builder=self._cache_key_builder,
        )
        app_config.stores = StoreRegistry(default_factory=self.redis_store_factory)
        app_config.on_shutdown.append(self.redis.aclose)  # type: ignore[attr-defined]
        # dependencies
        dependencies = {"current_user": Provide(provide_user)}
        app_config.dependencies.update(dependencies)
        # listeners
        app_config.listeners.extend(
            [
                account_signals.user_created_event_handler,
            ],
        )
        app_config.on_startup=[
            seed_db
        ]
        otel_config = open_telemetry_config
        app_config.middleware.insert(0, otel_config.middleware)

        return app_config

    def redis_store_factory(self, name: str) -> RedisStore:
        return RedisStore(self.redis, namespace=f"{self.app_slug}:{name}")

    def _cache_key_builder(self, request: Request) -> str:
        """App name prefixed cache key builder.

        Args:
            request (Request): Current request instance.

        Returns:
            str: App slug prefixed cache key.
        """

        return f"{self.app_slug}:{default_cache_key_builder(request)}"
