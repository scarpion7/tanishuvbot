import asyncio
import os
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from urllib.parse import urlparse
from dotenv import load_dotenv
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8000))
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))  # Bot admin ID from .env

# Yangi usulda botni yaratish
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# Dispatcher yaratish
dp = Dispatcher(storage=MemoryStorage())


# --- FSM (Finite State Machine) states ---
class Form(StatesGroup):
    language = State()
    country = State()
    region = State()
    city = State()
    gender = State()
    looking_for_type = State()
    partner_gender = State()
    partner_age = State()
    partner_info = State()
    characteristics = State()
    about_me = State()
    contact_option = State()
    phone_number = State()
    username = State()
    photo = State()
    publish_consent = State()
    confirm = State()
    admin_reply = State()   # Admin javob yozishi uchun holat


# --- TEXTS (Matnlar) ---
TEXTS = {
    "uz": {
        "start": "Assalomu alaykum! Sherik topish botiga xush kelibsiz. Iltimos, tilni tanlang:",
        "choose_language": "Iltimos, tilni tanlang:",
        "country": "Qaysi davlatdansiz?",
        "region": "Qaysi viloyatdansiz?",
        "city": "Qaysi shahardansiz?",
        "gender": "Jinsingizni tanlang:",
        "male": "Erkak 👨",
        "female": "Ayol 👩",
        "looking_for_type": "Kimni qidiryapsiz?",
        "for_marriage": "Oilam uchun 💍",
        "for_friendship": "Do'stlik uchun 🤝",
        "partner_gender": "Qidirayotgan sherigingiz qaysi jinsdan bo'lishi kerak?",
        "partner_age": "Qidirayotgan sherigingiz necha yoshda bo'lishi kerak? (Masalan: 25-30)",
        "partner_info": "Sherikingiz haqida qo'shimcha ma'lumot bering (kamida 50 belgi):",
        "characteristics": "O'zingiz haqingizda bir nechta xususiyatlarni yozing (kamida 50 belgi):",
        "about_me": "O'zingiz haqingizda to'liq ma'lumot bering (kamida 100 belgi):",
        "contact_option": "Siz bilan qanday bog'lanish mumkin?",
        "share_phone": "Telefon raqamini ulashish 📞",
        "share_username": "Username (Foydalanuvchi nomi) 👤",
        "photo": "O'zingizning aniq rasmingizni yuboring (yoki 'Skip' tugmasini bosing):",
        "skip_photo": "O'tkazish ➡️",
        "confirm_prompt": "Barcha ma'lumotlar to'g'rimi? Davom etish uchun 'Tasdiqlash' tugmasini bosing.",
        "confirm_button": "Tasdiqlash ✅",
        "edit_button": "Tahrirlash ✍️",
        "publish_consent": "Arizangizni kanalimizga joylashtirishimizga rozimisiz?",
        "yes": "Ha, roziman 👍",
        "no": "Yo'q, rad etaman 👎",
        "thank_you": "Arizangiz uchun rahmat! Ma'lumotlaringiz kanalga joylashtirildi. Tez orada javob kutishingiz mumkin.",
        "profile_template": (
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n"
            "<b>🚻 Jinsi:</b> {gender}\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n"
            "<b>🔢 Qidirayotgan yoshi:</b> {partner_age}\n"
            "<b>✨ Sherik haqida ma'lumot:</b> {partner_info}\n"
            "<b>📝 O'zi haqida xususiyatlari:</b> {characteristics}\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n"
            "<b>📞 Bog'lanish:</b> {contact}\n"
            "<b>Bot manbasi:</b> @{bot_username}"
        ),
        "invalid_input": "Noto'g'ri kiritish. Iltimos, qaytadan urinib ko'ring.",
        "too_short": "Kiritilgan matn juda qisqa. Iltimos, kamida {} belgi kiriting.",
        "back_button": "⬅️ Orqaga",
        "admin_notification_prompt": "Yangi ariza keldi: ",
        "admin_reply_button": "✉️ Foydalanuvchiga javob berish",
        "admin_enter_reply_text": "Foydalanuvchiga yubormoqchi bo'lgan javobingizni kiriting:",
        "admin_reply_sent": "Foydalanuvchiga javobingiz yuborildi.",
        "admin_no_active_user_for_reply": "Javob berish uchun faol foydalanuvchi topilmadi. Iltimos, arizaga javob tugmasi orqali javob bering."
    },
    "ru": {
        "start": "Здравствуйте! Добро пожаловать в бот для поиска партнеров. Пожалуйста, выберите язык:",
        "choose_language": "Пожалуйста, выберите язык:",
        "country": "Из какой вы страны?",
        "region": "Из какой вы области?",
        "city": "Из какого вы города?",
        "gender": "Выберите ваш пол:",
        "male": "Мужской 👨",
        "female": "Женский 👩",
        "looking_for_type": "Кого вы ищете?",
        "for_marriage": "Для брака 💍",
        "for_friendship": "Для дружбы 🤝",
        "partner_gender": "Какого пола должен быть ваш партнер?",
        "partner_age": "Сколько лет должно быть вашему партнеру? (Например: 25-30)",
        "partner_info": "Предоставьте дополнительную информацию о вашем партнере (минимум 50 символов):",
        "characteristics": "Напишите несколько ваших характеристик (минимум 50 символов):",
        "about_me": "Расскажите о себе (минимум 100 символов):",
        "contact_option": "Как с вами можно связаться?",
        "share_phone": "Поделиться номером телефона 📞",
        "share_username": "Имя пользователя 👤",
        "photo": "Отправьте ваше четкое фото (или нажмите 'Пропустить'):",
        "skip_photo": "Пропустить ➡️",
        "confirm_prompt": "Все данные верны? Нажмите 'Подтвердить' для продолжения.",
        "confirm_button": "Подтвердить ✅",
        "edit_button": "Редактировать ✍️",
        "publish_consent": "Вы согласны разместить вашу заявку в нашем канале?",
        "yes": "Да, согласен 👍",
        "no": "Нет, не согласен 👎",
        "thank_you": "Спасибо за вашу заявку! Ваша информация была размещена в канале. Вскоре вы можете ожидать ответа.",
        "profile_template": (
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n"
            "<b>🚻 Пол:</b> {gender}\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n"
            "<b>✨ Информация о партнере:</b> {partner_info}\n"
            "<b>📝 Характеристики о себе:</b> {characteristics}\n"
            "<b>✍️ О себе:</b> {about_me}\n"
            "<b>📞 Контакт:</b> {contact}\n"
            "<b>Источник бота:</b> @{bot_username}"
        ),
        "invalid_input": "Неверный ввод. Пожалуйста, попробуйте еще раз.",
        "too_short": "Введенный текст слишком короткий. Пожалуйста, введите не менее {} символов.",
        "back_button": "⬅️ Назад",
        "admin_notification_prompt": "Новая заявка: ",
        "admin_reply_button": "✉️ Ответить пользователю",
        "admin_enter_reply_text": "Введите текст ответа, который вы хотите отправить пользователю:",
        "admin_reply_sent": "Ваш ответ отправлен пользователю.",
        "admin_no_active_user_for_reply": "Не удалось найти активного пользователя для ответа. Пожалуйста, отвечайте через кнопку ответа на заявку."
    }
}

