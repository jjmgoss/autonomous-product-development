from apd.app.main import app


def test_fastapi_app_importable() -> None:
    assert app is not None
    assert app.title == "APD Local App"
