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

# --- FSM (Finite State Machine) states ---\nclass Form(StatesGroup):
    language = State()
    gender = State()
    # proof_voice = State() # Removed
    country = State()
    region = State()
    custom_region = State()
    city = State()
    # proof_photo = State() # Removed
    age = State()
    height = State()
    weight = State()
    looking_for_type = State()
    partner_gender = State()
    about_me = State()
    contact = State()
    confirm = State()

# --- Keyboards ---
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
        "age_prompt": "Yoshingizni kiriting:",
        "height_prompt": "Bo'yingizni smda kiriting (masalan, 175):",
        "weight_prompt": "Og'irligingizni kgda kiriting (masalan, 70):",
        "looking_for_prompt": "Nima maqsadda tanishmoqchisiz?",
        "partner_gender_prompt": "Kim bilan tanishmoqchisiz (sherikning jinsi)?",
        "about_me_prompt": "O'zingiz haqingizda ma'lumot kiriting (250 belgidan oshmasin):",
        "contact_prompt": "Bog'lanish uchun manzilingizni kiriting (Telegram username, telefon raqam, Instagram linki va hokazo):",
        "confirm_prompt": "Ma'lumotlaringiz to'g'rimi? Davom etish uchun 'Tasdiqlash' tugmasini bosing.",
        "thank_you": "Arizangiz qabul qilindi. Tez orada kanalga joylashtiriladi.",
        "profile_template": (
            "<b>🙋‍♂️ Ism:</b> {full_name}\n"
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n"
            "<b>🚻 Jinsi:</b> {gender}\n"
            "<b>📆 Yoshi:</b> {age}\n"
            "<b>📏 Bo'yi:</b> {height} sm\n"
            "<b>⚖️ Og'irligi:</b> {weight} kg\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n"
            "<b>📞 Bog'lanish:</b> {contact}\n"
            "<a href='https://t.me/example'>Manba: TopTanish</a>" # Example link
        ),
        "invalid_input": "Noto'g'ri kiritish. Iltimos, to'g'ri formatda kiriting.",
        "invalid_age": "Yoshingizni sonlarda kiriting.",
        "invalid_height": "Bo'yingizni sonlarda kiriting.",
        "invalid_weight": "Og'irligingizni sonlarda kiriting.",
        "invalid_callback_input": "Noto'g'ri tanlov. Iltimos, inline tugma orqali tanlang.",
        "select_from_options": "Iltimos, berilgan variantlardan birini tanlang.",
        "text_too_long": "Matn juda uzun. Iltimos, 250 belgidan oshirmang."
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
        "age_prompt": "Введите ваш возраст:",
        "height_prompt": "Введите ваш рост в см (например, 175):",
        "weight_prompt": "Введите ваш вес в кг (например, 70):",
        "looking_for_prompt": "С какой целью вы хотите познакомиться?",
        "partner_gender_prompt": "С кем вы хотите познакомиться (пол партнера)?",
        "about_me_prompt": "Введите информацию о себе (не более 250 символов):",
        "contact_prompt": "Введите ваш контакт (имя пользователя Telegram, номер телефона, ссылка на Instagram и т.д.):",
        "confirm_prompt": "Ваши данные верны? Нажмите 'Подтвердить' для продолжения.",
        "thank_you": "Ваша заявка принята. Скоро она будет размещена на канале.",
        "profile_template": (
            "<b>🙋‍♂️ Имя:</b> {full_name}\n"
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n"
            "<b>🚻 Пол:</b> {gender}\n"
            "<b>📆 Возраст:</b> {age}\n"
            "<b>📏 Рост:</b> {height} см\n"
            "<b>⚖️ Вес:</b> {weight} кг\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n"
            "<b>✍️ О себе:</b> {about_me}\n"
            "<b>📞 Контакт:</b> {contact}\n"
            "<a href='https://t.me/example'>Источник: TopTanish</a>" # Example link
        ),
        "invalid_input": "Неверный ввод. Пожалуйста, введите в правильном формате.",
        "invalid_age": "Введите ваш возраст цифрами.",
        "invalid_height": "Введите ваш рост цифрами.",
        "invalid_weight": "Введите ваш вес цифрами.",
        "invalid_callback_input": "Неверный выбор. Пожалуйста, выберите с помощью встроенной кнопки.",
        "select_from_options": "Пожалуйста, выберите один из предложенных вариантов.",
        "text_too_long": "Текст слишком длинный. Пожалуйста, не превышайте 250 символов."
    }
}

GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"}
}

LOOKING_FOR_OPTIONS = {
    "serious_relationship": {"uz": "Intim munosabat 18+", "ru": "Интимные отношения"},
    "friendship": {"uz": "Do'stlik", "ru": "Дружба"},
    "dating": {"uz": "Uchrashuv", "ru": "Свидания"},
    "marriage": {"uz": "Turmush qurish", "ru": "Брак"},
}

PARTNER_GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "any": {"uz": "Farqi yo'q", "ru": "Неважно"},
    "family": {"uz": "Oilani", "ru": "Семью"} # YANGI QO'SHILDI
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

