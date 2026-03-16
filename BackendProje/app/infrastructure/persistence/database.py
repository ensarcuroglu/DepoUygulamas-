"""
Geriye donuk uyumluluk wrapper'i.

Asil database konfigurasyonu BackendProje/database.py'dedir.
Bu dosya, Clean Architecture modullerinde eski import yollarinin
kirilmamasini saglar.
"""

from database import engine, SessionLocal, Base, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]