DEFAULT_PHOTO_URLS = {
    "male": "https://i.ibb.co/L95jN4p/default-male.jpg",
    "female": "https://i.ibb.co/VMy4v27/default-female.jpg",
    "default": "https://i.ibb.co/tZ5nB6k/default-user.jpg"
}


# --- Keyboards (Klaviaturalar) ---
def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_gender_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["male"], callback_data="gender_male")],
        [InlineKeyboardButton(text=TEXTS[lang]["female"], callback_data="gender_female")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_looking_for_type_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["for_marriage"], callback_data="looking_marriage")],
        [InlineKeyboardButton(text=TEXTS[lang]["for_friendship"], callback_data="looking_friendship")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_partner_gender_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["male"], callback_data="partner_gender_male")],
        [InlineKeyboardButton(text=TEXTS[lang]["female"], callback_data="partner_gender_female")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_contact_option_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["share_phone"], callback_data="contact_phone_number")],
        [InlineKeyboardButton(text=TEXTS[lang]["share_username"], callback_data="contact_username")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_photo_skip_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["skip_photo"], callback_data="skip_photo_")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["confirm_button"], callback_data="confirm_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["edit_button"], callback_data="confirm_edit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_publish_consent_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["yes"], callback_data="consent_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["no"], callback_data="consent_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_reply_keyboard(lang: str, user_id: int):
    """Admin uchun foydalanuvchiga javob berish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["admin_reply_button"], callback_data=f"admin_reply_to_user_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- Handlers (Ishlovchilar) ---
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.language)
    await message.answer(TEXTS["uz"]["start"], reply_markup=get_language_keyboard())

@dp.callback_query(Form.language, F.data.startswith("lang_"))
async def process_language(callback_query: CallbackQuery, state: FSMContext) -> None:
    lang = callback_query.data.removeprefix("lang_")
    await state.update_data(lang=lang)
    await state.set_state(Form.country)
    await callback_query.message.edit_text(TEXTS[lang]["country"])
    await callback_query.answer()

@dp.message(Form.country)
async def process_country(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(country=message.text)
    await state.set_state(Form.region)
    await message.answer(TEXTS[lang]["region"])

@dp.message(Form.region)
async def process_region(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(region=message.text)
    await state.set_state(Form.city)
    await message.answer(TEXTS[lang]["city"])

@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(city=message.text)
    await state.set_state(Form.gender)
    await message.answer(TEXTS[lang]["gender"], reply_markup=get_gender_keyboard(lang))

@dp.callback_query(Form.gender, F.data.startswith("gender_"))
async def process_gender(callback_query: CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    gender = callback_query.data.removeprefix("gender_")
    gender_text = TEXTS[lang]["male"] if gender == "male" else TEXTS[lang]["female"]
    await state.update_data(gender=gender_text, gender_key=gender)
    await state.set_state(Form.looking_for_type)
    await callback_query.message.edit_text(TEXTS[lang]["looking_for_type"], reply_markup=get_looking_for_type_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.looking_for_type, F.data.startswith("looking_"))
async def process_looking_for_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_type = callback_query.data.removeprefix("looking_")
    looking_text = TEXTS[lang]["for_marriage"] if looking_type == "marriage" else TEXTS[lang]["for_friendship"]
    await state.update_data(looking_for_type=looking_text)
    await state.set_state(Form.partner_gender)
    await callback_query.message.edit_text(TEXTS[lang]["partner_gender"], reply_markup=get_partner_gender_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.partner_gender, F.data.startswith("partner_gender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_gender = callback_query.data.removeprefix("partner_gender_")
    partner_gender_text = TEXTS[lang]["male"] if partner_gender == "male" else TEXTS[lang]["female"]
    await state.update_data(partner_gender=partner_gender_text)
    await state.set_state(Form.partner_age)
    await callback_query.message.edit_text(TEXTS[lang]["partner_age"])
    await callback_query.answer()

@dp.message(Form.partner_age)
async def process_partner_age(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(partner_age=message.text)
    await state.set_state(Form.partner_info)
    await message.answer(TEXTS[lang]["partner_info"])

@dp.message(Form.partner_info)
async def process_partner_info(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if len(message.text) < 50:
        await message.answer(TEXTS[lang]["too_short"].format(50))
        return
    await state.update_data(partner_info=message.text)
    await state.set_state(Form.characteristics)
    await message.answer(TEXTS[lang]["characteristics"])

@dp.message(Form.characteristics)
async def process_characteristics(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if len(message.text) < 50:
        await message.answer(TEXTS[lang]["too_short"].format(50))
        return
    await state.update_data(characteristics=message.text)
    await state.set_state(Form.about_me)
    await message.answer(TEXTS[lang]["about_me"])

@dp.message(Form.about_me)
async def process_about_me(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if len(message.text) < 100:
        await message.answer(TEXTS[lang]["too_short"].format(100))
        return
    await state.update_data(about_me=message.text)
    await state.set_state(Form.contact_option)
    await message.answer(TEXTS[lang]["contact_option"], reply_markup=get_contact_option_keyboard(lang))

@dp.callback_query(Form.contact_option, F.data.startswith("contact_"))
async def process_contact_option(callback_query: CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    contact_option = callback_query.data.removeprefix("contact_")

    if contact_option == "phone_number":
        await state.set_state(Form.phone_number)
        await callback_query.message.edit_text("Iltimos, telefon raqamingizni yuboring (Masalan: +998901234567):")
    elif contact_option == "username":
        await state.set_state(Form.username)
        await callback_query.message.edit_text("Iltimos, Telegram username'ingizni yuboring (Masalan: @your_username):")
    await callback_query.answer()

@dp.message(Form.phone_number)
async def process_phone_number(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(phone_number=message.text)
    await state.set_state(Form.photo)
    await message.answer(TEXTS[lang]["photo"], reply_markup=get_photo_skip_keyboard(lang))

@dp.message(Form.username)
async def process_username(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(username=message.text)
    await state.set_state(Form.photo)
    await message.answer(TEXTS[lang]["photo"], reply_markup=get_photo_skip_keyboard(lang))

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(Form.publish_consent)
    await message.answer(TEXTS[lang]["publish_consent"], reply_markup=get_publish_consent_keyboard(lang))

@dp.callback_query(Form.photo, F.data == "skip_photo_")
async def skip_photo(callback_query: CallbackQuery, state: FSMContext) -> None:
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(photo_id=None)  # Rasmsiz
    await state.set_state(Form.publish_consent)
    await callback_query.message.edit_text(TEXTS[lang]["publish_consent"], reply_markup=get_publish_consent_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(Form.publish_consent, F.data.startswith("consent_"))
async def process_publish_consent(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    consent = callback_query.data.removeprefix("consent_")

    if consent == "yes":
        user_id = callback_query.from_user.id
        full_name = callback_query.from_user.full_name
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # Kontakt ma'lumotini shakllantirish
        contact_info = ""
        if user_data.get("phone_number") and user_data.get("username"):
            contact_info = f"📞 {user_data['phone_number']}, @{user_data['username']}"
        elif user_data.get("phone_number"):
            contact_info = f"📞 {user_data['phone_number']}"
        elif user_data.get("username"):
            contact_info = f"@{user_data['username']}"

        # Kanal uchun profil matnini shakllantirish
        profile_text_for_channel = TEXTS[lang]["profile_template"].format(
            country=user_data.get("country", "N/A"),
            region=user_data.get("region", "N/A"),
            city=user_data.get("city", "N/A"),
            gender=user_data.get("gender", "N/A"),
            looking_for_type=user_data.get("looking_for_type", "N/A"),
            partner_gender=user_data.get("partner_gender", "N/A"),
            partner_age=user_data.get("partner_age", "N/A"),
            partner_info=user_data.get("partner_info", "N/A"),
            characteristics=user_data.get("characteristics", "N/A"),
            about_me=user_data.get("about_me", "N/A"),
            contact=contact_info,
            bot_username=bot_username
        )

        photo_id = user_data.get("photo_id")
        if photo_id:
            try:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=profile_text_for_channel)
            except Exception as e:
                print(f"Error sending photo to channel: {e}")
                await bot.send_message(chat_id=CHANNEL_ID, text=profile_text_for_channel)
        else:
            gender_key = user_data.get("gender_key", "default")
            default_photo_url = DEFAULT_PHOTO_URLS.get(gender_key, DEFAULT_PHOTO_URLS["default"])
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(default_photo_url) as resp:
                        if resp.status == 200:
                            photo_content = await resp.read()
                            await bot.send_photo(chat_id=CHANNEL_ID, photo=types.BufferedInputFile(photo_content, filename='photo.jpg'), caption=profile_text_for_channel)
                        else:
                            print(f"Failed to fetch default photo from {default_photo_url}, status: {resp.status}")
                            await bot.send_message(chat_id=CHANNEL_ID, text=profile_text_for_channel)
            except Exception as e:
                print(f"Error sending default photo or fetching it: {e}")
                await bot.send_message(chat_id=CHANNEL_ID, text=profile_text_for_channel)

        await callback_query.message.edit_text(TEXTS[lang]["thank_you"])

        # Admin uchun ma'lumotni yuborish
        user_profile_link = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
        admin_notification_text = (
            f"{TEXTS[lang]['admin_notification_prompt']}{user_profile_link}\n"
            f"<b>📍 Joylashuv:</b> {user_data.get('country', 'N/A')}, {user_data.get('region', 'N/A')}, {user_data.get('city', 'N/A')}\n"
            f"<b>🚻 Jinsi:</b> {user_data.get('gender', 'N/A')}\n"
            f"<b>🔍 Maqsadi:</b> {user_data.get('looking_for_type', 'N/A')}\n"
            f"<b>👫 Qidirayotgan jinsi:</b> {user_data.get('partner_gender', 'N/A')}\n"
            f"<b>🔢 Qidirayotgan yoshi:</b> {user_data.get('partner_age', 'N/A')}\n"
            f"<b>✨ Sherik haqida ma'lumot:</b> {user_data.get('partner_info', 'N/A')}\n"
            f"<b>📝 O'zi haqida xususiyatlari:</b> {user_data.get('characteristics', 'N/A')}\n"
            f"<b>✍️ O'zi haqida:</b> {user_data.get('about_me', 'N/A')}\n"
            f"<b>📞 Bog'lanish:</b> {contact_info}\n"
        )
        
        if photo_id:
            try:
                await bot.send_photo(
                    chat_id=BOT_ADMIN_ID,
                    photo=photo_id,
                    caption=admin_notification_text,
                    reply_markup=get_admin_reply_keyboard(lang, user_id)
                )
            except Exception as e:
                print(f"Error sending photo to admin: {e}")
                await bot.send_message(
                    chat_id=BOT_ADMIN_ID,
                    text=admin_notification_text,
                    reply_markup=get_admin_reply_keyboard(lang, user_id)
                )
        else:
            gender_key = user_data.get("gender_key", "default")
            default_photo_url = DEFAULT_PHOTO_URLS.get(gender_key, DEFAULT_PHOTO_URLS["default"])
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(default_photo_url) as resp:
                        if resp.status == 200:
                            photo_content = await resp.read()
                            await bot.send_photo(
                                chat_id=BOT_ADMIN_ID,
                                photo=types.BufferedInputFile(photo_content, filename='photo.jpg'),
                                caption=admin_notification_text,
                                reply_markup=get_admin_reply_keyboard(lang, user_id)
                            )
                        else:
                            print(f"Failed to fetch default photo for admin from {default_photo_url}, status: {resp.status}")
                            await bot.send_message(
                                chat_id=BOT_ADMIN_ID,
                                text=admin_notification_text,
                                reply_markup=get_admin_reply_keyboard(lang, user_id)
                            )
            except Exception as e:
                print(f"Error sending default photo to admin or fetching it: {e}")
                await bot.send_message(
                    chat_id=BOT_ADMIN_ID,
                    text=admin_notification_text,
                    reply_markup=get_admin_reply_keyboard(lang, user_id)
                )

    else: # consent == "no"
        await callback_query.message.edit_text("Arizangiz joylanishi rad etildi. Botdan foydalanishni qaytadan boshlashingiz mumkin.", reply_markup=get_language_keyboard())

    await state.clear() # Foydalanuvchining state'ini tozalash
    await callback_query.answer()


@dp.callback_query(F.data.startswith("admin_reply_to_user_") and F.from_user.id == BOT_ADMIN_ID)
async def admin_start_reply(callback_query: CallbackQuery, state: FSMContext):
    """Admin 'Foydalanuvchiga javob berish' tugmasini bosganda"""
    user_id_to_reply = int(callback_query.data.split("_")[4]) # admin_reply_to_user_USER_ID
    
    # Adminning tilini aniqlash
    admin_state_data = await state.get_data()
    lang = admin_state_data.get("lang", "uz") # Admin uchun tilni saqlash
    
    await state.update_data(reply_to_user_id=user_id_to_reply)
    await state.set_state(Form.admin_reply)
    await callback_query.message.edit_text(TEXTS[lang]["admin_enter_reply_text"])
    await callback_query.answer()

@dp.message(Form.admin_reply, F.from_user.id == BOT_ADMIN_ID)
async def process_admin_reply(message: Message, state: FSMContext):
    """Admin javob matnini kiritganda"""
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    reply_text = message.text
    user_id_to_reply = user_data.get("reply_to_user_id")

    if user_id_to_reply and reply_text:
        try:
            await bot.send_message(chat_id=user_id_to_reply, text=f"Admin javobi:\n\n{reply_text}")
            await message.answer(TEXTS[lang]["admin_reply_sent"])
        except Exception as e:
            print(f"Error sending admin reply to user {user_id_to_reply}: {e}")
            await message.answer("Xatolik yuz berdi. Javob yuborilmadi.")
    else:
        await message.answer(TEXTS[lang]["admin_no_active_user_for_reply"])

    await state.clear() # Admin state'ini tozalash


async def main() -> None:
    if WEBHOOK_URL:
        app = web.Application()
        parsed_url = urlparse(WEBHOOK_URL)
        webhook_path_for_handler = parsed_url.path if parsed_url.path else "/"

        webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_requests_handler.register(app, path=webhook_path_for_handler)
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEB_SERVER_HOST, WEB_SERVER_PORT)
        await site.start()

        print(f"Webhook URL: {WEBHOOK_URL}")
        await bot.set_webhook(WEBHOOK_URL)
        print("Bot started and listening via webhook...")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
            await bot.session.close()
            await dp.storage.close()
            print("Bot stopped and resources released.")

    else:
        print("Bot started and listening via polling...")
        try:
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
            await dp.storage.close()
            print("Bot stopped and resources released.")


if __name__ == "__main__":
    asyncio.run(main())