def get_partner_gender_keyboard(lang: str):
    keyboard = []
    for key, value in PARTNER_GENDER_OPTIONS.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"partner_gender_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["confirm_prompt"], callback_data="confirm_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="confirm_no")] # Use "Other" for "No" or "Edit"
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- Handlers ---
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
    await state.update_data(gender=GENDER_OPTIONS[gender][lang])
    await state.set_state(Form.country)
    await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_country_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.country, F.data.startswith("country_"))
async def process_country(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = callback_query.data.split("_")[1]
    
    # Store the actual text of the country, not the key
    selected_country_text = COUNTRIES.get(country_key, country_key) 
    
    await state.update_data(country=selected_country_text)

    if country_key == "other":
        await state.set_state(Form.custom_region) # Skip region, go straight to custom region for "Other" country
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
        await state.set_state(Form.age)
        await callback_query.message.edit_text(TEXTS[lang]["age_prompt"])
    await callback_query.answer()

@dp.message(Form.custom_city)
async def process_custom_city(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        await state.update_data(city=message.text)
        await state.set_state(Form.age)
        await message.answer(TEXTS[lang]["age_prompt"])
    else:
        await message.answer(TEXTS[lang]["invalid_input"])

@dp.message(StateFilter(Form.age))
async def process_age(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and message.text.isdigit():
        age = int(message.text)
        if 18 <= age <= 99: # Example age range
            await state.update_data(age=age)
            await state.set_state(Form.height)
            await message.answer(TEXTS[lang]["height_prompt"])
        else:
            await message.answer(TEXTS[lang]["invalid_age"])
    else:
        await message.answer(TEXTS[lang]["invalid_age"])

@dp.message(StateFilter(Form.height))
async def process_height(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and message.text.isdigit():
        height = int(message.text)
        if 100 <= height <= 250: # Example height range
            await state.update_data(height=height)
            await state.set_state(Form.weight)
            await message.answer(TEXTS[lang]["weight_prompt"])
        else:
            await message.answer(TEXTS[lang]["invalid_height"])
    else:
        await message.answer(TEXTS[lang]["invalid_height"])

@dp.message(StateFilter(Form.weight))
async def process_weight(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and message.text.isdigit():
        weight = int(message.text)
        if 30 <= weight <= 200: # Example weight range
            await state.update_data(weight=weight)
            await state.set_state(Form.looking_for_type)
            await message.answer(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
        else:
            await message.answer(TEXTS[lang]["invalid_weight"])
    else:
        await message.answer(TEXTS[lang]["invalid_weight"])

@dp.callback_query(Form.looking_for_type, F.data.startswith("looking_"))
async def process_looking_for(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_for_key = callback_query.data.split("_")[1]
    if looking_for_key in LOOKING_FOR_OPTIONS:
        await state.update_data(looking_for_type=LOOKING_FOR_OPTIONS[looking_for_key][lang])
        await state.set_state(Form.partner_gender)
        await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang))
    else:
        print(f"DEBUG: Invalid looking_for_key received: {looking_for_key} from callback_data: {callback_query.data}")
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.partner_gender, F.data.startswith("partner_gender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_gender_key = callback_query.data.split("_")[2]
    if partner_gender_key in PARTNER_GENDER_OPTIONS:
        await state.update_data(partner_gender=PARTNER_GENDER_OPTIONS[partner_gender_key][lang])
        await state.set_state(Form.about_me)
        await callback_query.message.edit_text(TEXTS[lang]["about_me_prompt"])
    else:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_partner_gender_keyboard(lang))
    await callback_query.answer()

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
        
        # Get full name from user's message object
        full_name = message.from_user.full_name if message.from_user else "Noma'lum"
        await state.update_data(full_name=full_name) # Save full name to state

        # Display confirmation
        final_data = await state.get_data()
        profile_text = TEXTS[lang]["profile_template"].format(
            full_name=final_data.get("full_name", "Noma'lum"),
            country=final_data.get("country", "Noma'lum"),
            region=final_data.get("region", "Noma'lum"),
            city=final_data.get("city", "Noma'lum"),
            gender=final_data.get("gender", "Noma'lum"),
            age=final_data.get("age", "Noma'lum"),
            height=final_data.get("height", "Noma'lum"),
            weight=final_data.get("weight", "Noma'lum"),
            looking_for_type=final_data.get("looking_for_type", "Noma'lum"),
            partner_gender=final_data.get("partner_gender", "Noma'lum"),
            about_me=final_data.get("about_me", "Noma'lum"),
            contact=final_data.get("contact", "Noma'lum")
        )
        await message.answer(profile_text, reply_markup=get_confirm_keyboard(lang))
        await state.set_state(Form.confirm)
    else:
        await message.answer(TEXTS[lang]["invalid_input"])

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
        age=user_data.get("age", "Noma'lum"),
        height=user_data.get("height", "Noma'lum"),
        weight=user_data.get("weight", "Noma'lum"),
        looking_for_type=user_data.get("looking_for_type", "Noma'lum"),
        partner_gender=user_data.get("partner_gender", "Noma'lum"),
        about_me=user_data.get("about_me", "Noma'lum"),
        contact=user_data.get("contact", "Noma'lum")
    )
    
    try:
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
    await message.answer(TEXTS[lang]["select_from_options"], reply_markup=get_partner_gender_keyboard(lang))

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
