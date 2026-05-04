"""Project root'u sys.path'e ekleyerek ml_models paketini import edilebilir kilar.

ml_models klasoru proje kokunde (BackendProje ile sibling). uvicorn/pytest
BackendProje icinden calistirildigi icin parent dizin sys.path'e eklenmelidir.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
