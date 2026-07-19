# ARŞİV — KULLANMA

Bu klasördeki 151 `run_rcXX_*.ps1` dosyası, eski RC1-614 serisinin (bkz.
`WIKI_ROOT/05-Decisions/ADR-001-RC-Numaralandirma-Reset.md`) her bir madde/batch'i
için manuel olarak çalıştırılan doğrulama script'leriydi. 2026-07-18'de kök
dizinden buraya taşındı.

## Neden taşındı
Depo genelinde (CI workflow'ları, Python kaynak kodu, diğer script'ler,
dokümantasyon) tam bir referans taraması yapıldı — hiçbir dosyadan bu
script'lerin herhangi birine tek bir referans bulunamadı. `.github/workflows/`
altındaki iki CI dosyası (`backend-ci.yml`, `production-release.yml`) doğrudan
`pytest`/`alembic`/`ruff` çağırıyor, bu script'lerin hiçbirini kullanmıyor.

## Ne yapılmalı
- Yeni doğrulama işleri için buradaki script'leri kullanmayın/çoğaltmayın —
  güncel iş, `06-Roadmap/Faz-Planı.md`'deki `HARDEN-0xx`/`AUTH-0xx` numaralandırmasını
  ve WIKI_ROOT'taki gerçek-testle-doğrulama disiplinini takip ediyor.
- Tarihsel kayıt olarak korunuyorlar, silinmediler.
- Bazıları (`run_rc401_rc440_production_hardening_validation.ps1`,
  `run_rc441_rc450_authentication_core_validation.ps1` gibi) tematik olarak
  bu oturumun HARDEN-001/HARDEN-004 ve auth_core çalışmasıyla örtüşüyor ama
  kod tabanından çağrılmıyorlardı — güncel iş bunların üzerine inşa edilmedi,
  bağımsız olarak yeniden yapıldı.

Detay: `WIKI_ROOT/00-Overview/Platform-Durumu.md`.
