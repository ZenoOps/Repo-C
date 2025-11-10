"""Chat Controllers."""

from __future__ import annotations

from agentric.db import models as m
from agentric.domain.teams.services import TeamService
from agentric.lib.deps import create_service_provider

__all__ = ["provide_team_service"]

provide_team_service = create_service_provider(
    TeamService,
    load=[m.Team.members],
    error_messages={
        "duplicate_key": "This Team already exists.",
        "integrity": "Team Operations failed.",
    },
)
