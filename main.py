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


# --- FSM (Finite State Machine) states ---
class Form(StatesGroup):
    language = State()
    gender = State()
    country = State()
    region = State()
    custom_region = State()
    city = State()
    custom_city = State()
    looking_for_type = State()
    partner_gender = State()
    partner_age = State()
    partner_info = State()
    about_me = State()
    characteristics = State()
    contact_type = State()
    phone_number = State()
    username = State()
    photo_upload = State()
    channel_check = State()
    publish_consent = State()
    confirm = State()
    # Removed admin_reply and admin_review states as per user request


TEXTS = {
    "uz": {
        "start": "Salom! Botdan foydalanish uchun tilingizni tanlang:",
        "choose_language": "Iltimos, tilingizni tanlang:",
        "language_selected": "Til o'zbek tiliga o'rnatildi.",
        "gender_prompt": "O'zingizning jinsingizni tanlang:",
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
        "contact_type_prompt": "Bog'lanish uchun qanday ma'lumot qoldirishni xohlaysiz?",
        "phone_number_prompt": "Iltimos, telefon raqamingizni kiriting (masalan, +998XXXXXXXXX):",
        "username_prompt": "Iltimos, Telegram username, Instagram linki yoki boshqa profilingizga havolani kiriting (masalan, @username yoki instagram.com/user):",
        "photo_upload_prompt": "Iltimas, profilingiz uchun rasm yuklang (yuzingiz aniq ko'rinishi shart) yoki 'Yuklamaslik' tugmasini bosing:",
        "channel_check_prompt": "Arizangizni kanalga joylashdan oldin, iltimos, bizning kanalimizga a'zo bo'ling:",
        "channel_button_text": "Kanalga a'zo bo'lish",
        "not_a_member": "Siz kanalga a'zo emassiz. Iltimos, kanalga a'zo bo'lib, 'Tekshirish' tugmasini bosing.",
        "publish_consent_prompt": "Ma'lumotlaringizni kanalga chop etishimizga rozimisiz?",
        "confirm_prompt": "Ma'lumotlaringiz to'g'rimi?",
        "thank_you": "Arizangiz qabul qilindi. Ma'lumotlaringiz kanalga avtomatik tarzda joylashtirildi va sizga yuborildi.",
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
            "<a href='https://t.me/@Tanishuv18plus_bot'>Manba: TopTanish</a>"
        ),
        "user_profile_template": (  # Template for user's own confirmation message
            "<b>Sizning arizangiz kanalga muvaffaqiyatli joylashtirildi!</b>\n\n"
            "<b>🙋‍♂️ Ism:</b> {full_name} (<a href='{user_profile_link}'>Profilga havola</a>)\n"
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n"
            "<b>🚻 Jinsi:</b> {gender}\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n"
            "<b>🔢 Qidirayotgan yoshi:</b> {partner_age}\n"
            "<b>✨ Sherik haqida ma'lumot:</b> {partner_info}\n"
            "<b>📝 O'zi haqida xususiyatlari:</b> {characteristics}\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n"
            "<b>📞 Bog'lanish:</b> {contact}\n"
            "<b>Bot orqali sizga javob yozish:</b> {reply_to_user_link}"
        ),
        "invalid_input": "Noto'g'ri kiritish. Iltimos, to'g'ri formatda kiriting.",
        "invalid_age_format": "Yoshingizni to'g'ri formatda kiriting (masalan, 25-35).",
        "invalid_characteristics": "Iltimos, xususiyatlaringizni to'g'ri formatda kiriting. Namuna: Yoshi: 25, Bo'yi: 170sm, Og'irligi: 65kg, Sportchi",
        "invalid_callback_input": "Noto'g'ri tanlov. Iltimos, inline tugma orqali tanlang.",
        "select_from_options": "Iltimos, berilgan variantlardan birini tanlang.",
        "text_too_long": "Matn juda uzun. Iltimos, 250 belgidan oshirmang.",
        "other": "Boshqa",
        "back_button": "🔙 Orqaga",
        "skip_photo": "Yuklamaslik",
        "contact_number_only": "Faqat raqam",
        "contact_username_only": "Faqat username (link)",
        "contact_both": "Ikkalasi ham",
        "invalid_phone_number": "Noto'g'ri telefon raqami formati. Iltimos, +998XXXXXXXXX formatida kiriting.",
        "partner_info_prompt": "Qidirayotgan sherigingiz haqida qisqacha ma'lumot kiriting:",
        # Removed admin related messages
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
        "contact_type_prompt": "Какую информацию для связи вы хотите оставить?",
        "phone_number_prompt": "Пожалуйста, введите ваш номер телефона (например, +998XXXXXXXXX):",
        "username_prompt": "Пожалуйста, введите имя пользователя Telegram, ссылку на Instagram или другую ссылку на ваш профиль (например, @username или instagram.com/user):",
        "photo_upload_prompt": "Пожалуйста, загрузите фото для вашего профиля (лицо должно быть хорошо видно) или нажмите 'Не загружать':",
        "channel_check_prompt": "Перед публикацией вашей заявки на канале, пожалуйста, подпишитесь на наш канал:",
        "channel_button_text": "Подписаться на канал",
        "not_a_member": "Вы не подписаны на канал. Пожалуйста, подпишитесь на канал и нажмите кнопку 'Проверить'.",
        "publish_consent_prompt": "Вы согласны на публикацию ваших данных на канале?",
        "confirm_prompt": "Ваши данные верны?",
        "thank_you": "Ваша заявка принята. Ваши данные автоматически размещены на канале и отправлены вам.",
        "profile_template": (
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n"
            "<b>🚻 Пол:</b> {gender}\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n"
            "<b>✨ Информация о партнере:</b> {partner_info}\n"
            "<b>📝 О себе (характеристики):</b> {characteristics}\n"
            "<b>✍️ О себе:</b> {about_me}\n"
            "<b>📞 Контакт:</b> {contact}\n"
            "<a href='https://t.me/@Tanishuv18plus_bot'>Источник: TopTanish</a>"
        ),
        "user_profile_template": (  # Template for user's own confirmation message
            "<b>Ваша заявка успешно размещена на канале!</b>\n\n"
            "<b>🙋‍♂️ Имя:</b> {full_name} (<a href='{user_profile_link}'>Ссылка на профиль</a>)\n"
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n"
            "<b>🚻 Пол:</b> {gender}\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n"
            "<b>✨ Информация о партнере:</b> {partner_info}\n"
            "<b>📝 О себе (характеристики):</b> {characteristics}\n"
            "<b>✍️ О себе:</b> {about_me}\n"
            "<b>📞 Контакт:</b> {contact}\n"
            "<b>Ответить вам через бота:</b> {reply_to_user_link}"
        ),
        "invalid_input": "Неверный ввод. Пожалуйста, введите в правильном формате.",
        "invalid_age_format": "Введите возраст в правильном формате (например, 25-35).",
        "invalid_characteristics": "Пожалуйста, введите ваши характеристики в правильном формате. Пример: Возраст: 25, Рост: 170см, Вес: 65кг, Спортсмен",
        "invalid_callback_input": "Неверный выбор. Пожалуйста, выберите с помощью встроенной кнопки.",
        "select_from_options": "Пожалуйста, выберите один из предложенных вариантов.",
        "text_too_long": "Текст слишком длинный. Пожалуйста, не превышайте 250 символов.",
        "other": "Другое",
        "back_button": "🔙 Назад",
        "skip_photo": "Не загружать",
        "contact_number_only": "Только номер",
        "contact_username_only": "Только имя пользователя (ссылка)",
        "contact_both": "И то, и другое",
        "invalid_phone_number": "Неверный формат номера телефона. Пожалуйста, введите в формате +998XXXXXXXXX.",
        "partner_info_prompt": "Введите краткую информацию о партнере, которого вы ищете:",
        # Removed admin related messages
    }
}

