"""Topic and API naming helpers for the FocusGuard platform."""


def build_api_route(resource: str) -> str:
    return f"/api/{resource.strip('/')}"
