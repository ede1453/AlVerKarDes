# RC441–RC450 Authentication Core — Teknik Tasarım

## Amaç

Mevcut minimal register/login/me altyapısını bozmadan production düzeyinde
oturum ve token güvenliği eklemek.

## Güvenlik kararları

### Access token

JWT access token kısa ömürlüdür ve şu claim'leri zorunlu taşır:

- `sub`: kullanıcı
- `sid`: oturum
- `sv`: security version
- `jti`: benzersiz token kimliği
- `iss`: issuer
- `aud`: audience
- `iat`, `nbf`, `exp`
- `typ=access`

### Refresh token

Refresh token JWT değildir. Yüksek entropili opaque token'dır.

Veritabanında açık token tutulmaz:

```text
raw refresh token -> SHA-256 -> auth_tokens.token_hash
```

Her kullanımda rotate edilir. Kullanılmış bir token tekrar görülürse tüm token
ailesi iptal edilir ve session `COMPROMISED` olur.

### Session

Her cihaz/login için ayrı session kaydı tutulur. Kullanıcı:

- aktif oturumlarını görebilir,
- tek oturumu kapatabilir,
- tüm oturumları kapatabilir.

### Brute force

Başarısız giriş sayısı kalıcı veritabanı state'idir. Eşik aşılırsa hesap geçici
olarak kilitlenir.

### E-posta doğrulama ve parola sıfırlama

Tek kullanımlık opaque token kullanılır. Token açık halde tutulmaz, zaman aşımı
vardır ve tüketim atomik yapılır.

### Parola geçmişi

Son beş parola hash'i kontrol edilir. Parola sıfırlaması:

- security version artırır,
- tüm sessionları iptal eder,
- audit eventi üretir.

## Mevcut identity katmanına entegrasyon

Mevcut `/identity/login` endpointinde başarılı parola doğrulamasından sonra:

```python
pair = await auth_core_service.issue_token_pair(
    user_id=user.id,
    context=context,
)
```

çağrısı eklenmelidir.

Mevcut access-token üretimi kaldırılmadan önce response contract testleri
güncellenmeli; geçiş döneminde aynı response içine `refresh_token`,
`session_id`, `access_expires_at`, `refresh_expires_at` eklenebilir.

Başarısız login durumunda:

```python
await auth_core_service.record_failed_login(...)
```

Başarılı login öncesinde:

```python
await auth_core_service.check_login_allowed(user_id=user.id)
```

Başarılı login sonunda:

```python
await auth_core_service.record_successful_login(...)
```

kullanılmalıdır.
