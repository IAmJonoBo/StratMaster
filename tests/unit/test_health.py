import importlib


def test_health_route():
    app_module = importlib.import_module("packages.api.app.main")
    app = getattr(app_module, "app", None)
    assert app is not None, "FastAPI app should be defined"
    # Basic contract check: route exists
    routes = [r.path for r in app.router.routes]
    assert "/health" in routes