DEFAULT_PHOTO_URLS = {
    "male": "https://img.freepik.com/premium-vector/business-man-vector-silhouette-illustration_554682-2324.jpg",
    # REPLACE with actual URL
    "female": "https://img.freepik.com/premium-photo/silhouette-beautiful-young-woman-black-lingerie_949828-10264.jpg?semt=ais_hybrid&w=740",
    # REPLACE with actual URL
    "family": "https://st3.depositphotos.com/17392768/32153/i/450/depositphotos_321539808-stock-photo-man-woman-passionately-embrace-each.jpg",
    # REPLACE with actual URL
    "default": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRC57QkJrIJVFfdbSyL8XWctGIcQhMmQJq9_w&s"
    # Fallback if gender is not found
}

GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "family": {"uz": "Oila 👨‍👩‍👧‍👦", "ru": "Семья 👨‍👩‍👧‍👦"}
}

LOOKING_FOR_OPTIONS = {
    "intimate_18": {"uz": "Intim/Seks munosabat 18+", "ru": "Интимные/Секс отношения 18+"},
    "friendship": {"uz": "Do'stlik", "ru": "Дружба"},
    "marriage": {"uz": "Nikoh", "ru": "Брак"},
    "pleasant_chat": {"uz": "Yoqimli suhbat", "ru": "Приятное общение"},
    "no_preference": {"uz": "Farqi yo'q", "ru": "Неважно"}
}

