from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram.utils.exceptions import BotBlocked

from config.config import TELEGRAM_TOKEN
from config.states import Calendar, AdminPanel
from config.constants import *

from utils.api import get_schedule
from utils.database import Database

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = Database()


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    db.add_user(user_id=message.from_user.id, username=message.from_user.username)
    admins = db.get_admins()
    admin = db.check_admin(user_id=message.from_user.id)

    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Расписание", callback_data="calendar")
    keyboard.add(button)

    if not admins:
        db.add_admin(user_id=message.from_user.id, username=message.from_user.username)
    elif admin:
        button2 = types.InlineKeyboardButton(text="Панель Администратора", callback_data="admin_panel")
        keyboard.add(button2)
    await message.answer(text=start_message, reply_markup=keyboard)


@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer(text=help_message)


@dp.callback_query_handler(text="cancel", state='*')
async def cancel(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await call.message.edit_text(text="Отменено")


@dp.callback_query_handler(text="calendar")
async def calendar(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Понедельник", callback_data="monday")
    button2 = types.InlineKeyboardButton(text="Вторник", callback_data="tuesday")
    button3 = types.InlineKeyboardButton(text="Среда", callback_data="wednesday")
    button4 = types.InlineKeyboardButton(text="Четверг", callback_data="thursday")
    button5 = types.InlineKeyboardButton(text="Пятница", callback_data="friday")
    button6 = types.InlineKeyboardButton(text="Суббота", callback_data="saturday")
    button7 = types.InlineKeyboardButton(text="Воскресенье", callback_data="sunday")
    button8 = types.InlineKeyboardButton(text="❌", callback_data="cancel")
    week = [button1, button2, button3, button4, button5, button6, button7, button8]
    for day in week:
        keyboard.add(day)
    await call.message.edit_text(text=select_day, reply_markup=keyboard)
    await Calendar.day.set()


@dp.callback_query_handler(state=Calendar.day)
async def choose_anime(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(day=call.data)
    anime_list = await get_schedule(day=call.data)

    keyboard = types.InlineKeyboardMarkup()
    for item in anime_list:
        anime_name = item['title_ru']
        anime_id = item['id']
        button = types.InlineKeyboardButton(text=anime_name, callback_data=anime_id)
        keyboard.add(button)
    keyboard.add(types.InlineKeyboardButton(text="👈 Назад", callback_data="calendar"))

    await call.message.edit_text(text=select_anime, reply_markup=keyboard)
    await Calendar.next()


@dp.message_handler(lambda message: message.text not in ["monday", "tuesday", "wednesday", "thursday", "friday",
                                                         "saturday", "sunday"], state=Calendar.day)
async def process_calendar_invalid(message: types.Message):
    return await message.reply(text=invalid_day)


@dp.callback_query_handler(state=Calendar.anime)
async def get_anime(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'calendar':
        await state.finish()
        await calendar(call)
    else:
        await state.update_data(anime=call.data)
        get_state_data = await state.get_data()
        anime_list = await get_schedule(day=get_state_data['day'])
        anime_info = [item for item in anime_list if item['id'] == int(call.data)].pop()

        await call.message.edit_text(text=f"*{anime_info['title_ru']}*" + '\n' + '\n' +
                                          f"- *Оригинальное название*: {anime_info['title_original']}" + '\n' +
                                          f"- *Год*: {anime_info['year']}" + '\n' +
                                          f"- *Жанры*: {anime_info['genres']}" + '\n' +
                                          f"- *Рейтинг*: {str(anime_info['grade'])[:4]} из 5" + '\n' +
                                          f"- *Тип*: {anime_info['category']['name']}" + '\n' +
                                          f"- *Серий всего*: {anime_info['episodes_total']}" + '\n' +
                                          f"- *Серий вышло*: {anime_info['episodes_released']}" + '\n' + '\n' +
                                          "✨ Чтобы узнать о другом аниме, нажмите /start",
                                     parse_mode=ParseMode.MARKDOWN)
        await state.finish()


@dp.callback_query_handler(text="admin_panel")
async def admin_panel(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button1 = types.InlineKeyboardButton(text="Количество пользователей", callback_data="count_users")
    button2 = types.InlineKeyboardButton(text="Рассылка", callback_data="mailing")
    button3 = types.InlineKeyboardButton(text="Управление администраторами", callback_data="manage_admins")
    button4 = types.InlineKeyboardButton(text="❌", callback_data="cancel")
    keyboard.add(button1, button2, button3, button4)
    await call.message.edit_text(text=admin_text, reply_markup=keyboard)
    await AdminPanel.func.set()


@dp.callback_query_handler(text="count_users", state=AdminPanel.func)
async def count_users(call: types.CallbackQuery, state: FSMContext):
    users = len(db.get_users())
    await call.message.edit_text(text=f"Количество пользователей - {users}")
    await state.finish()


@dp.callback_query_handler(text="mailing", state=AdminPanel.func)
async def mailing(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="❌", callback_data="cancel")
    keyboard.add(button1)
    await call.message.edit_text(text=mailing_text, reply_markup=keyboard)
    await AdminPanel.mailing.set()


@dp.message_handler(state=AdminPanel.mailing)
async def check_message(message: types.Message, state: FSMContext):
    await state.update_data(check_message=message.text)
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Да", callback_data="yes")
    button2 = types.InlineKeyboardButton(text="Нет", callback_data="cancel")
    keyboard.add(button1, button2)
    await message.reply(text=check_message_text, reply_markup=keyboard)
    await AdminPanel.check_message.set()


@dp.callback_query_handler(state=AdminPanel.check_message)
async def start_mailing(call: types.CallbackQuery, state: FSMContext):
    get_state_data = await state.get_data()
    users = db.get_users()
    users_work = 0
    for user in users:
        user_id = user[1]
        try:
            users_work += 1
            await call.message.bot.send_message(chat_id=user_id, text=get_state_data['check_message'],
                                                parse_mode=ParseMode.MARKDOWN)
        except BotBlocked:
            pass
    await call.message.edit_text(text=f"Сообщение доставлено {users_work} пользователям ✅")
    await state.finish()


@dp.callback_query_handler(text="manage_admins", state=AdminPanel.func)
async def manage_admins(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="Посмотреть администраторов", callback_data="get_admins")
    button2 = types.InlineKeyboardButton(text="Добавить", callback_data="add_admin")
    button3 = types.InlineKeyboardButton(text="Удалить", callback_data="delete_admin")
    button4 = types.InlineKeyboardButton(text="❌", callback_data="cancel")
    keyboard.add(button1)
    keyboard.add(button2, button3)
    keyboard.add(button4)
    await call.message.edit_text(text=admin_text, reply_markup=keyboard)
    await AdminPanel.manage_admins.set()


@dp.callback_query_handler(text="get_admins", state=AdminPanel.manage_admins)
async def get_admins(call: types.CallbackQuery, state: FSMContext):
    admins = db.get_admins()
    message_text = "".join([f'ID: `{admin[1]}` | Username: `{admin[2]}`\n' for admin in admins])
    await call.message.edit_text(text=f"🔑 Список администраторов:" + '\n' + '\n' +
                                      f"{message_text}", parse_mode=ParseMode.MARKDOWN)
    await state.finish()


@dp.callback_query_handler(lambda call: call.data in ['add_admin', 'delete_admin'], state=AdminPanel.manage_admins)
async def send_admin_info(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="❌", callback_data="cancel")
    keyboard.add(button1)

    if call.data == 'add_admin':
        await call.message.edit_text(text=add_admin_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        await AdminPanel.add_admin.set()
    elif call.data == 'delete_admin':
        await call.message.edit_text(text=delete_admin_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        await AdminPanel.delete_admin.set()


@dp.message_handler(regexp=r"[0-9]+:\w+", state=AdminPanel.add_admin)
async def add_admin(message: types.Message, state: FSMContext):
    admin = message.text.split(':')
    user_id = admin[0]
    username = admin[1]
    db.add_admin(user_id=user_id, username=username)
    await message.reply(text=f"Пользователь {user_id} успешно добавлен ✅")
    await state.finish()


@dp.message_handler(lambda message: message.text.isdigit(), state=AdminPanel.delete_admin)
async def delete_admin(message: types.Message, state: FSMContext):
    user_id = int(message.text)
    db.delete_admin(user_id=user_id)
    await message.reply(text=f"Пользователь {user_id} успешно удалён ✅")
    await state.finish()


if __name__ == "__main__":
    db.check_database()
    executor.start_polling(dp, skip_updates=True)
