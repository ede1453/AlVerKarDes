# ARŞİV — KULLANMA

Bu klasördeki her şey, kod tabanı genelinde tam referans taraması yapıldıktan
sonra (CI, Python, script'ler, dokümantasyon, script-script) hiçbir yerden
kullanılmadığı doğrulanan, ama tarihsel kayıt olarak silinmeyen dosyalardır.
Yeni iş için buraya bakmayın/yeniden kullanmayın.

## Alt klasörler
- `rc-scripts/` — 151 eski `run_rcXX_*.ps1` doğrulama script'i (RC1-614 serisi).
- `release-manifests/` — eski release/hotfix/RC batch manifest JSON'ları
  (`FINAL_RELEASE_MANIFEST.json`, `HOTFIX_MANIFEST.json`,
  `PACKAGE_MANIFEST.json`, `RC301_RC340_MANIFEST.json`).
- `env-backups/` — kullanılmayan, referanssız `.env.*` yedek dosyaları
  (`.env.production--` — zayıf/placeholder değerler içeriyordu, sadece kod
  tabanı üzerinde bırakılmış eski bir yedek, hiçbir yerden yüklenmiyordu).
- `misc/` — sınıflandırılamayan tekil dosyalar (`openapi.json` — kök dizinde
  duran dosya gerçek bir OpenAPI şeması değildi, bir PowerShell
  `Invoke-WebRequest` yanıtının ham/bozuk çıktısıydı — `StatusCode`/
  `Content` alanlarıyla; hiçbir kod bunu okumuyordu, güncel şema her zaman
  canlı `/openapi.json` endpoint'inden alınmalı).
- `dead-code/` — CONNECT-003'te (2026-07-19) arşivlenen `app/domains/` alt-paketleri:
  - `product_canonicalization/` — gerçek ingestion zincirinden (`app/domains/products/normalization`)
    bağımsız, kendi marka listesi + farklı `canonical_key` formatı üreten standalone bir
    kanonikleştirme motoruydu. Tek çağıranı `shopping_pipeline` (disconnected demo pipeline)
    artık gerçek `app/domains/products/canonical_service.CanonicalProductService.canonicalize()`
    kullanıyor. `/api/v1/product-canonicalization/*` endpoint'leri hâlâ canlı, artık gerçek
    motorla besleniyor (`app/api/v1/product_canonicalization_router.py`).
  - `product_matching/` — gerçek ingestion zincirinden (`app/domains/products/matching_engine`)
    bağımsız, ilk-4-token'a göre gruplandıran kaba bir eşleştirme motoruydu. Tek çağıranı
    `ai_shopping_agent` (disconnected demo pipeline) artık gerçek
    `app/domains/products/matching_engine.ProductMatchEngine.match()` kullanıyor.
    `/api/v1/product-matching/*` endpoint'leri hâlâ canlı, artık gerçek motorla besleniyor.
  - Referans taraması (`grep -rl "app\.domains\.product_(canonicalization|matching)" app/`)
    taşımadan önce sıfır kalan çağıran doğruladı. Detay: `WIKI_ROOT/05-Decisions/ADR-007-Faz3-Envanteri-CONNECT-000.md`
    (CONNECT-002/CONNECT-003 Sonuç Raporu).

Detay: `WIKI_ROOT/00-Overview/Platform-Durumu.md` (kök dizin envanteri).
