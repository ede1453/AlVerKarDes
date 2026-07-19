# Authentication Core Threat Model

## Korunan varlıklar

- kullanıcı hesapları
- refresh token aileleri
- session kimlikleri
- parola hash'leri
- audit kayıtları
- e-posta doğrulama ve reset tokenları

## Tehditler ve karşılıklar

| Tehdit | Kontrol |
|---|---|
| Refresh token veritabanından çalınması | Yalnızca SHA-256 hash saklama |
| Çalınmış refresh token tekrar kullanımı | Rotation ve family revocation |
| Brute-force login | Kalıcı attempt sayacı ve geçici lockout |
| JWT başka serviste kullanılması | Issuer ve audience doğrulaması |
| Eski JWT parola değişiminden sonra kullanılması | Security version |
| Reset token tekrar kullanımı | Atomik consumed_at |
| Kullanıcının başka sessionı kapatması | Session ownership kontrolü |
| Hesap enumeration | Reset issue endpointi her durumda aynı cevap |
| Parola tekrar kullanımı | Password history |
| Güvenlik olaylarının izsiz kalması | Auth audit event tablosu |
