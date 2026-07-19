from app.domains.auth_core.tokens import TokenCodec

def test_rc442_access_token_contains_required_claims():
    codec = TokenCodec(
        secret="A"*64+"1!",
        algorithm="HS256",
        issuer="aici",
        audience="aici-api",
        access_minutes=30,
    )
    token, _ = codec.encode_access_token(
        user_id="user-1",
        session_id="session-1",
        security_version=3,
    )
    claims = codec.decode_access_token(token)
    for key in ("sub","sid","sv","jti","iss","aud","exp","typ"):
        assert key in claims
    assert claims["sv"] == 3
