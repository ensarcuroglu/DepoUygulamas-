"""Render PDFs and image uploads into a VLM-ready base64 image."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO

from app.core.entities.belge import Belge, BelgeTipi


class ImageRenderingError(RuntimeError):
    """Raised when a document cannot be rendered as an image."""


@dataclass(frozen=True)
class RenderedImage:
    image_base64: str
    mime_type: str
    width: int
    height: int
    page_index: int | None = None


class ImageRenderer:
    def __init__(self, pdf_dpi: int = 180, image_format: str = "JPEG") -> None:
        self.pdf_dpi = pdf_dpi
        self.image_format = image_format.upper()

    def render(self, belge: Belge, belge_tipi: BelgeTipi) -> RenderedImage:
        if belge_tipi is BelgeTipi.SCANNED_PDF:
            image = self._render_pdf_first_page(belge.content)
            return self._to_rendered_image(image, page_index=0)
        if belge_tipi is BelgeTipi.IMAGE:
            image = self._load_image(belge.content)
            return self._to_rendered_image(image, page_index=None)
        raise ImageRenderingError(f"Gorsel render desteklenmeyen belge tipi: {belge_tipi.value}")

    def _render_pdf_first_page(self, content: bytes):
        try:
            import pypdfium2 as pdfium
        except ImportError as exc:
            raise ImageRenderingError("pypdfium2 kurulu degil") from exc

        try:
            pdf = pdfium.PdfDocument(content)
            if len(pdf) == 0:
                raise ImageRenderingError("PDF sayfa icermiyor")
            page = pdf[0]
            bitmap = page.render(scale=self.pdf_dpi / 72)
            image = bitmap.to_pil()
            return image.convert("RGB")
        except ImageRenderingError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ImageRenderingError("PDF sayfasi gorsel olarak render edilemedi") from exc

    @staticmethod
    def _load_image(content: bytes):
        try:
            from PIL import Image
        except ImportError as exc:
            raise ImageRenderingError("Pillow kurulu degil") from exc

        try:
            with Image.open(BytesIO(content)) as image:
                return image.convert("RGB")
        except Exception as exc:  # noqa: BLE001
            raise ImageRenderingError("Gorsel dosyasi okunamadi") from exc

    def _to_rendered_image(self, image, page_index: int | None) -> RenderedImage:
        buffer = BytesIO()
        image.save(buffer, format=self.image_format, quality=90)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        mime_type = "image/jpeg" if self.image_format == "JPEG" else "image/png"
        return RenderedImage(
            image_base64=image_base64,
            mime_type=mime_type,
            width=image.width,
            height=image.height,
            page_index=page_index,
        )
