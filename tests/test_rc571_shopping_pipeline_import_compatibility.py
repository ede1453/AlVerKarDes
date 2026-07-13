def test_rc571_shopping_pipeline_service_imports_successfully():
    from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService

    assert ShoppingPipelineService is not None


def test_rc571_shopping_pipeline_router_imports_successfully():
    from app.api.v1.shopping_pipeline_router import router

    assert router is not None
