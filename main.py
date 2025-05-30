import asyncio
import os
import random
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

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8000))

# Yangi usulda botni yaratish
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# --- FSM (Finite State Machine) states ---
class Form(StatesGroup):
    language = State()
    gender = State()
    country = State()
    region = State()
    custom_region = State()
    city = State()
    custom_city = State()
    # Removed: age, height, weight from initial form, they will be part of characteristics or partner_age
    looking_for_type = State() # This will be "Munosabat"
    partner_gender = State()
    partner_age = State() # NEW
    characteristics = State() # NEW for "xususiyatlari"
    about_me = State()
    contact = State()
    photo_upload = State() # NEW
    channel_check = State() # NEW
    publish_consent = State() # NEW
    confirm = State()
    
TEXTS = {
    "uz": {
        "start": "Salom! Botdan foydalanish uchun tilingizni tanlang:",
        "choose_language": "Iltimos, tilingizni tanlang:",
        "language_selected": "Til o'zbek tiliga o'rnatildi.",
        "gender_prompt": "Jinsingizni tanlang:",
        "country_prompt": "Davlatingizni tanlang:",
        "region_prompt": "Viloyatingizni tanlang yoki kiriting:",
        "custom_region_prompt": "Iltimos, viloyatingiz nomini kiriting:",
        "city_prompt": "Shahringizni tanlang yoki kiriting:",
        "custom_city_prompt": "Iltimos, shahringiz nomini kiriting:",
        "looking_for_prompt": "Nima maqsadda tanishmoqchisiz?",
        "partner_gender_prompt": "Kim bilan tanishmoqchisiz (sherikning jinsi)?",
        "partner_age_prompt": "Qidirayotgan sherigingizning yoshini kiriting (masalan, 25-35):",
        "characteristics_prompt": "O'zingizning yoshingiz, bo'yingiz (sm), og'irligingiz (kg) va boshqa xususiyatlaringizni kiriting (masalan: Yoshi: 25, Bo'yi: 170sm, Og'irligi: 65kg, Sportchi):",
        "about_me_prompt": "O'zingiz haqida ma'lumot kiriting (250 belgidan oshmasin):",
        "contact_prompt": "Bog'lanish uchun manzilingizni kiriting (Telegram username, telefon raqam, Instagram linki va hokazo):",
        "photo_upload_prompt": "Iltimos, profilingiz uchun rasm yuklang (yuzingiz aniq ko'rinishi shart):",
        "channel_check_prompt": "Arizangizni kanalga joylashdan oldin, iltimos, bizning kanalimizga a'zo bo'ling:",
        "channel_button_text": "Kanalga a'zo bo'lish",
        "not_a_member": "Siz kanalga a'zo emassiz. Iltimos, kanalga a'zo bo'lib, 'Tekshirish' tugmasini bosing.",
        "publish_consent_prompt": "Ma'lumotlaringizni kanalga chop etishimizga rozimisiz?",
        "confirm_prompt": "Ma'lumotlaringiz to'g'rimi? Davom etish uchun 'Tasdiqlash' tugmasini bosing.",
        "thank_you": "Arizangiz qabul qilindi. Tez orada kanalga joylashtiriladi.",
        "profile_template": (
            "<b>🙋‍♂️ Ism:</b> {full_name}\n"
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n"
            "<b>🚻 Jinsi:</b> {gender}\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n"
            "<b>🔢 Qidirayotgan yoshi:</b> {partner_age}\n"
            "<b>📝 O'zi haqida xususiyatlari:</b> {characteristics}\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n"
            "<b>📞 Bog'lanish:</b> {contact}\n"
            "<a href='{photo_url}'>Rasm</a>\n"
            "<a href='https://t.me/example'>Manba: TopTanish</a>"
        ),
        "invalid_input": "Noto'g'ri kiritish. Iltimos, to'g'ri formatda kiriting.",
        "invalid_age_format": "Yoshingizni to'g'ri formatda kiriting (masalan, 25-35).",
        "invalid_characteristics": "Iltimos, xususiyatlaringizni to'g'ri formatda kiriting. Namuna: Yoshi: 25, Bo'yi: 170sm, Og'irligi: 65kg, Sportchi",
        "invalid_callback_input": "Noto'g'ri tanlov. Iltimos, inline tugma orqali tanlang.",
        "select_from_options": "Iltimos, berilgan variantlardan birini tanlang.",
        "text_too_long": "Matn juda uzun. Iltimos, 250 belgidan oshirmang.",
        "other": "Boshqa" # YANGI QO'SHILDI
    },
    "ru": {
        "start": "Привет! Выберите ваш язык для использования бота:",
        "choose_language": "Пожалуйста, выберите ваш язык:",
        "language_selected": "Язык установлен на русский.",
        "gender_prompt": "Выберите ваш пол:",
        "country_prompt": "Выберите вашу страну:",
        "region_prompt": "Выберите или введите ваш регион:",
        "custom_region_prompt": "Пожалуйста, введите название вашего региона:",
        "city_prompt": "Выберите или введите ваш город:",
        "custom_city_prompt": "Пожалуйста, введите название вашего города:",
        "looking_for_prompt": "С какой целью вы хотите познакомиться?",
        "partner_gender_prompt": "С кем вы хотите познакомиться (пол партнера)?",
        "partner_age_prompt": "Введите возраст партнера, которого вы ищете (например, 25-35):",
        "characteristics_prompt": "Введите свой возраст, рост (см), вес (кг) и другие характеристики (например: Возраст: 25, Рост: 170см, Вес: 65кг, Спортсмен):",
        "about_me_prompt": "Введите информацию о себе (не более 250 символов):",
        "contact_prompt": "Введите ваш контакт (имя пользователя Telegram, номер телефона, ссылка на Instagram и т.д.):",
        "photo_upload_prompt": "Пожалуйста, загрузите фото для вашего профиля (лицо должно быть хорошо видно):",
        "channel_check_prompt": "Перед публикацией вашей заявки на канале, пожалуйста, подпишитесь на наш канал:",
        "channel_button_text": "Подписаться на канал",
        "not_a_member": "Вы не подписаны на канал. Пожалуйста, подпишитесь на канал и нажмите кнопку 'Проверить'.",
        "publish_consent_prompt": "Вы согласны на публикацию ваших данных на канале?",
        "confirm_prompt": "Ваши данные верны? Нажмите 'Подтвердить' для продолжения.",
        "thank_you": "Ваша заявка принята. Скоро она будет размещена на канале.",
        "profile_template": (
            "<b>🙋‍♂️ Имя:</b> {full_name}\n"
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n"
            "<b>🚻 Пол:</b> {gender}\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n"
            "<b>📝 О себе (характеристики):</b> {characteristics}\n"
            "<b>✍️ О себе:</b> {about_me}\n"
            "<b>📞 Контакт:</b> {contact}\n"
            "<a href='{photo_url}'>Фото</a>\n"
            "<a href='https://t.me/example'>Источник: TopTanish</a>"
        ),
        "invalid_input": "Неверный ввод. Пожалуйста, введите в правильном формате.",
        "invalid_age_format": "Введите возраст в правильном формате (например, 25-35).",
        "invalid_characteristics": "Пожалуйста, введите ваши характеристики в правильном формате. Пример: Возраст: 25, Рост: 170см, Вес: 65кг, Спортсмен",
        "invalid_callback_input": "Неверный выбор. Пожалуйста, выберите с помощью встроенной кнопки.",
        "select_from_options": "Пожалуйста, выберите один из предложенных вариантов.",
        "text_too_long": "Текст слишком длинный. Пожалуйста, не превышайте 250 символов.",
        "other": "Другое" # YANGI QO'SHILDI
    }
}

GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "family": {"uz": "Oila 👨‍👩‍👧‍👦", "ru": "Семья 👨‍👩‍👧‍👦"} # Added Family
}

LOOKING_FOR_OPTIONS = {
    "intimate_18": {"uz": "Intim munosabat 18+", "ru": "Интимные отношения 18+"}, # Modified key and text
    "friendship": {"uz": "Do'stlik", "ru": "Дружба"},
    "marriage": {"uz": "Nikoh", "ru": "Брак"},
    "pleasant_chat": {"uz": "Yoqimli suhbat", "ru": "Приятное общение"}, # New
    "no_preference": {"uz": "Farqi yo'q", "ru": "Неважно"} # Modified from "dating" or "any"
}

PARTNER_GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "family": {"uz": "Oila 👨‍👩‍👧‍👦", "ru": "Семья 👨‍👩‍👧‍👦"}, # Added Family
    "any": {"uz": "Farqi yo'q", "ru": "Неважно"} # Keep "any" for flexibility if not intim
}

# Qolgan kod o'zgarishsiz qoladi

COUNTRIES = {
    "uz": "O'zbekiston",
    "ru": "Rossiya",
    "kz": "Qozog'iston",
    "kg": "Qirg'iziston",
    "tj": "Tojikiston",
    "tm": "Turkmaniston",
    "other": "Boshqa"
}

