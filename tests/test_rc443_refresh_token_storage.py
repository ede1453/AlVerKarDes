from app.domains.auth_core.tokens import create_opaque_token, hash_opaque_token

def test_rc443_refresh_token_is_opaque_and_hashable():
    token = create_opaque_token()
    assert len(token) >= 64
    assert token != hash_opaque_token(token)
    assert len(hash_opaque_token(token)) == 64
