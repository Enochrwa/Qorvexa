from app.main import create_app


def _ok_schema(path: str) -> dict[str, object]:
    op = create_app().openapi()["paths"][path]["get"]
    schema: dict[str, object] = op["responses"]["200"]["content"]["application/json"]["schema"]
    return schema


def test_catalog_responses_are_documented_so_the_frontend_is_typed() -> None:
    assert _ok_schema("/api/v1/titles")["$ref"].endswith("/TitleList")  # type: ignore[union-attr]
    assert _ok_schema("/api/v1/titles/{slug}")["$ref"].endswith("/TitleDetail")  # type: ignore[union-attr]
    assert _ok_schema("/api/v1/genres")["type"] == "array"
    assert _ok_schema("/api/v1/titles/{slug}/seasons")["type"] == "array"


def test_not_modified_is_documented() -> None:
    op = create_app().openapi()["paths"]["/api/v1/titles"]["get"]
    assert "304" in op["responses"]
