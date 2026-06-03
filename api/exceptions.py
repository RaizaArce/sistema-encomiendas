from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'error': True,
            'status_code': response.status_code,
            'message': response.data.get('detail', str(exc)) if isinstance(response.data, dict) else str(exc),
        }

        if isinstance(response.data, dict):
            detail = response.data.pop('detail', None)
            custom_data['errors'] = response.data
            if detail:
                custom_data['message'] = detail

        response.data = custom_data

    return response
