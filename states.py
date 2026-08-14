# states.py
from aiogram.fsm.state import State, StatesGroup


class PurchaseStates(StatesGroup):
    choosing_type = State()
    entering_quantity = State()
    entering_name = State()
    entering_phone = State()
    waiting_screenshot = State()


class RejectStates(StatesGroup):
    waiting_reason = State()


class BroadcastStates(StatesGroup):
    waiting_text = State()
    confirming = State()


class AskQuestionStates(StatesGroup):
    waiting_question = State()