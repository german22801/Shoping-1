import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import json

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
GROUP_CHAT_ID = -1002557567873

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

CITIES = ["Мурманск", "Апатиты", "Кировск"]

class AdminState(StatesGroup):
    login = State()
    password = State()
    city = State()
    name = State()
    price = State()
    desc = State()

admin_logged_in = {}

def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for city in CITIES:
        markup.add(KeyboardButton(city))
    await message.answer("Выберите город:", reply_markup=markup)

@dp.message_handler(lambda msg: msg.text in CITIES)
async def show_products(message: types.Message):
    products = load_products()
    city = message.text
    if city not in products or not products[city]:
        await message.answer("В этом городе пока нет товаров.")
        return
    for product in products[city]:
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Заказать", callback_data=f"order:{city}:{product['name']}"))
        await message.answer(f"📦 <b>{product['name']}</b>
💰 {product['price']}₽
📝 {product['desc']}", parse_mode="HTML", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("order:"))
async def order_handler(callback: types.CallbackQuery):
    _, city, name = callback.data.split(":")
    await bot.send_message(GROUP_CHAT_ID, f"🛒 Новый заказ:
Город: {city}
Товар: {name}
Пользователь: @{callback.from_user.username or callback.from_user.id}")
    await callback.answer("Заказ отправлен!")

# --- Админка ---
@dp.message_handler(commands=['admin'])
async def admin_cmd(message: types.Message):
    await message.answer("Введите логин:")
    await AdminState.login.set()

@dp.message_handler(state=AdminState.login)
async def admin_login(message: types.Message, state: FSMContext):
    if message.text == "admin":
        await state.update_data(login=message.text)
        await message.answer("Введите пароль:")
        await AdminState.password.set()
    else:
        await message.answer("Неверный логин.")

@dp.message_handler(state=AdminState.password)
async def admin_password(message: types.Message, state: FSMContext):
    if message.text == "program1029":
        admin_logged_in[message.from_user.id] = True
        await message.answer("Добро пожаловать в админку!
Напиши город, куда добавить товар:")
        await AdminState.city.set()
    else:
        await message.answer("Неверный пароль.")
        await state.finish()

@dp.message_handler(state=AdminState.city)
async def admin_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Введите название товара:")
    await AdminState.name.set()

@dp.message_handler(state=AdminState.name)
async def admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите цену:")
    await AdminState.price.set()

@dp.message_handler(state=AdminState.price)
async def admin_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Введите описание:")
    await AdminState.desc.set()

@dp.message_handler(state=AdminState.desc)
async def admin_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    products = load_products()
    city = data['city']
    new_item = {
        "name": data['name'],
        "price": data['price'],
        "desc": message.text
    }
    if city not in products:
        products[city] = []
    products[city].append(new_item)
    save_products(products)
    await message.answer("Товар добавлен!")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)