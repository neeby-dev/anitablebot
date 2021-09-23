from aiogram.dispatcher.filters.state import State, StatesGroup


class Calendar(StatesGroup):
    day = State()
    anime = State()


class AdminPanel(StatesGroup):
    func = State()
    mailing = State()
    check_message = State()
    manage_admins = State()
    get_admins = State()
    add_admin = State()
    delete_admin = State()
