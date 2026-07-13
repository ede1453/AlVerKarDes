# AI Consumer Intelligence v1.0.0 Production Handoff

## Verified locally

- Production image builds
- PostgreSQL and Redis are healthy
- Alembic reaches head
- Production API is healthy on port 18000
- Health and OpenAPI smoke tests pass
- Full automated test suite passes

## Remaining before public internet launch

1. Configure a real domain and DNS.
2. Install TLS certificates and enable the Nginx `edge` profile.
3. Set the real frontend domain in CORS.
4. Replace all test passwords and secrets.
5. Create and externally store the first database backup.
6. Complete a restore drill.
7. Configure real marketplace credentials.
8. Run real connector smoke tests.
9. Verify monitoring and alert delivery.

## Final validation

```powershell
powershell -ExecutionPolicy Bypass `
  -File .\scriptsinal_release_validation.ps1
```
