from aiogram.fsm.state import StatesGroup, State

class InputPasswordState(StatesGroup):
    password = State()

class InputUrlState(StatesGroup):
    name = State()
    url = State()
    
class InputNewUser(StatesGroup):
    new_name = State()
    new_url = State()