REGIONS_UZ = [
    "Andijon", "Buxoro", "Farg'ona", "Jizzax", "Xorazm", "Namangan",
    "Navoiy", "Qashqadaryo", "Samarqand", "Sirdaryo", "Surxondaryo",
    "Toshkent viloyati", "Toshkent shahri", "Qoraqalpog'iston Respublikasi"
]

CITIES_UZ = {
    "Toshkent shahri": ["Toshkent"],
    "Toshkent viloyati": ["Angren", "Bekobod", "Chirchiq", "G'azalkent", "Keles", "Olmaliq", "Ohangaron", "Parkent", "Piskent", "Yangiobod", "Yangiyo'l", "Qibray", "Nurafshon"],
    "Andijon": ["Andijon", "Asaka", "Xonobod", "Shahrixon"],
    "Buxoro": ["Buxoro", "G'ijduvon", "Kogon"],
    "Farg'ona": ["Farg'ona", "Marg'ilon", "Qo'qon", "Quva", "Quvasoy"],
    "Jizzax": ["Jizzax", "Gagarin", "Do'stlik"],
    "Xorazm": ["Urganch", "Xiva"],
    "Namangan": ["Namangan", "Chust", "Pop"],
    "Navoiy": ["Navoiy", "Zarafshon", "Nurota"],
    "Qashqadaryo": ["Qarshi", "Kitob", "Shahrisabz", "G'uzor"],
    "Samarqand": ["Samarqand", "Kattaqo'rg'on", "Urgut"],
    "Sirdaryo": ["Guliston", "Yangiyer", "Shirnix", "Sirdaryo"],
    "Surxondaryo": ["Termiz", "Denov", "Boysun"],
    "Qoraqalpog'iston Respublikasi": ["Nukus", "Beruniy", "Chimboy", "To'rtko'l", "Xo'jayli", "Qo'ng'irot"]
}

# --- Dispatcher and Memory Storage ---
dp = Dispatcher(storage=MemoryStorage())

