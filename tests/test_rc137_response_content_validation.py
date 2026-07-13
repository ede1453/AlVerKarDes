from app.domains.commerce_ingestion.production_http import (
    ResponseContentValidator,
)


def test_rc137_valid_json_content():
    result = ResponseContentValidator().validate(
        status_code=200,
        headers={
            "content-type":"application/json"
        },
        body='{"items":[]}',
    )
    assert result["valid"] is True

def test_rc137_invalid_content_type():
    result = ResponseContentValidator().validate(
        status_code=200,
        headers={"content-type":"text/html"},
        body="<html></html>",
    )
    assert result["valid"] is False
    assert result["reason"] == "UNSUPPORTED_CONTENT_TYPE"
