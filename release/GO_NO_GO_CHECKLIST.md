# v1.0.0 Go/No-Go Checklist

- [ ] Production API container healthy
- [ ] `/health` HTTP 200
- [ ] `/openapi.json` HTTP 200
- [ ] Full pytest suite passed
- [ ] OpenAPI uniqueness passed
- [ ] Alembic head: `0014_deal_storage_sqlalchemy`
- [ ] PostgreSQL and Redis healthy
- [ ] No placeholders in `.env.production`
- [ ] Strong PostgreSQL password
- [ ] `JWT_SECRET` at least 32 random characters
- [ ] Backup created
- [ ] Restore drill passed
- [ ] Real domain and TLS ready
- [ ] CORS limited to real frontend domain
- [ ] Connector credentials stored securely
- [ ] Monitoring and alert receiver verified

Do not expose the platform publicly until every mandatory item is complete.
