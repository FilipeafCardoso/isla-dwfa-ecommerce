"""Erros no formato Problem Details (RFC 9457) · errors as Problem Details."""

from rest_framework.views import exception_handler


def problem_details_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:  # not a DRF exception → 500, logged · não é exceção DRF → 500
        return None
    detail = response.data
    response.data = {
        "type": "about:blank",
        "title": response.status_text,
        "status": response.status_code,
        "errors": detail if isinstance(detail, dict) else {"detail": detail},
    }
    return response
