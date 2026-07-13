from scripts.api_contract_snapshot import extract_contract


def test_api_contract_snapshot_extractor_compacts_openapi_paths():
    openapi = {
        "paths": {
            "/api/v1/test": {
                "post": {
                    "operationId": "createTest",
                    "tags": ["test"],
                    "summary": "Create Test",
                    "requestBody": {
                        "content": {
                            "application/json": {},
                        }
                    },
                    "responses": {
                        "200": {},
                        "422": {},
                    },
                }
            }
        }
    }

    contract = extract_contract(openapi)

    assert contract["version"] == "v1"
    assert contract["path_count"] == 1
    assert contract["paths"]["/api/v1/test"]["post"]["operationId"] == "createTest"
    assert contract["paths"]["/api/v1/test"]["post"]["responses"] == ["200", "422"]