PARTNER_GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "family": {"uz": "Oila 👨‍👩‍👧‍👦", "ru": "Семья 👨‍👩‍👧‍👦"},
    "any": {"uz": "Farqi yo'q", "ru": "Неважно"}
}

COUNTRIES = {
    "uz": "O'zbekiston",
    "ru": "Rossiya",
    "kz": "Qozog'iston",
    "kg": "Qirg'iziston",
    "tj": "Tojikiston",
    "tm": "Turkmaniston",
    "other": "Boshqa"
}

REGIONS = {
    "uz": [
        "Andijon", "Buxoro", "Farg'ona", "Jizzax", "Xorazm", "Namangan",
        "Navoiy", "Qashqadaryo", "Samarqand", "Sirdaryo", "Surxondaryo",
        "Toshkent viloyati", "Toshkent shahri", "Qoraqalpog'iston Respublikasi"
    ],
    "ru": [
        "Moskva", "Sankt-Peterburg", "Tatarstan", "Bashkortostan", "Novosibirsk viloyati", "Sverdlovsk viloyati",
        "Krasnodar o'lkasi"
    ],
    "kz": [
        "Almati", "Ostona", "Chimkent", "Qarag'anda", "Aqto'be"
    ],
    "kg": [
        "Bishkek", "O'sh", "Jalolobod", "Issiqko'l"
    ],
    "tj": [
        "Dushanbe", "Xo'jand", "Kulob", "Qo'rg'ontepa"
    ],
    "tm": [
        "Ashxabod", "Turkmanobod", "Dashoguz", "Mari"
    ]
}