# --- Inline Keyboards ---
def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🇺🇿 O'zbek Tili", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский Язык", callback_data="lang_ru")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_gender_keyboard(lang: str):
    keyboard = []
    for key, value in GENDER_OPTIONS.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"gender_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_country_keyboard(lang: str):
    keyboard = []
    for key, value in COUNTRIES.items():
        keyboard.append([InlineKeyboardButton(text=value, callback_data=f"country_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_region_keyboard(lang: str):
    keyboard = []
    regions = REGIONS_UZ if lang == "uz" else ["Moscow", "Saint Petersburg", "Other (enter manually)"] # Example for RU
    for region in regions:
        keyboard.append([InlineKeyboardButton(text=region, callback_data=f"region_{region}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="region_other")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_city_keyboard(lang: str, region: str):
    keyboard = []
    cities = CITIES_UZ.get(region, []) if lang == "uz" else [] # Add RU cities if needed
    for city in cities:
        keyboard.append([InlineKeyboardButton(text=city, callback_data=f"city_{city}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="city_other")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_looking_for_keyboard(lang: str):
    keyboard = []
    for key, value in LOOKING_FOR_OPTIONS.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"looking_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_partner_gender_keyboard(lang: str, looking_for_type: str = None):
    keyboard = []
    if looking_for_type == "intimate_18":
        # If "Intim munosabat 18+" was chosen, only show Male, Female, Family
        options = {k: v for k, v in PARTNER_GENDER_OPTIONS.items() if k in ["male", "female", "family"]}
    else:
        # Otherwise, show all options including "Farqi yo'q"
        options = PARTNER_GENDER_OPTIONS
    
    for key, value in options.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"partner_gender_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_channel_check_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["channel_button_text"], url=f"https://t.me/your_channel_username")], # REPLACE with your channel link
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_channel_member")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_publish_consent_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ Roziman", callback_data="consent_yes")],
        [InlineKeyboardButton(text="❌ Rad etaman", callback_data="consent_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["confirm_prompt"], callback_data="confirm_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="confirm_no")] # Use "Other" for "No" or "Edit"
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# --- Handlers ---
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.language)
    await message.answer(TEXTS["uz"]["start"], reply_markup=get_language_keyboard())

@dp.callback_query(Form.language, F.data.startswith("lang_"))
async def process_language(callback_query: CallbackQuery, state: FSMContext):
    lang = callback_query.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(Form.gender)
    await callback_query.message.edit_text(TEXTS[lang]["language_selected"])
    await callback_query.message.answer(TEXTS[lang]["gender_prompt"], reply_markup=get_gender_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.gender, F.data.startswith("gender_"))
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    gender = callback_query.data.split("_")[1]
    if gender in GENDER_OPTIONS:
        await state.update_data(gender=GENDER_OPTIONS[gender][lang])
        await state.set_state(Form.country)
        await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_country_keyboard(lang))
    else:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_gender_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.country, F.data.startswith("country_"))
async def process_country(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = callback_query.data.split("_")[1]
    
    selected_country_text = COUNTRIES.get(country_key, country_key) 
    
    await state.update_data(country=selected_country_text)

    if country_key == "other":
        await state.set_state(Form.custom_region) 
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.set_state(Form.region)
        await callback_query.message.edit_text(TEXTS[lang]["region_prompt"], reply_markup=get_region_keyboard(lang))
    
    await callback_query.answer()


@dp.callback_query(Form.region, F.data.startswith("region_"))
async def process_region(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    region = callback_query.data.split("_")[1]
    if region == "other":
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.update_data(region=region)
        await state.set_state(Form.city)
        await callback_query.message.edit_text(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, region))
    await callback_query.answer()

@dp.message(Form.custom_region)
async def process_custom_region(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        await state.update_data(region=message.text)
        await state.set_state(Form.city)
        await message.answer(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, message.text))
    else:
        await message.answer(TEXTS[lang]["invalid_input"])

@dp.callback_query(Form.city, F.data.startswith("city_"))
async def process_city(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    city = callback_query.data.split("_")[1]
    if city == "other":
        await state.set_state(Form.custom_city)
        await callback_query.message.edit_text(TEXTS[lang]["custom_city_prompt"])
    else:
        await state.update_data(city=city)
        await state.set_state(Form.looking_for_type) # Changed flow here
        await callback_query.message.edit_text(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()

@dp.message(Form.custom_city)
async def process_custom_city(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        await state.update_data(city=message.text)
        await state.set_state(Form.looking_for_type) # Changed flow here
        await message.answer(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["invalid_input"])

@dp.callback_query(Form.looking_for_type, F.data.startswith("looking_"))
async def process_looking_for(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_for_key = callback_query.data.split("_")[1]

    # DEBUG: Qaysi kalit qabul qilinayotganini ko'rish
    print(f"DEBUG: Qabul qilingan 'looking_for_key': {looking_for_key} foydalanuvchi {callback_query.from_user.id} uchun")
    print(f"DEBUG: callback_data to'lig'icha: {callback_query.data}")


    if looking_for_key in LOOKING_FOR_OPTIONS:
        print(f"DEBUG: '{looking_for_key}' LOOKING_FOR_OPTIONS ichida topildi.")
        await state.update_data(looking_for_type_key=looking_for_key) # Shartli mantiq uchun kalitni saqlaymiz
        await state.update_data(looking_for_type=LOOKING_FOR_OPTIONS[looking_for_key][lang])

        # Keyingi holatga o'tish
        await state.set_state(Form.partner_gender)
        await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang, looking_for_key))
    else:
        # DEBUG: Nima uchun topilmaganini ko'rish
        print(f"DEBUG: '{looking_for_key}' LOOKING_FOR_OPTIONS ichida topilmadi. Qayta urinish.")
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.partner_gender, F.data.startswith("partner_gender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_gender_key = callback_query.data.split("_")[2] # Adjusted split index

    # Check if the chosen partner_gender_key is valid
    if partner_gender_key not in PARTNER_GENDER_OPTIONS:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_partner_gender_keyboard(lang))
        await callback_query.answer()
        return

    # Special handling for "family" option only if "intimate_18" was chosen previously
    if user_data.get("looking_for_type_key") == "intimate_18" and partner_gender_key not in ["male", "female", "family"]:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_partner_gender_keyboard(lang, "intimate_18"))
        await callback_query.answer()
        return

    await state.update_data(partner_gender=PARTNER_GENDER_OPTIONS[partner_gender_key][lang])
    await state.set_state(Form.partner_age) # NEW state transition
    await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    await callback_query.answer()

@dp.message(StateFilter(Form.partner_age))
async def process_partner_age(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    # Basic validation for age range (e.g., "20-30" or "30+")
    if message.text and (len(message.text.split('-')) == 2 and all(p.isdigit() for p in message.text.split('-')) or message.text.endswith('+') and message.text[:-1].isdigit()):
        await state.update_data(partner_age=message.text)
        await state.set_state(Form.characteristics) # NEW state transition
        await message.answer(TEXTS[lang]["characteristics_prompt"])
    else:
        await message.answer(TEXTS[lang]["invalid_age_format"])

@dp.message(StateFilter(Form.characteristics))
async def process_characteristics(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        # You might want to add more robust validation here for characteristics
        # For now, just check length
        if len(message.text) <= 250: # Assuming characteristics also have length limit
            await state.update_data(characteristics=message.text)
            await state.set_state(Form.about_me) # Transition to existing about_me
            await message.answer(TEXTS[lang]["about_me_prompt"])
        else:
            await message.answer(TEXTS[lang]["text_too_long"]) # Reuse text too long
    else:
        await message.answer(TEXTS[lang]["invalid_characteristics"])


@dp.message(StateFilter(Form.about_me))
async def process_about_me(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and len(message.text) <= 250:
        await state.update_data(about_me=message.text)
        await state.set_state(Form.contact)
        await message.answer(TEXTS[lang]["contact_prompt"])
    else:
        await message.answer(TEXTS[lang]["text_too_long"])

@dp.message(StateFilter(Form.contact))
async def process_contact(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        await state.update_data(contact=message.text)
        await state.set_state(Form.photo_upload) # NEW state transition
        await message.answer(TEXTS[lang]["photo_upload_prompt"])
    else:
        await message.answer(TEXTS[lang]["invalid_input"])

@dp.message(StateFilter(Form.photo_upload), F.photo)
async def process_photo_upload(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    
    # Get the file ID of the largest photo
    photo_file_id = message.photo[-1].file_id
    
    # You can get the file path or download it here if needed for permanent storage
    # For now, we'll store the file_id and later get its URL for the channel post
    await state.update_data(photo_file_id=photo_file_id)

    await state.set_state(Form.channel_check) # NEW state transition
    await message.answer(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))

@dp.message(StateFilter(Form.photo_upload)) # Handle non-photo input in photo state
async def handle_invalid_photo_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["photo_upload_prompt"]) # Re-prompt for photo

@dp.callback_query(Form.channel_check, F.data == "check_channel_member")
async def check_channel_membership(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")

    user_status = await bot.get_chat_member(CHANNEL_ID, callback_query.from_user.id)
    if user_status.status in ["member", "administrator", "creator"]:
        await state.set_state(Form.publish_consent) # NEW state transition
        await callback_query.message.edit_text(TEXTS[lang]["publish_consent_prompt"], reply_markup=get_publish_consent_keyboard(lang))
    else:
        await callback_query.message.edit_text(TEXTS[lang]["not_a_member"], reply_markup=get_channel_check_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(Form.publish_consent, F.data.startswith("consent_"))
async def request_publish_consent(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    consent = callback_query.data.split("_")[1]

    if consent == "yes":
        # Get full name from user's message object
        full_name = callback_query.from_user.full_name if callback_query.from_user else "Noma'lum"
        await state.update_data(full_name=full_name) # Save full name to state

        # Display confirmation
        final_data = await state.get_data()
        
        # Get photo URL
        photo_file_id = final_data.get("photo_file_id")
        photo_url = "https://t.me/example" # Default or placeholder
        if photo_file_id:
            try:
                # You need to get a direct file URL for the photo to display it in channel
                # This requires either:
                # 1. Downloading the file and serving it yourself (complex)
                # 2. Using bot.get_file to get file_path and then construct Telegram file URL (limited time)
                # For simplicity, let's assume a placeholder for now, or use a method that returns a persistent URL.
                # A common approach is to upload to a public image hosting or just send the photo directly to the channel.
                # If you need a persistent URL, you'll need to implement file download and hosting.
                # For basic use, file_id can be used by Telegram clients to display the photo directly when sent.
                # For the template, we need a URL. For demonstration, we'll use a placeholder.
                # In a real scenario, you'd send the photo directly to the channel in process_confirm_yes
                # and then optionally send the text message separately, or caption the photo.
                
                # For now, let's make a dummy link or leave it blank if no direct URL is generated
                # file_info = await bot.get_file(photo_file_id)
                # photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
                photo_url = "https://example.com/your_photo_link.jpg" # Placeholder or actual URL after processing
                
            except Exception as e:
                print(f"Error getting photo URL: {e}")
                photo_url = "https://t.me/example" # Fallback

        profile_text = TEXTS[lang]["profile_template"].format(
            full_name=final_data.get("full_name", "Noma'lum"),
            country=final_data.get("country", "Noma'lum"),
            region=final_data.get("region", "Noma'lum"),
            city=final_data.get("city", "Noma'lum"),
            gender=final_data.get("gender", "Noma'lum"),
            looking_for_type=final_data.get("looking_for_type", "Noma'lum"),
            partner_gender=final_data.get("partner_gender", "Noma'lum"),
            partner_age=final_data.get("partner_age", "Noma'lum"),
            characteristics=final_data.get("characteristics", "Noma'lum"),
            about_me=final_data.get("about_me", "Noma'lum"),
            contact=final_data.get("contact", "Noma'lum"),
            photo_url=photo_url # Pass photo URL to template
        )
        await callback_query.message.edit_text(profile_text, reply_markup=get_confirm_keyboard(lang))
        await state.set_state(Form.confirm)

    elif consent == "no":
        await state.clear() # Clear state and restart
        await callback_query.message.edit_text(TEXTS[lang]["start"], reply_markup=get_language_keyboard())
    await callback_query.answer()


@dp.callback_query(Form.confirm, F.data == "confirm_yes")
async def process_confirm_yes(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")

    # Construct the final profile message
    profile_text = TEXTS[lang]["profile_template"].format(
        full_name=user_data.get("full_name", "Noma'lum"),
        country=user_data.get("country", "Noma'lum"),
        region=user_data.get("region", "Noma'lum"),
        city=user_data.get("city", "Noma'lum"),
        gender=user_data.get("gender", "Noma'lum"),
        looking_for_type=user_data.get("looking_for_type", "Noma'lum"),
        partner_gender=user_data.get("partner_gender", "Noma'lum"),
        partner_age=user_data.get("partner_age", "Noma'lum"),
        characteristics=user_data.get("characteristics", "Noma'lum"),
        about_me=user_data.get("about_me", "Noma'lum"),
        contact=user_data.get("contact", "Noma'lum"),
        photo_url="https://t.me/example" # Placeholder, actual photo sent separately
    )
    
    try:
        # Send photo to channel
        photo_file_id = user_data.get("photo_file_id")
        if photo_file_id:
            await bot.send_photo(CHANNEL_ID, photo_file_id, caption=profile_text, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(CHANNEL_ID, profile_text, parse_mode=ParseMode.HTML)
            
        await callback_query.message.edit_text(TEXTS[lang]["thank_you"])
    except Exception as e:
        await callback_query.message.edit_text(f"Xato yuz berdi: {e}") # Error handling
    
    await state.clear()
    await callback_query.answer()

@dp.callback_query(Form.confirm, F.data == "confirm_no")
async def process_confirm_no(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.clear() # Clear state and restart for re-entering data
    await callback_query.message.edit_text(TEXTS[lang]["start"], reply_markup=get_language_keyboard())
    await callback_query.answer()

# --- Invalid input handlers for specific states ---
@dp.message(StateFilter(Form.language))
async def handle_invalid_language_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_language_keyboard())

@dp.message(StateFilter(Form.gender))
async def handle_invalid_gender_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_gender_keyboard(lang))

@dp.message(StateFilter(Form.country))
async def handle_invalid_country_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_country_keyboard(lang))

@dp.message(StateFilter(Form.region))
async def handle_invalid_region_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_region_keyboard(lang))

@dp.message(StateFilter(Form.city))
async def handle_invalid_city_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_city_keyboard(lang, user_data.get("region", ""))) # Pass region to regenerate city keyboard

@dp.message(StateFilter(Form.looking_for_type))
async def handle_invalid_looking_for_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_looking_for_keyboard(lang))

@dp.message(StateFilter(Form.partner_gender))
async def handle_invalid_partner_gender_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    # Need to pass looking_for_type_key for correct keyboard re-generation
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_partner_gender_keyboard(lang, user_data.get("looking_for_type_key")))

@dp.message(StateFilter(Form.partner_age))
async def handle_invalid_partner_age_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["invalid_age_format"])

@dp.message(StateFilter(Form.characteristics))
async def handle_invalid_characteristics_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["invalid_characteristics"])

@dp.message(StateFilter(Form.about_me))
async def handle_invalid_about_me_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["about_me_prompt"]) # Re-prompt for text input

@dp.message(StateFilter(Form.contact))
async def handle_invalid_contact_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["contact_prompt"]) # Re-prompt for text input


# --- Main function ---
async def main() -> None:
    # Start webhook or polling
    if WEBHOOK_URL:
        # Webhook mode
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

        # Keep the main task alive
        while True:
            await asyncio.sleep(3600) # Sleep for 1 hour
    else:
        # Polling mode
        print("Bot started and listening via polling...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
