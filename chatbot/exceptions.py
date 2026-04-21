from django.db.utils import DatabaseError, OperationalError, ProgrammingError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # Return JSON instead of HTML traceback for transient DB outages.
    if isinstance(exc, OperationalError):
        return Response(
            {"error": "Database connection temporarily unavailable. Please retry in a few seconds."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Missing relations/tables after deploy should surface as JSON for clients.
    if isinstance(exc, ProgrammingError):
        return Response(
            {"error": "Database schema is not ready. Run migrations and retry."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Catch-all for other DB-level failures.
    if isinstance(exc, DatabaseError):
        return Response(
            {"error": "Database error occurred. Please try again shortly."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return response
