from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.plugins.problem_details import ProblemDetailsPlugin
from litestar.plugins.structlog import StructlogPlugin
from litestar_granian import GranianPlugin
from litestar_saq import SAQPlugin
from litestar_vite import VitePlugin

from agentric.config import app as config
from agentric.lib.oauth import OAuth2ProviderPlugin
from litestar.contrib.opentelemetry import OpenTelemetryPlugin

otel = OpenTelemetryPlugin(config=config.open_telemetry_config)
structlog = StructlogPlugin(config=config.log)
vite = VitePlugin(config=config.vite)
saq = SAQPlugin(config=config.saq)
alchemy = SQLAlchemyPlugin(config=config.alchemy)
granian = GranianPlugin()
problem_details = ProblemDetailsPlugin(config=config.problem_details)
oauth = OAuth2ProviderPlugin()