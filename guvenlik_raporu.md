✅ Önerilen Güvenlik Geliştirmeleri

1. Rate Limiting (Acil)
# slowapi veya @fastapi/security
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)
@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request): ...

2. JWT Refresh Token
# Mevcut: tek token (8 saat)
# Önerilen: Access + Refresh token
- Access Token: 15-30 dk
- Refresh Token: 7-30 gün

3. İki Faktörlü Kimlik Doğrulama (2FA)
# TOTP (Time-based One-Time Password)
import pyotp
# Google Authenticator uyumlu

4. Şifre Güvenlik Politikası
# Minimum 8 karakter, büyük/küçük harf, rakam, özel karakter
import re
def validate_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*]", password)
    )

5. Gelişmiş Audit Logging
Özellik
Login/Logout takibi
Şifre değişikliği
Yetki değişikliği
Kritik veri erişimi

6. Request Security
# Request body size limit
app.add_middleware(
    Middleware,
    max_body_size=1024 * 1024  # 1MB
)
# IP Whitelist (opsiyonel)
ALLOWED_IPS = ["192.168.1.0/24", "10.0.0.0/8"]

7. Veritabanı Güvenliği
- SSL/TLS zorunlu
- Bağlantı havuzu (connection pooling) güvenli yapılandırma
- ROW-level security (ileri düzey)
---