CITIES = {
    "uz": {
        "Toshkent shahri": ["Toshkent"],
        "Toshkent viloyati": ["Angren", "Bekobod", "Chirchiq", "G'azalkent", "Keles", "Olmaliq", "Ohangaron", "Parkent",
                              "Piskent", "Yangiobod", "Yangiyo'l", "Qibray", "Nurafshon"],
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
    },
    "ru": {
        "Moskva": ["Moskva"],
        "Sankt-Peterburg": ["Sankt-Peterburg"],
        "Tatarstan": ["Qozon", "Naberezhnye Chelny"],
        "Bashkortostan": ["Ufa", "Sterlitamak"],
        "Novosibirsk viloyati": ["Novosibirsk"],
        "Sverdlovsk viloyati": ["Yekaterinburg", "Nijniy Tagil"],
        "Krasnodar o'lkasi": ["Krasnodar", "Sochi"]
    },
    "kz": {
        "Almati": ["Almati"],
        "Ostona": ["Ostona"],
        "Chimkent": ["Chimkent"],
        "Qarag'anda": ["Qarag'anda"],
        "Aqto'be": ["Aqto'be"]
    },
    "kg": {
        "Bishkek": ["Bishkek"],
        "O'sh": ["O'sh"],
        "Jalolobod": ["Jalolobod"],
        "Issiqko'l": ["Qoraqol", "Cholponota"]
    },
    "tj": {
        "Dushanbe": ["Dushanbe"],
        "Xo'jand": ["Xo'jand"],
        "Kulob": ["Kulob"],
        "Qo'rg'ontepa": ["Boxtar"]
    },
    "tm": {
        "Ashxabod": ["Ashxabod"],
        "Turkmanobod": ["Turkmanobod"],
        "Dashoguz": ["Dashoguz"],
        "Mari": ["Mari"]
    }
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
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_language")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_country_keyboard(lang: str):
    keyboard = []
    for key, value in COUNTRIES.items():
        keyboard.append([InlineKeyboardButton(text=value, callback_data=f"country_{key}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_gender")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_region_keyboard(lang: str, country_key: str):
    keyboard = []
    regions_for_country = REGIONS.get(country_key, [])
    for region in regions_for_country:
        keyboard.append([InlineKeyboardButton(text=region, callback_data=f"region_{region}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="region_other")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_country")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_city_keyboard(lang: str, country_key: str, region: str):
    keyboard = []
    cities_for_region = CITIES.get(country_key, {}).get(region, [])
    for city in cities_for_region:
        keyboard.append([InlineKeyboardButton(text=city, callback_data=f"city_{city}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["other"], callback_data="city_other")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_region")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_looking_for_keyboard(lang: str):
    keyboard = []
    for key, value in LOOKING_FOR_OPTIONS.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"looking_{key}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_city")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_partner_gender_keyboard(lang: str, looking_for_type_key: str = None):
    keyboard = []
    if looking_for_type_key == "intimate_18":
        options = {k: v for k, v in PARTNER_GENDER_OPTIONS.items() if k in ["male", "female", "family"]}
    else:
        options = PARTNER_GENDER_OPTIONS

    for key, value in options.items():
        keyboard.append([InlineKeyboardButton(text=value[lang], callback_data=f"partner_gender_{key}")])
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_looking_for")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contact_type_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["contact_number_only"], callback_data="contact_type_number")],
        [InlineKeyboardButton(text=TEXTS[lang]["contact_username_only"], callback_data="contact_type_username")],
        [InlineKeyboardButton(text=TEXTS[lang]["contact_both"], callback_data="contact_type_both")]
    ]
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_about_me")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_photo_upload_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["skip_photo"], callback_data="skip_photo_upload")],
        [InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_contact")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_channel_check_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text=TEXTS[lang]["channel_button_text"], url=f"https://t.me/ommaviy_tanishuv_kanali")],  # REPLACE with your channel link
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_channel_member")]
    ]
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_photo_upload")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_publish_consent_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ Roziman", callback_data="consent_yes")],
        [InlineKeyboardButton(text="❌ Rad etaman", callback_data="consent_no")]
    ]
    keyboard.append([InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="back_to_channel_check")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_keyboard(lang: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="confirm_no")]  # Use "Back" for "No" or "Edit"
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Removed get_admin_review_keyboard as per user request

# --- Handlers ---
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.language)
    await message.answer(TEXTS["uz"]["start"], reply_markup=get_language_keyboard())


# --- BACK BUTTON HANDLERS ---
@dp.callback_query(F.data == "back_to_language")
async def back_to_language(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.language)
    await callback_query.message.edit_text(TEXTS[lang]["start"], reply_markup=get_language_keyboard())
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_gender")
async def back_to_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.gender)
    await callback_query.message.edit_text(TEXTS[lang]["gender_prompt"], reply_markup=get_gender_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_country")
async def back_to_country(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.country)
    await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_country_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_region")
async def back_to_region(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key", "uz")  # Need to get original country key
    await state.set_state(Form.region)
    await callback_query.message.edit_text(TEXTS[lang]["region_prompt"], reply_markup=get_region_keyboard(lang, country_key))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_city")
async def back_to_city(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key", "uz")
    region = user_data.get("region", "")
    await state.set_state(Form.city)
    await callback_query.message.edit_text(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, country_key, region))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_looking_for")
async def back_to_looking_for(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.looking_for_type)
    await callback_query.message.edit_text(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_partner_gender")
async def back_to_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_for_type_key = user_data.get("looking_for_type_key")
    await state.set_state(Form.partner_gender)
    await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang, looking_for_type_key))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_partner_age")
async def back_to_partner_age(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.partner_age)
    await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_partner_info")
async def back_to_partner_info(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.partner_info)
    await callback_query.message.edit_text(TEXTS[lang]["partner_info_prompt"])
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_characteristics")
async def back_to_characteristics(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.characteristics)
    await callback_query.message.edit_text(TEXTS[lang]["characteristics_prompt"])
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_about_me")
async def back_to_about_me(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.about_me)
    await callback_query.message.edit_text(TEXTS[lang]["about_me_prompt"])
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_contact")
async def back_to_contact(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.contact_type)
    await callback_query.message.edit_text(TEXTS[lang]["contact_type_prompt"], reply_markup=get_contact_type_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_photo_upload")
async def back_to_photo_upload(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.photo_upload)
    await callback_query.message.edit_text(TEXTS[lang]["photo_upload_prompt"], reply_markup=get_photo_upload_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_channel_check")
async def back_to_channel_check(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.channel_check)
    await callback_query.message.edit_text(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_publish_consent")
async def back_to_publish_consent(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.publish_consent)
    await callback_query.message.edit_text(TEXTS[lang]["publish_consent_prompt"], reply_markup=get_publish_consent_keyboard(lang))
    await callback_query.answer()


# --- Language Selection ---
@dp.callback_query(StateFilter(Form.language), F.data.startswith("lang_"))
async def process_language(callback_query: CallbackQuery, state: FSMContext):
    lang = callback_query.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(Form.gender)
    await callback_query.message.edit_text(TEXTS[lang]["gender_prompt"], reply_markup=get_gender_keyboard(lang))
    await callback_query.answer()


# --- Gender Selection ---
@dp.callback_query(StateFilter(Form.gender), F.data.startswith("gender_"))
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    gender_key = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    lang = user_data["lang"]
    gender_text = GENDER_OPTIONS[gender_key][lang]
    await state.update_data(gender=gender_text, gender_key=gender_key)
    await state.set_state(Form.country)
    await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_country_keyboard(lang))
    await callback_query.answer()


# --- Country Selection ---
@dp.callback_query(StateFilter(Form.country), F.data.startswith("country_"))
async def process_country(callback_query: CallbackQuery, state: FSMContext):
    country_key = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    lang = user_data["lang"]
    country_text = COUNTRIES[country_key]
    await state.update_data(country=country_text, country_key=country_key)
    await state.set_state(Form.region)
    await callback_query.message.edit_text(TEXTS[lang]["region_prompt"], reply_markup=get_region_keyboard(lang, country_key))
    await callback_query.answer()


# --- Region Selection ---
@dp.callback_query(StateFilter(Form.region), F.data.startswith("region_"))
async def process_region_callback(callback_query: CallbackQuery, state: FSMContext):
    region = callback_query.data.split("_", 1)[1]
    user_data = await state.get_data()
    lang = user_data["lang"]

    if region == "other":
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.update_data(region=region)
        await state.set_state(Form.city)
        country_key = user_data["country_key"]
        await callback_query.message.edit_text(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, country_key, region))
    await callback_query.answer()


@dp.message(StateFilter(Form.custom_region))
async def process_custom_region(message: Message, state: FSMContext):
    region = message.text.strip()
    if not region:
        user_data = await state.get_data()
        lang = user_data["lang"]
        await message.answer(TEXTS[lang]["invalid_input"])
        return

    await state.update_data(region=region)
    user_data = await state.get_data()
    lang = user_data["lang"]
    country_key = user_data["country_key"]
    await state.set_state(Form.city)
    await message.answer(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, country_key, region))


# --- City Selection ---
@dp.callback_query(StateFilter(Form.city), F.data.startswith("city_"))
async def process_city_callback(callback_query: CallbackQuery, state: FSMContext):
    city = callback_query.data.split("_", 1)[1]
    user_data = await state.get_data()
    lang = user_data["lang"]

    if city == "other":
        await state.set_state(Form.custom_city)
        await callback_query.message.edit_text(TEXTS[lang]["custom_city_prompt"])
    else:
        await state.update_data(city=city)
        await state.set_state(Form.looking_for_type)
        await callback_query.message.edit_text(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()


@dp.message(StateFilter(Form.custom_city))
async def process_custom_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        user_data = await state.get_data()
        lang = user_data["lang"]
        await message.answer(TEXTS[lang]["invalid_input"])
        return

    await state.update_data(city=city)
    user_data = await state.get_data()
    lang = user_data["lang"]
    await state.set_state(Form.looking_for_type)
    await message.answer(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))


# --- Looking For Type Selection ---
@dp.callback_query(StateFilter(Form.looking_for_type), F.data.startswith("looking_"))
async def process_looking_for(callback_query: CallbackQuery, state: FSMContext):
    looking_for_type_key = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    lang = user_data["lang"]
    looking_for_type_text = LOOKING_FOR_OPTIONS[looking_for_type_key][lang]
    await state.update_data(looking_for_type=looking_for_type_text, looking_for_type_key=looking_for_type_key)
    await state.set_state(Form.partner_gender)
    await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang, looking_for_type_key))
    await callback_query.answer()


