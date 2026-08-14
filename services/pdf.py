"""Generation of the event ticket PDF."""

import os
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from db.pool import get_pool


_FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
_FONT_REGULAR = "TicketSans"
_FONT_BOLD = "TicketSansBold"
_fonts_ready = False


def _ensure_fonts() -> tuple[str, str]:
    """Register an embedded Cyrillic font, falling back to its bold face safely.

    The repository deliberately ships only DejaVuSans-Bold.ttf.  Registering that
    file for both faces is preferable to falling back to Helvetica, which cannot
    display Russian text and produces black squares in the generated ticket.
    """
    global _fonts_ready
    if _fonts_ready:
        return _FONT_REGULAR, _FONT_BOLD

    font_path = os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf")
    if not os.path.isfile(font_path):
        raise RuntimeError("Не найден шрифт для генерации PDF-билетов.")

    if _FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(_FONT_REGULAR, font_path))
    if _FONT_BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(_FONT_BOLD, font_path))
    _fonts_ready = True
    return _FONT_REGULAR, _FONT_BOLD


def format_ticket_number(number: int) -> str:
    """Format the sequential number as at least three digits, e.g. ``042``."""
    return f"{number:03d}"


async def next_ticket_number(event_id: int) -> int:
    """Atomically obtain the next number for an event."""
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE events SET last_ticket_no = last_ticket_no + 1 WHERE id = $1 RETURNING last_ticket_no",
        event_id,
    )
    return row["last_ticket_no"]


def _fit_text(text: str, font: str, size: float, max_width: float) -> str:
    """Keep a single line readable by trimming it with an ellipsis when needed."""
    text = str(text).strip()
    if stringWidth(text, font, size) <= max_width:
        return text
    ellipsis = "..."
    while text and stringWidth(text + ellipsis, font, size) > max_width:
        text = text[:-1]
    return text.rstrip() + ellipsis


def _draw_centered(c: canvas.Canvas, text: str, font: str, size: float,
                   y: float, page_width: float, max_width: float) -> None:
    text = _fit_text(text, font, size, max_width)
    c.setFont(font, size)
    c.drawCentredString(page_width / 2, y, text)


def generate_ticket_pdf(
    event_name: str,
    event_date: str,
    event_location: str,
    ticket_type_name: str,
    ticket_number: int,
    buyer_name: str,
    buyer_phone: str,
) -> bytes:
    """Generate a branded A6 ticket with clear event, owner and number details."""
    font_regular, font_bold = _ensure_fonts()
    # Сохраняем корректную подпись и для уже созданных баз, где ранее был
    # единственный тип «Обычный билет».
    if ticket_type_name == "Обычный билет":
        ticket_type_name = "Танцпол"
    page_width, page_height = A6
    padding = 12 * mm
    content_width = page_width - 2 * padding

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A6, pageCompression=1)
    c.setTitle(f"Билет {format_ticket_number(ticket_number)}")
    c.setAuthor("Kovcheg")

    # Dark neon base inspired by the landing page.
    c.setFillColor(HexColor("#0A0A0F"))
    c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    c.setFillColor(HexColor("#201034"))
    c.circle(page_width - 8 * mm, page_height - 13 * mm, 38 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#15152B"))
    c.circle(3 * mm, 46 * mm, 32 * mm, fill=1, stroke=0)

    c.setStrokeColor(HexColor("#FF2E9F"))
    c.setLineWidth(1.2)
    c.roundRect(7 * mm, 7 * mm, page_width - 14 * mm, page_height - 14 * mm, 5 * mm, stroke=1, fill=0)
    c.setStrokeColor(HexColor("#00E5FF"))
    c.setLineWidth(0.65)
    c.line(padding, page_height - 25 * mm, page_width - padding, page_height - 25 * mm)

    c.setFillColor(HexColor("#00E5FF"))
    c.setFont(font_bold, 7)
    c.drawString(padding, page_height - 18 * mm, "KOVCHEG / БИЛЕТ")
    c.setFillColor(HexColor("#F7F8FF"))
    c.setFont(font_bold, 7)
    c.drawRightString(page_width - padding, page_height - 18 * mm, "ДЛЯ 1 ВХОДА")

    y = page_height - 38 * mm
    c.setFillColor(HexColor("#F7F8FF"))
    _draw_centered(c, event_name, font_bold, 16, y, page_width, content_width)
    y -= 12 * mm
    c.setFillColor(HexColor("#C8C4D4"))
    _draw_centered(c, event_date, font_regular, 8.8, y, page_width, content_width)
    y -= 6.5 * mm
    _draw_centered(c, event_location, font_regular, 8.8, y, page_width, content_width)

    y -= 9 * mm
    c.setFillColor(HexColor("#00E5FF"))
    _draw_centered(c, ticket_type_name.upper(), font_bold, 8, y, page_width, content_width)
    y -= 9 * mm
    c.setFillColor(HexColor("#FF2E9F"))
    c.setFont(font_bold, 7.5)
    c.drawCentredString(page_width / 2, y, "БИЛЕТ НОМЕР")
    y -= 18 * mm
    c.setFillColor(HexColor("#F7F8FF"))
    c.setFont(font_bold, 47)
    c.drawCentredString(page_width / 2, y, format_ticket_number(ticket_number))
    c.setStrokeColor(HexColor("#7B2FFF"))
    c.setLineWidth(0.8)
    c.line(39 * mm, y - 4 * mm, page_width - 39 * mm, y - 4 * mm)

    owner_top = 49.5 * mm
    owner_height = 23 * mm
    c.setFillColor(HexColor("#121321"))
    c.roundRect(padding, owner_top - owner_height, content_width, owner_height, 3.5 * mm, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#4A3A66"))
    c.setLineWidth(0.5)
    c.roundRect(padding, owner_top - owner_height, content_width, owner_height, 3.5 * mm, fill=0, stroke=1)
    c.setFillColor(HexColor("#9C97AB"))
    c.setFont(font_bold, 6.7)
    c.drawString(padding + 5 * mm, owner_top - 7 * mm, "ВЛАДЕЛЕЦ И КОНТАКТ")
    c.setFillColor(HexColor("#F7F8FF"))
    owner_name = _fit_text(buyer_name, font_bold, 10.5, content_width - 10 * mm)
    c.setFont(font_bold, 10.5)
    c.drawString(padding + 5 * mm, owner_top - 14.5 * mm, owner_name)
    phone = _fit_text(buyer_phone, font_bold, 10.5, content_width - 10 * mm)
    c.setFont(font_bold, 10.5)
    c.drawString(padding + 5 * mm, owner_top - 21.5 * mm, phone)

    c.setFillColor(HexColor("#9C97AB"))
    c.setFont(font_regular, 6.7)
    c.drawCentredString(page_width / 2, 15 * mm, "СОХРАНИТЕ БИЛЕТ И ПРЕДЪЯВИТЕ НА ВХОДЕ")

    c.showPage()
    c.save()
    return buf.getvalue()
