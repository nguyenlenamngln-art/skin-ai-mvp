from skin_ai.product_api_mobile_v14 import app


def _route_paths():
    return [getattr(route, "path", None) for route in app.router.routes]


def test_dermatoscope_api_routes_registered_before_root_web_mount():
    routes = app.router.routes
    web_indices = [i for i, route in enumerate(routes) if getattr(route, "name", None) == "web"]
    assert web_indices, "root SPA mount must exist"
    web_index = web_indices[-1]

    required = {
        "/v1/dermatoscope/position-summary",
        "/v1/dermatoscope/sessions/resumable/latest",
        "/v1/dermatoscope/captures/{capture_id}/analyze",
    }
    paths = _route_paths()
    for path in required:
        assert path in paths, f"missing API route: {path}"
        assert paths.index(path) < web_index, f"{path} is shadowed by root web mount"


def test_root_web_mount_is_last_route():
    routes = app.router.routes
    assert getattr(routes[-1], "name", None) == "web"
