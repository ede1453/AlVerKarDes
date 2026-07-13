# RC301–RC340 Production Launch Hotfix v1.3

## Logdan belirlenen hatalar

1. Alembic `postgresql+psycopg://` nedeniyle `psycopg` yüklemeye çalıştı.
   Projede kurulu driver `asyncpg` olduğundan URL:
   `postgresql+asyncpg://` olmalıdır.

2. Host portu `8000` başka bir servis tarafından kullanılıyordu.
   Production Compose artık varsayılan olarak `18000` kullanır.

3. PowerShell `$ErrorActionPreference = "Stop"` native Docker komutlarının
   başarısız exit code'larında tek başına durmaz. Yeni script her komuttan
   sonra `$LASTEXITCODE` kontrol eder.

4. Önceki smoke test port 8000'de çalışan eski servise bağlanarak sahte başarı
   üretti. Yeni smoke test yalnızca `.env.production` içindeki
   `AICI_API_PORT` portunu test eder ve production API container'ının gerçekten
   çalıştığını doğrular.

5. `docker compose down` artık `--env-file .env.production` ile çalışır;
   POSTGRES değişken uyarıları oluşmaz.

## `.env.production` zorunlu düzeltmeler

```env
DATABASE_URL=postgresql+asyncpg://aici:GERCEK_DB_PAROLASI@db:5432/aici
POSTGRES_PASSWORD=GERCEK_DB_PAROLASI
JWT_SECRET=EN_AZ_32_KARAKTERLIK_GUCLU_SECRET
CORS_ALLOWED_ORIGINS=http://localhost:3000
AICI_API_PORT=18000
```

`DATABASE_URL` içindeki parola ile `POSTGRES_PASSWORD` aynı olmalıdır.

## Çalıştırma

```powershell
powershell -ExecutionPolicy Bypass `
  -File .\scriptspply_production_hotfix.ps1
```

Script herhangi bir aşamada hata alırsa artık hemen durur; sonraki aşamaları
çalıştırmaz ve sahte başarı yazmaz.
