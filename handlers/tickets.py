# handlers/tickets.py
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile

import texts
from db.queries import get_event, get_user_tickets, set_ticket_pdf
from services.pdf import generate_ticket_pdf, format_ticket_number

router = Router()


@router.message(F.text == texts.BTN_MY_TICKETS)
async def my_tickets(message: Message):
    tickets = await get_user_tickets(message.from_user.id)

    if not tickets:
        await message.answer(texts.NO_TICKETS)
        return

    event = await get_event()
    await message.answer(texts.CLIENT_TICKETS_HEADER.format(count=len(tickets)))

    for t in tickets:
        num_str = format_ticket_number(t["ticket_number"])
        caption = texts.ticket_caption(event["name"], num_str, t["buyer_name"])

        # 1) пробуем переотправить по сохраненному file_id
        if t["pdf_file_id"]:
            try:
                await message.answer_document(t["pdf_file_id"], caption=caption)
                continue
            except Exception:
                # file_id инвалидирован — уходим в fallback-перегенерацию
                pass

        # 2) fallback: перегенерируем PDF по данным из БД
        pdf_bytes = generate_ticket_pdf(
            event_name=event["name"],
            event_date=event["date"],
            event_location=event["location"],
            ticket_type_name=t["ticket_type_name"],
            ticket_number=t["ticket_number"],
            buyer_name=t["buyer_name"],
            buyer_phone=t["buyer_phone"],
        )
        doc = BufferedInputFile(pdf_bytes, filename=f"ticket_{num_str}.pdf")
        try:
            sent = await message.answer_document(doc, caption=caption)
            # обновляем свежий file_id в БД
            if sent.document:
                await set_ticket_pdf(t["ticket_id"], sent.document.file_id)
        except Exception:
            # клиент недоступен — молча пропускаем, данные билета в БД
            pass
