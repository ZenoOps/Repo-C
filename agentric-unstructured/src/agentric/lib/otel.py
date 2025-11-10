from __future__ import annotations

import base64
import copy
import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from litestar.contrib.opentelemetry import (
    OpenTelemetryConfig,
    OpenTelemetryInstrumentationMiddleware,
)
from litestar.middleware import AbstractMiddleware
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span

from agentric.config.base import OTEL

if TYPE_CHECKING:
    from litestar.types import ASGIApp
    from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware


class OpenTelemetrySingletonMiddleware(OpenTelemetryInstrumentationMiddleware):
    """OpenTelemetry Singleton Middleware

    https://github.com/litestar-org/litestar/issues/3056
    """

    __open_telemetry_middleware__: ClassVar[OpenTelemetryMiddleware]

    def __init__(self, app: ASGIApp, config: OpenTelemetryConfig) -> None:
        cls = self.__class__
        if singleton_middleware := getattr(cls, "__open_telemetry_middleware__", None):
            AbstractMiddleware.__init__(
                self,
                app,
                scopes=config.scopes,
                exclude=config.exclude,
                exclude_opt_key=config.exclude_opt_key,
            )
            self.open_telemetry_middleware = copy.copy(singleton_middleware)
            self.open_telemetry_middleware.app = app
        else:
            super().__init__(app, config)
            cls.__open_telemetry_middleware__ = self.open_telemetry_middleware

def get_authorization_header(headers: list[tuple[bytes, bytes]]) -> str | None:
    """Extract the Authorization header from a list of (name, value) tuples.

    Args:
        headers: List of (header_name, header_value) tuples

    Returns:
        str: Authorization header value if found, None otherwise
    """
    for name, value in headers:
        logging.warning(f"Header: {name}={value}")
        if name.decode("utf8").lower() == "authorization":
            logging.warning(f"Authorization Header: {value}")
            return str(value)
    return None

def parse_jwt_token(header:str)->dict:
    """Parse a JWT token from a Bearer authorization header.

    Args:
        token (str): Full JWT token

    Returns:
        dict: Decoded JWT payload
    """
    token = header.split(" ")[1]  # Extract token from "Bearer <token>"
    token_parts = token.split(".")
    # Decode the payload (the second part)
    payload_decoded = base64.b64decode(token_parts[1] + "==").decode("utf-8")  # Add padding if needed
    payload_json: dict = json.loads(payload_decoded)
    return payload_json

def configure_instrumentation() -> OpenTelemetryConfig:
    """Initialize Open Telemetry configuration."""
    from opentelemetry import metrics

    otel_settings = OTEL()
    """Configures the OpenTelemetry SDK with a Jaeger exporter."""
    resource = Resource.create({SERVICE_NAME: otel_settings.SERVICE_NAME})

    provider = TracerProvider(resource=resource)

    oltp_exporter = OTLPSpanExporter(
        endpoint=otel_settings.EXPORTER_OTLP_ENDPOINT,  # Default OTLP gRPC endpoint
        insecure=otel_settings.INSECURE,
    )

    processor: SpanProcessor = BatchSpanProcessor(oltp_exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    GoogleGenAIInstrumentor().instrument(tracer_provider=provider)
    configuration = {
        "system.memory.usage": ["used", "free", "cached"],
        "system.cpu.time": ["idle", "user", "system", "irq"],
        "system.network.io": ["transmit", "receive"],
        "process.memory.usage": None,
        "process.memory.virtual": None,
        "process.cpu.time": ["user", "system"],
        "process.context_switches": ["involuntary", "voluntary"],
    }
    SystemMetricsInstrumentor(
        config=configuration,
    ).instrument()

    def server_request_hook_handler(span: Span, scope: dict[str, Any]) -> None:
        logging.info(scope)
        if span.is_recording():
            logging.info("Processing server request hook for span attributes")
            logging.warning(scope)
            headers = scope.get("headers", [])
            logging.warning(headers)

            if headers:
                authorization_header = get_authorization_header(headers)
                if authorization_header:
                    try:
                        jwt_payload = parse_jwt_token(authorization_header)
                        logging.warning(jwt_payload)
                        user = jwt_payload.get("sub")
                        session = jwt_payload.get("jti")
                        if user:
                            span.set_attribute("user", user)
                        if session:
                            span.set_attribute("session_id",session)
                    except ValueError as e:
                        logging.warning(f"Failed to parse JWT token: {e!s}")

    return OpenTelemetryConfig(
        tracer_provider=provider,
        meter=metrics.get_meter(__name__),
        middleware_class=OpenTelemetrySingletonMiddleware,
        server_request_hook_handler=server_request_hook_handler,
        client_request_hook_handler=server_request_hook_handler,
    )
