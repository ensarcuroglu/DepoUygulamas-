"""Prompts used by the text PDF extraction pipeline."""

from __future__ import annotations

import json

SYSTEM_PROMPT = """\
Sen depo mal kabul belgelerinden irsaliye taslagi cikaran bir asistansin.
Sadece gecerli JSON dondur. Markdown, aciklama veya ek metin dondurme.

JSON semasi:
{
  "tedarikci": {"value": "string", "confidence": 0.0-1.0},
  "irsaliye_no": {"value": "string", "confidence": 0.0-1.0},
  "tarih": {"value": "YYYY-MM-DD", "confidence": 0.0-1.0},
  "kalemler": [
    {
      "urun_kodu": {"value": "string", "confidence": 0.0-1.0},
      "ad": {"value": "string", "confidence": 0.0-1.0},
      "miktar": {"value": number, "confidence": 0.0-1.0},
      "birim": {"value": "string", "confidence": 0.0-1.0}
    }
  ],
  "toplam": {"value": number, "confidence": 0.0-1.0}
}

Belgede alan yoksa tahmin uydurma; en dusuk guvenle bos/eksik bir alan yerine
belgede gorunen en yakin bilgiyi kullan. Tarihi ISO-8601 bicimine cevir.
"""

FEW_SHOT_EXAMPLES = [
    {
        "document_text": (
            "Tedarikci: ACME GIDA A.S.\n"
            "Irsaliye No: IRS-2026-0001\n"
            "Tarih: 11.05.2026\n"
            "URUN-001 Pirinc 10 KG\n"
            "Toplam: 10"
        ),
        "json": {
            "tedarikci": {"value": "ACME GIDA A.S.", "confidence": 0.95},
            "irsaliye_no": {"value": "IRS-2026-0001", "confidence": 0.94},
            "tarih": {"value": "2026-05-11", "confidence": 0.92},
            "kalemler": [
                {
                    "urun_kodu": {"value": "URUN-001", "confidence": 0.9},
                    "ad": {"value": "Pirinc", "confidence": 0.85},
                    "miktar": {"value": 10, "confidence": 0.9},
                    "birim": {"value": "KG", "confidence": 0.9},
                }
            ],
            "toplam": {"value": 10, "confidence": 0.88},
        },
    },
    {
        "document_text": (
            "TEDARIKCI BETA LOJISTIK\n"
            "Sevk No: SVK-77\n"
            "Belge Tarihi: 2026/05/10\n"
            "KOD-9 Strech Film 24 ADET"
        ),
        "json": {
            "tedarikci": {"value": "BETA LOJISTIK", "confidence": 0.88},
            "irsaliye_no": {"value": "SVK-77", "confidence": 0.8},
            "tarih": {"value": "2026-05-10", "confidence": 0.83},
            "kalemler": [
                {
                    "urun_kodu": {"value": "KOD-9", "confidence": 0.82},
                    "ad": {"value": "Strech Film", "confidence": 0.78},
                    "miktar": {"value": 24, "confidence": 0.84},
                    "birim": {"value": "ADET", "confidence": 0.86},
                }
            ],
            "toplam": {"value": 24, "confidence": 0.7},
        },
    },
    {
        "document_text": (
            "Gamma Ambalaj San. Tic. Ltd. Sti.\n"
            "Irsaliye: G-2026-45 Tarih 09-05-2026\n"
            "AMB-10 Koli 120 Adet\n"
            "AMB-11 Palet Strech 5 Rulo"
        ),
        "json": {
            "tedarikci": {
                "value": "Gamma Ambalaj San. Tic. Ltd. Sti.",
                "confidence": 0.9,
            },
            "irsaliye_no": {"value": "G-2026-45", "confidence": 0.86},
            "tarih": {"value": "2026-05-09", "confidence": 0.85},
            "kalemler": [
                {
                    "urun_kodu": {"value": "AMB-10", "confidence": 0.85},
                    "ad": {"value": "Koli", "confidence": 0.82},
                    "miktar": {"value": 120, "confidence": 0.88},
                    "birim": {"value": "Adet", "confidence": 0.84},
                },
                {
                    "urun_kodu": {"value": "AMB-11", "confidence": 0.85},
                    "ad": {"value": "Palet Strech", "confidence": 0.8},
                    "miktar": {"value": 5, "confidence": 0.86},
                    "birim": {"value": "Rulo", "confidence": 0.84},
                },
            ],
            "toplam": {"value": 125, "confidence": 0.68},
        },
    },
]


def build_irsaliye_text_prompt(document_text: str) -> str:
    examples = json.dumps(FEW_SHOT_EXAMPLES, ensure_ascii=False, indent=2)
    return f"""\
Asagidaki ornekleri referans al:
{examples}

Simdi bu irsaliye metnini ayni JSON semasina donustur:
---
{document_text}
---
"""
