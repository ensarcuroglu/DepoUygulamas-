"""
Rate Limiter — Merkezi Yapılandırma
main.py'den ayrıştırıldı; circular import sorununu önler.
Her router bu modülden import eder.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
