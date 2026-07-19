# Sonraki Fazlar

## Faz A — RC401-RC440: Production hardening

Bu paketin kapsamı:

- release secret hijyeni
- sanitized ZIP builder
- CORS ve trusted hosts
- security headers
- request-size sınırı
- liveness/readiness
- production environment gate
- connector fixture gate
- auth coverage raporu
- uygulama sürümünün tekilleştirilmesi

## Faz B — Authorization ve tenant security

Önerilen sonraki 40'lı RC:

- endpoint sınıflandırması
- authenticated-user zorunluluğu
- role/permission modeli
- admin endpoint koruması
- ownership kontrolleri
- tenant isolation
- audit log
- refresh-token rotation
- account lockout
- password reset/email verification

## Faz C — Gerçek connector activation

- Amazon Creators gerçek credential/onboarding
- eBay Browse API gerçek OAuth ve access approval
- Idealo gerçek partner feed/API
- affiliate network webhook/postback
- credential secret manager
- sandbox/production ayrımı
- connector contract tests
- scheduled collection
- real price snapshots
- source SLA dashboard

## Faz D — Distributed runtime

- scheduler state Redis/PostgreSQL
- distributed locks
- leader election lease
- durable job queue
- idempotent worker execution
- notification state persistence
- horizontal scaling tests
- chaos/recovery tests

## Faz E — Product API ve kullanıcı deneyimi

- frontend/mobile BFF
- onboarding
- saved search/watchlist
- personalized deal feed
- notification preference UI
- purchase intent
- affiliate disclosure UI
- account and privacy controls

## Faz F — Public deployment

- domain/DNS
- TLS
- reverse proxy/WAF
- managed PostgreSQL/Redis
- secret manager
- Sentry/Prometheus/Grafana/Loki/Tempo
- backups and restore drills
- GDPR/privacy/retention
- load/performance/security testing