# --- Partner Gender Selection ---
@dp.callback_query(StateFilter(Form.partner_gender), F.data.startswith("partner_gender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    partner_gender_key = callback_query.data.split("_")[2]
    user_data = await state.get_data()
    lang = user_data["lang"]
    partner_gender_text = PARTNER_GENDER_OPTIONS[partner_gender_key][lang]
    await state.update_data(partner_gender=partner_gender_text)
    await state.set_state(Form.partner_age)
    await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    await callback_query.answer()


# --- Partner Age Input ---
@dp.message(StateFilter(Form.partner_age))
async def process_partner_age(message: Message, state: FSMContext):
    partner_age = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if not (2 <= len(partner_age.split('-')) <= 2 and all(p.isdigit() for p in partner_age.split('-'))):
        await message.answer(TEXTS[lang]["invalid_age_format"])
        return

    await state.update_data(partner_age=partner_age)
    await state.set_state(Form.partner_info)
    await message.answer(TEXTS[lang]["partner_info_prompt"])


# --- Partner Info Input ---
@dp.message(StateFilter(Form.partner_info))
async def process_partner_info(message: Message, state: FSMContext):
    partner_info = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if len(partner_info) > 250:
        await message.answer(TEXTS[lang]["text_too_long"])
        return

    await state.update_data(partner_info=partner_info)
    await state.set_state(Form.characteristics)
    await message.answer(TEXTS[lang]["characteristics_prompt"])


# --- Characteristics Input ---
@dp.message(StateFilter(Form.characteristics))
async def process_characteristics(message: Message, state: FSMContext):
    characteristics = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if not characteristics:
        await message.answer(TEXTS[lang]["invalid_input"])
        return

    await state.update_data(characteristics=characteristics)
    await state.set_state(Form.about_me)
    await message.answer(TEXTS[lang]["about_me_prompt"])


# --- About Me Input ---
@dp.message(StateFilter(Form.about_me))
async def process_about_me(message: Message, state: FSMContext):
    about_me = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if len(about_me) > 250:
        await message.answer(TEXTS[lang]["text_too_long"])
        return

    await state.update_data(about_me=about_me)
    await state.set_state(Form.contact_type)
    await message.answer(TEXTS[lang]["contact_type_prompt"], reply_markup=get_contact_type_keyboard(lang))


# --- Contact Type Selection ---
@dp.callback_query(StateFilter(Form.contact_type), F.data.startswith("contact_type_"))
async def process_contact_type(callback_query: CallbackQuery, state: FSMContext):
    contact_type = callback_query.data.split("_")[2]
    user_data = await state.get_data()
    lang = user_data["lang"]

    await state.update_data(contact_type=contact_type)

    if contact_type == "number":
        await state.set_state(Form.phone_number)
        await callback_query.message.edit_text(TEXTS[lang]["phone_number_prompt"])
    elif contact_type == "username":
        await state.set_state(Form.username)
        await callback_query.message.edit_text(TEXTS[lang]["username_prompt"])
    elif contact_type == "both":
        await state.set_state(Form.phone_number)
        await callback_query.message.edit_text(TEXTS[lang]["phone_number_prompt"])
    await callback_query.answer()


# --- Phone Number Input ---
@dp.message(StateFilter(Form.phone_number))
async def process_phone_number(message: Message, state: FSMContext):
    phone_number = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if not (phone_number.startswith('+') and phone_number[1:].isdigit() and len(phone_number) > 9):
        await message.answer(TEXTS[lang]["invalid_phone_number"])
        return

    await state.update_data(phone_number=phone_number)
    if user_data["contact_type"] == "both":
        await state.set_state(Form.username)
        await message.answer(TEXTS[lang]["username_prompt"])
    else:
        await state.set_state(Form.photo_upload)
        await message.answer(TEXTS[lang]["photo_upload_prompt"], reply_markup=get_photo_upload_keyboard(lang))


# --- Username/Link Input ---
@dp.message(StateFilter(Form.username))
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()
    user_data = await state.get_data()
    lang = user_data["lang"]

    if not username:
        await message.answer(TEXTS[lang]["invalid_input"])
        return

    await state.update_data(username=username)
    await state.set_state(Form.photo_upload)
    await message.answer(TEXTS[lang]["photo_upload_prompt"], reply_markup=get_photo_upload_keyboard(lang))


# --- Photo Upload ---
@dp.message(StateFilter(Form.photo_upload), F.photo | F.text == TEXTS["uz"]["skip_photo"] | F.text == TEXTS["ru"]["skip_photo"])
async def process_photo_upload(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data["lang"]
    photo_file_id = None
    photo_url = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        # In a real scenario, you would download the photo and store it,
        # then generate a public URL. For this example, we'll store the file_id.
        # Or, you can fetch the file path directly if your bot has local access
        file = await bot.get_file(photo_file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        await state.update_data(photo_file_id=photo_file_id, photo_url=photo_url)
        await message.answer("Rasm qabul qilindi. ✅") # User feedback

    elif message.text in [TEXTS["uz"]["skip_photo"], TEXTS["ru"]["skip_photo"]]:
        gender_key = user_data.get("gender_key", "default")
        photo_url = DEFAULT_PHOTO_URLS.get(gender_key, DEFAULT_PHOTO_URLS["default"])
        await state.update_data(photo_url=photo_url, photo_file_id=None)
        await message.answer("Rasm yuklash o'tkazib yuborildi. ✅") # User feedback
    else:
        await message.answer(TEXTS[lang]["invalid_input"])
        return

    await state.set_state(Form.channel_check)
    await message.answer(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))


@dp.callback_query(F.data == "skip_photo_upload")
async def process_skip_photo_callback(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data["lang"]
    gender_key = user_data.get("gender_key", "default")
    photo_url = DEFAULT_PHOTO_URLS.get(gender_key, DEFAULT_PHOTO_URLS["default"])
    await state.update_data(photo_url=photo_url, photo_file_id=None)
    await state.set_state(Form.channel_check)
    await callback_query.message.edit_text(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))
    await callback_query.answer()


# --- Channel Check ---
@dp.callback_query(StateFilter(Form.channel_check), F.data == "check_channel_member")
async def check_channel_member(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_data = await state.get_data()
    lang = user_data["lang"]

    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            await state.set_state(Form.publish_consent)
            await callback_query.message.edit_text(TEXTS[lang]["publish_consent_prompt"], reply_markup=get_publish_consent_keyboard(lang))
        else:
            await callback_query.message.edit_text(TEXTS[lang]["not_a_member"], reply_markup=get_channel_check_keyboard(lang))
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        await callback_query.message.edit_text(TEXTS[lang]["not_a_member"], reply_markup=get_channel_check_keyboard(lang))
    await callback_query.answer()


# --- Publish Consent ---
@dp.callback_query(StateFilter(Form.publish_consent), F.data.startswith("consent_"))
async def process_publish_consent(callback_query: CallbackQuery, state: FSMContext):
    consent = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    lang = user_data["lang"]

    if consent == "yes":
        await state.set_state(Form.confirm)
        user_profile_text = format_user_profile(user_data, lang, callback_query.from_user)
        await callback_query.message.edit_text(TEXTS[lang]["confirm_prompt"] + "\n\n" + user_profile_text, reply_markup=get_confirm_keyboard(lang))
    else:
        # If user denies, restart the process or inform them
        await state.clear()
        await callback_query.message.edit_text("Arizangiz rad etildi. Botdan foydalanish uchun /start buyrug'ini yuboring.")
    await callback_query.answer()


# --- Confirmation ---
@dp.callback_query(StateFilter(Form.confirm), F.data == "confirm_yes")
async def process_confirm(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data["lang"]
    photo_url = user_data.get("photo_url")
    photo_file_id = user_data.get("photo_file_id")

    # Format profile for channel
    profile_text_for_channel = format_profile_for_channel(user_data, lang)

    # Send photo with caption to channel
    if photo_file_id:
        message_to_channel = await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo_file_id,
            caption=profile_text_for_channel,
            parse_mode=ParseMode.HTML
        )
    elif photo_url:
        message_to_channel = await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo_url,
            caption=profile_text_for_channel,
            parse_mode=ParseMode.HTML
        )
    else:
        message_to_channel = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=profile_text_for_channel,
            parse_mode=ParseMode.HTML
        )

    # Format profile for user's own confirmation
    user_profile_text = format_user_profile(user_data, lang, callback_query.from_user)

    # Send confirmation to user
    await callback_query.message.answer(TEXTS[lang]["thank_you"]) # Changed from edit_text to answer to avoid TelegramBadRequest

    # Send application to admin
    admin_notification_text = (
        f"Yangi ariza kelib tushdi!\n\n"
        f"<b>🙋‍♂️ Ism:</b> {callback_query.from_user.full_name} (<a href='tg://user?id={callback_query.from_user.id}'>Profilga havola</a>)\n\n"
        f"{profile_text_for_channel}\n\n"
        f"<a href='tg://user?id={callback_query.from_user.id}'>Userga javob yuborish</a>"
    )

    if photo_file_id:
        await bot.send_photo(
            chat_id=BOT_ADMIN_ID,
            photo=photo_file_id,
            caption=admin_notification_text,
            parse_mode=ParseMode.HTML
        )
    elif photo_url:
        await bot.send_photo(
            chat_id=BOT_ADMIN_ID,
            photo=photo_url,
            caption=admin_notification_text,
            parse_mode=ParseMode.HTML
        )
    else:
        await bot.send_message(
            chat_id=BOT_ADMIN_ID,
            text=admin_notification_text,
            parse_mode=ParseMode.HTML
        )

    await state.clear()
    await callback_query.answer("Arizangiz tasdiqlandi!")


@dp.callback_query(StateFilter(Form.confirm), F.data == "confirm_no")
async def process_confirm_no(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data["lang"]
    await state.set_state(Form.publish_consent)
    await callback_query.message.edit_text(TEXTS[lang]["publish_consent_prompt"], reply_markup=get_publish_consent_keyboard(lang))
    await callback_query.answer()


# --- Formatting Functions ---
def format_profile_for_channel(data: dict, lang: str) -> str:
    contact_info = ""
    if data.get("contact_type") == "number":
        contact_info = data.get("phone_number", "N/A")
    elif data.get("contact_type") == "username":
        contact_info = data.get("username", "N/A")
    elif data.get("contact_type") == "both":
        contact_info = f"{data.get('phone_number', 'N/A')}, {data.get('username', 'N/A')}"

    return TEXTS[lang]["profile_template"].format(
        country=data.get("country", "N/A"),
        region=data.get("region", "N/A"),
        city=data.get("city", "N/A"),
        gender=data.get("gender", "N/A"),
        looking_for_type=data.get("looking_for_type", "N/A"),
        partner_gender=data.get("partner_gender", "N/A"),
        partner_age=data.get("partner_age", "N/A"),
        partner_info=data.get("partner_info", "N/A"),
        characteristics=data.get("characteristics", "N/A"),
        about_me=data.get("about_me", "N/A"),
        contact=contact_info
    )


def format_user_profile(data: dict, lang: str, user: types.User) -> str:
    contact_info = ""
    if data.get("contact_type") == "number":
        contact_info = data.get("phone_number", "N/A")
    elif data.get("contact_type") == "username":
        contact_info = data.get("username", "N/A")
    elif data.get("contact_type") == "both":
        contact_info = f"{data.get('phone_number', 'N/A')}, {data.get('username', 'N/A')}"

    # Generate a direct reply link to the user
    reply_to_user_link = f"tg://user?id={user.id}"
    user_profile_link = f"tg://user?id={user.id}"

    return TEXTS[lang]["user_profile_template"].format(
        full_name=user.full_name,
        user_profile_link=user_profile_link,
        country=data.get("country", "N/A"),
        region=data.get("region", "N/A"),
        city=data.get("city", "N/A"),
        gender=data.get("gender", "N/A"),
        looking_for_type=data.get("looking_for_type", "N/A"),
        partner_gender=data.get("partner_gender", "N/A"),
        partner_age=data.get("partner_age", "N/A"),
        partner_info=data.get("partner_info", "N/A"),
        characteristics=data.get("characteristics", "N/A"),
        about_me=data.get("about_me", "N/A"),
        contact=contact_info,
        reply_to_user_link=reply_to_user_link
    )


# Registering command and message handlers as per user request (admin_approve, admin_reject, admin_reply)


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
        except asyncio.CancelledError:
            pass
        finally:
            await bot.session.close()
            await dp.storage.close()
            print("Bot stopped and resources released.")


if __name__ == "__main__":
    asyncio.run(main())
