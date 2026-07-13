# RC301–RC340 Production Launch Hotfix v1.2

## Düzeltilen gerçek hatalar

### 1. JWT environment değişkeni

Projenin `app/core/config.py` dosyası:

```text
JWT_SECRET
```

bekliyor. Önceki paket yanlışlıkla:

```text
JWT_SECRET_KEY
```

kullanıyordu.

`.env.production` içinde şu satır bulunmalı:

```env
JWT_SECRET=EN_AZ_32_KARAKTERLIK_RASTGELE_BIR_SECRET
```

Eski `JWT_SECRET_KEY` satırı silinmeli.

### 2. Yerel smoke test

Aşağıdaki komut geçersizdir:

```powershell
python .\scripts\production_smoke_test.py https://YOUR_DOMAIN
```

`YOUR_DOMAIN` gerçek DNS adı değildir.

Domain ve TLS hazırlanmadan önce:

```powershell
python .\scripts\production_smoke_test.py http://127.0.0.1:8000
```

kullanılmalıdır.

### 3. Nginx/TLS başlangıç sırası

Nginx artık `edge` profiline alındı. Sertifikalar hazır değilken normal
`docker compose up -d` komutuyla başlamaz.

Gerçek domain ve sertifika hazır olduğunda:

```powershell
docker compose `
  --env-file .\.env.production `
  -f .\deploy\docker\docker-compose.production.yml `
  --profile edge up -d
```

### 4. Compose proje adı

Compose projesi:

```yaml
name: aici-production
```

olarak sabitlendi. Bu, ilgisiz containerların orphan olarak algılanması riskini
azaltır.

## Tek komutla uygulama

Dosyaları proje köküne kopyaladıktan ve `.env.production` içindeki secretları
düzelttikten sonra:

```powershell
powershell -ExecutionPolicy Bypass `
  -File .\scriptspply_production_hotfix.ps1
```
