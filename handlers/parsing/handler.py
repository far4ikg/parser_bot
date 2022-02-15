from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from dotenv.main import load_dotenv
from os import getenv

from keyboards.reply.main_menu import menu_reply_kb
from keyboards.inline.parsing import first_marks_list_ikb, second_marks_list_ikb, parse_ikb, update_db_ikb
from parsing.database.db_functions import get_products_db
from parsing.parse import create_parse_db, start_parse


class FsmBot(StatesGroup):
    mark_auto = State()


stop_parsing = bool


async def call_main_menu(msg: Message):
    await msg.reply(text="Держи главное меню", reply_markup=menu_reply_kb)


async def close_main_menu(msg: Message):
    await msg.answer(text="Я закрыл главное меню", reply_markup=ReplyKeyboardRemove())


async def set_parse_mode(msg: Message):
    await msg.answer(text="Выбери метод", reply_markup=parse_ikb)


async def change_parse_mode_marks(call: CallbackQuery, state_group=FsmBot):
    global stop_parsing
    if not stop_parsing:
        stop_parsing = True
        await call.bot.send_message(chat_id=call.message.chat.id, text="Остановка парсинга...")
    await state_group.mark_auto.set()
    await call.bot.send_message(chat_id=call.message.chat.id, text="1-ой список", reply_markup=first_marks_list_ikb())
    await call.bot.send_message(chat_id=call.message.chat.id, text="2-ой список", reply_markup=second_marks_list_ikb())
    await call.answer(text="Выбирай марку", show_alert=True)


async def parse_mode_marks(call: CallbackQuery, state: FSMContext):
    global stop_parsing
    load_dotenv()
    search_attr = getenv(key='PAGE')
    if call.data == "-1":
        stop_parsing = False
        await state.finish()
        await state.storage.close()
        await call.answer(text="Выбор сделан")
        await create_parse_db(search_attr=search_attr, call=call, break_parse=stop_parsing)
        while not stop_parsing:
            await start_parse(search_attr=search_attr, call=call, break_parse=stop_parsing)
        await call.bot.send_message(chat_id=call.from_user.id, text="Парсинг остановлен")
    elif call.data == "-2":
        stop_parsing = False
        for i in await state.get_data():
            search_attr += f"{getenv(key='MARK') + i + '&'}"
        search_attr = search_attr[:-1]
        await state.finish()
        await state.storage.close()
        await call.answer(text="Выбор сделан")
        await create_parse_db(search_attr=search_attr, call=call, break_parse=stop_parsing)
        while not stop_parsing:
            await start_parse(search_attr=search_attr, call=call, break_parse=stop_parsing)
        await call.bot.send_message(chat_id=call.from_user.id, text="Парсинг остановлен")
    elif call.data == "-3":
        if not stop_parsing:
            stop_parsing = True
            await call.bot.send_message(chat_id=call.message.chat.id, text="Остановка парсинга...")
        await state.finish()
        await state.storage.close()
        await call.answer(text="Парсинг отменен")
    else:
        async with state.proxy() as data:
            data[f"{int(call.data)}"] = int(call.data)
        await call.answer(text="Выбор сделан\n\"Отменить\" - отменить процесс")


async def parse_mode_models(call: CallbackQuery):
    await call.bot.send_message(chat_id=call.message.chat.id, text="Выбери марку", reply_markup=first_marks_list_ikb())
    await call.answer(text="Выбирай марку", show_alert=True)


async def stop_parse(msg: Message):
    global stop_parsing
    await msg.answer(text="Остановка парсинга...")
    stop_parsing = True


async def update_products_db(msg: Message):
    await msg.answer(text="Обновить БД?", reply_markup=update_db_ikb)


async def confirm_update_products_db(call: CallbackQuery):
    load_dotenv()
    if call.from_user.id == int(getenv(key="OWNER_ID")):
        await call.answer()
        await get_products_db(call=call)
    else:
        await call.answer(text="Обновлять БД может только мой хозяин...")
