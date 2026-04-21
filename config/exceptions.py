"""Custom DRF exception handler to match Rails API contract.

Rails API returns:
- 404 → {"error": "..."}
- validation failures → {"errors": [...]} with status 422
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _flatten_errors(detail):
    if isinstance(detail, list):
        out = []
        for item in detail:
            out.extend(_flatten_errors(item))
        return out
    if isinstance(detail, dict):
        out = []
        for field, errs in detail.items():
            for err in _flatten_errors(errs):
                out.append(f"{field}: {err}" if field != "non_field_errors" else err)
        return out
    return [str(detail)]


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        else:
            detail = {"non_field_errors": exc.messages}
        return Response(
            {"errors": _flatten_errors(detail)},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, NotFound):
        return Response({"error": str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, PermissionDenied):
        return Response({"error": str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, ValidationError):
        return Response(
            {"errors": _flatten_errors(exc.detail)},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return response
