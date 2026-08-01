"""Structured errors returned by the planner boundary."""

from __future__ import annotations

from typing import Any


class PlannerError(Exception):
    """Base exception that can be returned as the planner JSON error envelope."""

    code = "planner_error"
    status_code = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, dict[str, Any]]:
        """Serialize the error using the public HTTP contract."""

        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class InvalidRequestError(PlannerError):
    """Raised when a planner request cannot be processed."""

    code = "invalid_request"
    status_code = 422


class UnsupportedRequestError(PlannerError):
    """Raised when the model identifies a request as outside CAD planning."""

    code = "unsupported_request"
    status_code = 422


class PlannerConfigurationError(PlannerError):
    """Raised when required planner configuration is absent or invalid."""

    code = "planner_configuration_error"
    status_code = 500


class ProviderRequestError(PlannerError):
    """Raised when the configured LLM provider cannot complete a request."""

    code = "provider_request_failed"
    status_code = 502


class MalformedModelResponseError(PlannerError):
    """Raised when the provider response cannot be parsed as planner JSON."""

    code = "malformed_model_response"
    status_code = 502


class InvalidModelResponseError(PlannerError):
    """Raised when valid JSON violates the planner output contract."""

    code = "invalid_model_response"
    status_code = 502
