def serialize_llm_gateway_response(response):
    return {
        "provider": response.provider,
        "model": response.model,
        "status": response.status,
        "generated_text": response.generated_text,
        "safety_warnings": response.safety_warnings,
        "usage": response.usage,
        "metadata": response.metadata,
    }
