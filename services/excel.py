# services/excel.py
from io import BytesIO

from openpyxl import Workbook

from services.pdf import format_ticket_number
from db.queries import get_export_rows

# Человекочитаемые статусы (в выгрузку попадают только confirmed)
_STATUS_RU = {
    "confirmed": "Оплачен",
}

_HEADERS = ["Имя", "Телефон", "Тип билета", "Статус оплаты", "Номер билета", "Отметка входа"]


async def build_export_xlsx() -> bytes:
    """
    Генерирует .xlsx (п.10): одна строка = один билет подтвержденного заказа.
    Последняя колонка «Отметка входа» — пустая, для ручных отметок контролера.
    """
    rows = await get_export_rows()

    wb = Workbook()
    ws = wb.active
    ws.title = "Билеты"

    ws.append(_HEADERS)

    for r in rows:
        ws.append([
            r["buyer_name"],
            r["buyer_phone"],
            r["ticket_type_name"],
            _STATUS_RU.get(r["status"], r["status"]),
            format_ticket_number(r["ticket_number"]),
            "",  # отметка входа — пустая колонка
        ])

    # простая ширина колонок
    widths = [22, 16, 18, 14, 14, 16]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()