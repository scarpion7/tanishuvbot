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
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) # Bu bot e'lonlarni joylashtiradigan asosiy kanal ID'si
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
    admin_reply = State()


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
        "about_me_prompt": "O'zingiz haqida ma'lumot kiriting:",
        "contact_type_prompt": "Bog'lanish uchun qanday ma'lumot qoldirishni xohlaysiz?",
        "phone_number_prompt": "Iltimos, telefon raqamingizni kiriting (masalan, +998XXXXXXXXX):",
        "username_prompt": "Iltimos, Telegram username, Instagram linki yoki boshqa profilingizga havolani kiriting (masalan, @username yoki instagram.com/user):",
        "photo_upload_prompt": "Iltimos, profilingiz uchun rasm yuklang (yuzingiz aniq ko'rinishi shart) yoki 'Yuklamaslik' tugmasini bosing:",
        "channel_check_prompt": "Arizangizni kanalga joylashdan oldin, iltimos, quyidagi kanallarga a'zo bo'ling:",
        "not_a_member_multiple": "Siz quyidagi kanallarga a'zo emassiz:\n{missing_channels}\nIltimos, a'zo bo'lib, 'Tekshirish' tugmasini bosing.",
        "publish_consent_prompt": "Ma'lumotlaringizni kanalga chop etishimizga rozimisiz?",
        "confirm_prompt": "Ma'lumotlaringiz to'g'rimi?",
        "thank_you": "Arizangiz qabul qilindi. Tez orada kanalga joylashtiriladi.",
        "profile_template": (
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n\n"
            "<b>🚻 Jinsi:</b> {gender}\n\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n\n"
            "<b>🔢 Qidirayotgan yoshi:</b> {partner_age}\n\n"
            "<b>✨ Sherik haqida ma'lumot:</b> {partner_info}\n\n"
            "<b>📝 O'zi haqida xususiyatlari:</b> {characteristics}\n\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n\n"
            "<b>📞 Bog'lanish:</b> {contact}\n\n"
            "<a href='https://t.me/@tanishuv18plus_bot'>Manba: TopTanish</a>"
        ),
        "user_profile_link_template": "<a href='t.me/{username}'>@{username}</a>",
        "user_id_link_template": "<a href='tg://user?id={user_id}'>{user_id}</a>",
        "user_profile_template": (
            "<b>🙋‍♂️ Ism:</b> {full_name} ({user_profile_link})\n\n"
            "<b>📍 Joylashuv:</b> {country}, {region}, {city}\n\n"
            "<b>🚻 Jinsi:</b> {gender}\n\n"
            "<b>🔍 Maqsadi:</b> {looking_for_type}\n\n"
            "<b>👫 Qidirayotgan jinsi:</b> {partner_gender}\n\n"
            "<b>🔢 Qidirayotgan yoshi:</b> {partner_age}\n\n"
            "<b>✨ Sherik haqida ma'lumot:</b> {partner_info}\n\n"
            "<b>📝 O'zi haqida xususiyatlari:</b> {characteristics}\n\n"
            "<b>✍️ O'zi haqida:</b> {about_me}\n\n"
            "<b>📞 Bog'lanish:</b> {contact}\n\n"
            "Manba: <a href='https://t.me/@Tanishuv18plus_bot'> TopTanish</a>"
        ),
        "invalid_input": "Noto'g'ri kiritish. Iltimos, to'g'ri formatda kiriting.",
        "invalid_age_format": "Yoshingizni to'g'ri formatda kiriting (masalan, 25-35).",
        "invalid_characteristics": "Iltimos, xususiyatlaringizni to'g'ri formatda kiriting. Namuna: Yoshi: 25, Bo'yi: 170sm, Og'irligi: 65kg, Sportchi",
        "invalid_callback_input": "Noto'g'ri tanlov. Iltimos, inline tugma orqali tanlang.",
        "select_from_options": "Iltimos, berilgan variantlardan birini tanlang.",
        "text_too_long": "Matn juda uzun.",
        "other": "Boshqa",
        "back_button": "🔙 Orqaga",
        "skip_photo": "Yuklamaslik",
        "contact_number_only": "Faqat raqam",
        "contact_username_only": "Faqat username (link)",
        "contact_both": "Ikkalasi ham",
        "invalid_phone_number": "Noto'g'ri telefon raqami formati. Iltimos, +998XXXXXXXXX formatida kiriting.",
        "partner_info_prompt": "Qidirayotgan sherigingiz haqida qisqacha ma'lumot kiriting:",
        "admin_reply_prompt": "Foydalanuvchiga yuboriladigan javob matnini kiriting:",
        "admin_reply_sent": "Javob foydalanuvchiga yuborildi.",
        "admin_reply_error": "Javobni yuborishda xatolik yuz berdi.",
        "reply_button_text": "Javob yozish",
        "channel_links": [
            {"name": "TopTanish Rasmiy Kanali",  "url": "https://t.me/ommaviy_tanishuv_kanali", "id": -1002683172524},
            {"name": "MJM JMJ Oila tanishuv",     "url": "https://t.me/oila_ayollar_mjm_jmj_12_viloyat", "id": -1002571964009}
        ],
        "message_received_by_admin": "Xabaringiz adminlarga yuborildi. Tez orada javob olasiz.",
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
        "about_me_prompt": "Введите информацию о себе:",
        "contact_type_prompt": "Какую информацию для связи вы хотите оставить?",
        "phone_number_prompt": "Пожалуйста, введите ваш номер телефона (например, +998XXXXXXXXX):",
        "username_prompt": "Пожалуйста, введите имя пользователя Telegram, ссылку на Instagram или другую ссылку на ваш профиль (например, @username или instagram.com/user):",
        "photo_upload_prompt": "Пожалуйста, загрузите фото для вашего профиля (лицо должно быть хорошо видно) или нажмите 'Не загружать':",
        "channel_check_prompt": "Перед публикацией вашей заявки на канале, пожалуйста, подпишитесь на следующие каналы:",
        "not_a_member_multiple": "Вы не подписаны на следующие каналы:\n{missing_channels}\nПожалуйста, подпишитесь на них и нажмите кнопку 'Проверить'.",
        "publish_consent_prompt": "Вы согласны на публикацию ваших данных на канале?",
        "confirm_prompt": "Ваши данные верны?",
        "thank_you": "Ваша заявка принята. Скоро она будет размещена на канале.",
        "profile_template": (
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n\n"
            "<b>🚻 Пол:</b> {gender}\n\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n\n"
            "<b>✨ Информация о партнере:</b> {partner_info}\n\n"
            "<b>📝 О себе (характеристики):</b> {characteristics}\n\n"
            "<b>✍️ О себе:</b> {about_me}\n\n"
            "<b>📞 Контакт:</b> {contact}\n\n"
            "<a href='https://t.me/@tanishuv18plus_bot'>Источник: TopTanish</a>"
        ),
        "user_profile_link_template": "<a href='t.me/{username}'>@{username}</a>",
        "user_id_link_template": "<a href='tg://user?id={user_id}'>{user_id}</a>",
        "user_profile_template": (
            "<b>🙋‍♂️ Имя:</b> {full_name} ({user_profile_link})\n\n"
            "<b>📍 Местоположение:</b> {country}, {region}, {city}\n\n"
            "<b>🚻 Пол:</b> {gender}\n\n"
            "<b>🔍 Цель:</b> {looking_for_type}\n\n"
            "<b>👫 Искомый пол:</b> {partner_gender}\n\n"
            "<b>🔢 Искомый возраст:</b> {partner_age}\n\n"
            "<b>✨ Информация о партнере:</b> {partner_info}\n\n"
            "<b>📝 О себе (характеристики):</b> {characteristics}\n\n"
            "<b>✍️ О себе:</b> {about_me}\n\n"
            "<b>📞 Контакт:</b> {contact}\n\n"
            "Источник: <a href='https://t.me/@Tanishuv18plus_bot'> TopTanish</a>"
        ),
        "invalid_input": "Неверный ввод. Пожалуйста, введите в правильном формате.",
        "invalid_age_format": "Введите возраст в правильном формате (например, 25-35).",
        "invalid_characteristics": "Пожалуйста, введите ваши характеристики в правильном формате. Пример: Возраст: 25, Рост: 170см, Вес: 65кг, Спортсмен",
        "invalid_callback_input": "Неверный выбор. Пожалуйста, выберите с помощью встроенной кнопки.",
        "select_from_options": "Пожалуйста, выберите один из предложенных вариантов.",
        "text_too_long": "Текст слишком длинный",
        "other": "Другое",
        "back_button": "🔙 Назад",
        "skip_photo": "Не загружать",
        "contact_number_only": "Только номер",
        "contact_username_only": "Только имя пользователя (ссылка)",
        "contact_both": "И то, и другое",
        "invalid_phone_number": "Неверный формат номера телефона. Пожалуйста, введите в формате +998XXXXXXXXX.",
        "partner_info_prompt": "Введите краткую информацию о партнере, которого вы ищете:",
        "admin_reply_prompt": "Введите текст ответа, который будет отправлен пользователю:",
        "admin_reply_sent": "Ответ отправлен пользователю.",
        "admin_reply_error": "Произошла ошибка при отправке ответа.",
        "reply_button_text": "Ответить",
        "channel_links": [
            {"name": "Официальный канал TopTanish", "url": "https://t.me/ommaviy_tanishuv_kanali", "id": -1002683172524},
            {"name": "МЖМ ЖМЖ Семейные Знакомства", "url": "https://t.me/oila_ayollar_mjm_jmj_12_viloyat", "id": -1002571964009}
        ],
        "message_received_by_admin": "Ваше сообщение отправлено администраторам. Скоро вы получите ответ.",
    }
}

DEFAULT_PHOTO_URLS = {
    "male": "https://img.freepik.com/premium-vector/business-man-vector-silhouette-illustration_554682-2324.jpg",
    "female": "https://img.freepik.com/premium-photo/silhouette-beautiful-young-woman-black-lingerie_949828-10264.jpg?semt=ais_hybrid&w=740",
    "family": "https://st3.depositphotos.com/17392768/32153/i/450/depositphotos_321539808-stock-photo-man-woman-passionately-embrace-each.jpg",
    "default": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRC57QkJrIJVFfdbSyL8XWctGIcQhMmQJq9_w&s"
}

GENDER_OPTIONS = {
    "male": {"uz": "Erkak 🙋‍♂️", "ru": "Мужчина 🙋‍♂️"},
    "female": {"uz": "Ayol 🙋‍♀️", "ru": "Женщина 🙋‍♀️"},
    "family": {"uz": "Oila 👨‍👩‍👧‍👦", "ru": "Семья 👨‍👩‍👧‍👦"}
}

LOOKING_FOR_OPTIONS = {
    "intim": {"uz": "Intim/Seks munosabat 18+", "ru": "Интимные/Секс отношения 18+"},
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
    if looking_for_type_key == "intim":
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
    keyboard = []
    for channel_info in TEXTS[lang]["channel_links"]:
        keyboard.append([InlineKeyboardButton(text=channel_info["name"], url=channel_info["url"])])
    
    keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_channel_member")])
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
        [InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
    country_key = user_data.get("country_key", "uz")
    await state.set_state(Form.region)
    await callback_query.message.edit_text(TEXTS[lang]["region_prompt"],
                                           reply_markup=get_region_keyboard(lang, country_key))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_city")
async def back_to_city(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key", "uz")
    region = user_data.get("region")
    if not region or user_data.get("custom_region_entered"): # Agar foydalanuvchi avval custom region kiritgan bo'lsa
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.set_state(Form.city)
        await callback_query.message.edit_text(TEXTS[lang]["city_prompt"],
                                               reply_markup=get_city_keyboard(lang, country_key, region))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_looking_for")
async def back_to_looking_for(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.looking_for_type)
    await callback_query.message.edit_text(TEXTS[lang]["looking_for_prompt"],
                                           reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_partner_gender")
async def back_to_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_for_type_key = user_data.get("looking_for_type_key")
    await state.set_state(Form.partner_gender)
    await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"],
                                           reply_markup=get_partner_gender_keyboard(lang, looking_for_type_key))
    await callback_query.answer()


@dp.callback_query(F.data == "back_to_partner_age")
async def back_to_partner_age(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.set_state(Form.partner_age)
    await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
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

# --- END BACK BUTTON HANDLERS ---

@dp.callback_query(Form.language, F.data.startswith("lang_"))
async def process_language(callback_query: CallbackQuery, state: FSMContext):
    lang = callback_query.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(Form.gender)
    await callback_query.message.edit_text(TEXTS[lang]["gender_prompt"], reply_markup=get_gender_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(Form.gender, F.data.startswith("gender_"))
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    gender_key = callback_query.data.split("_")[1]
    await state.update_data(gender=GENDER_OPTIONS[gender_key][lang], gender_key=gender_key)
    await state.set_state(Form.country)
    await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_country_keyboard(lang))
    await callback_query.answer()


@dp.callback_query(Form.country, F.data.startswith("country_"))
async def process_country(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = callback_query.data.split("_")[1]
    selected_country_text = COUNTRIES.get(country_key, country_key)
    await state.update_data(country=selected_country_text, country_key=country_key)
    if country_key == "other":
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.set_state(Form.region)
        await callback_query.message.edit_text(TEXTS[lang]["region_prompt"], reply_markup=get_region_keyboard(lang, country_key))
    await callback_query.answer()


@dp.callback_query(Form.region, F.data.startswith("region_"))
async def process_region(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key", "uz")
    region = callback_query.data.split("_")[1]
    if region == "other":
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    else:
        await state.update_data(region=region, custom_region_entered=False) # custom_region_entered flag
        await state.set_state(Form.city)
        await callback_query.message.edit_text(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, country_key, region))
    await callback_query.answer()


@dp.message(Form.custom_region)
async def process_custom_region(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key", "uz")
    if message.text:
        await state.update_data(region=message.text, custom_region_entered=True) # custom_region_entered flag
        await state.set_state(Form.city)
        await message.answer(TEXTS[lang]["city_prompt"], reply_markup=get_city_keyboard(lang, country_key, message.text))
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
        await state.set_state(Form.looking_for_type)
        await callback_query.message.edit_text(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()


@dp.message(Form.custom_city)
async def process_custom_city(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text:
        await state.update_data(city=message.text)
        await state.set_state(Form.looking_for_type)
        await message.answer(TEXTS[lang]["looking_for_prompt"], reply_markup=get_looking_for_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["invalid_input"])


@dp.callback_query(Form.looking_for_type, F.data.startswith("looking_"))
async def process_looking_for(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    looking_for_type_key = callback_query.data.split("_")[1]
    await state.update_data(looking_for_type=LOOKING_FOR_OPTIONS[looking_for_type_key][lang], looking_for_type_key=looking_for_type_key)
    await state.set_state(Form.partner_gender)
    await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang, looking_for_type_key))
    await callback_query.answer()


@dp.callback_query(Form.partner_gender, F.data.startswith("partner_gender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_gender_key = callback_query.data.split("_")[2]
    await state.update_data(partner_gender=PARTNER_GENDER_OPTIONS[partner_gender_key][lang])
    await state.set_state(Form.partner_age)
    await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    await callback_query.answer()


@dp.message(Form.partner_age)
async def process_partner_age(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and (len(message.text.split('-')) == 2 and all(p.isdigit() for p in message.text.split('-')) or (
                message.text.endswith('+') and message.text[:-1].isdigit()) or message.text.isdigit()):
        await state.update_data(partner_age=message.text)
        await state.set_state(Form.partner_info)
        await message.answer(TEXTS[lang]["partner_info_prompt"])
    else:
        await message.answer(TEXTS[lang]["invalid_age_format"])


@dp.message(Form.partner_info)
async def process_partner_info(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and len(message.text) <= 1000:
        await state.update_data(partner_info=message.text)
        await state.set_state(Form.characteristics)
        await message.answer(TEXTS[lang]["characteristics_prompt"])
    else:
        await message.answer(TEXTS[lang]["text_too_long"])


@dp.message(Form.characteristics)
async def process_characteristics(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and len(message.text) <= 500:
        await state.update_data(characteristics=message.text)
        await state.set_state(Form.about_me)
        await message.answer(TEXTS[lang]["about_me_prompt"])
    else:
        await message.answer(TEXTS[lang]["text_too_long"])


@dp.message(Form.about_me)
async def process_about_me(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.text and len(message.text) <= 1000:
        await state.update_data(about_me=message.text)
        await state.set_state(Form.contact_type)
        await message.answer(TEXTS[lang]["contact_type_prompt"], reply_markup=get_contact_type_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["text_too_long"])


@dp.callback_query(Form.contact_type, F.data.startswith("contact_type_"))
async def process_contact_type(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    contact_type = callback_query.data.split("_")[-1]
    await state.update_data(contact_type=contact_type)

    if contact_type == "number" or contact_type == "both":
        await state.set_state(Form.phone_number)
        await callback_query.message.edit_text(TEXTS[lang]["phone_number_prompt"])
    elif contact_type == "username":
        await state.set_state(Form.username)
        await callback_query.message.edit_text(TEXTS[lang]["username_prompt"])
    await callback_query.answer()


@dp.message(Form.phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    phone_number = message.text

    if phone_number and phone_number.startswith("+") and phone_number[1:].isdigit() and len(phone_number) == 13:
        await state.update_data(phone_number=phone_number)
        if user_data.get("contact_type") == "both":
            await state.set_state(Form.username)
            await message.answer(TEXTS[lang]["username_prompt"])
        else:
            await state.set_state(Form.photo_upload)
            await message.answer(TEXTS[lang]["photo_upload_prompt"], reply_markup=get_photo_upload_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["invalid_phone_number"])


@dp.message(Form.username)
async def process_username(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    username_input = message.text
    if username_input:
        await state.update_data(username=username_input)
        await state.set_state(Form.photo_upload)
        await message.answer(TEXTS[lang]["photo_upload_prompt"], reply_markup=get_photo_upload_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["invalid_input"])


@dp.callback_query(Form.photo_upload, F.data == "skip_photo_upload")
async def skip_photo_upload(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await state.update_data(photo_id=None)
    await state.set_state(Form.channel_check)
    await callback_query.message.edit_text(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))
    await callback_query.answer()


@dp.message(Form.photo_upload, F.photo)
async def process_photo_upload(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_file_id)
    await state.set_state(Form.channel_check)
    await message.answer(TEXTS[lang]["channel_check_prompt"], reply_markup=get_channel_check_keyboard(lang))


@dp.message(Form.photo_upload)
async def handle_invalid_photo_upload(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer("Iltimos, rasm yuklang yoki 'Yuklamaslik' tugmasini bosing.", reply_markup=get_photo_upload_keyboard(lang))


@dp.callback_query(Form.channel_check, F.data == "check_channel_member")
async def check_channel_membership(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    user_id = callback_query.from_user.id
    
    missing_channels_info = []
    
    for channel_info in TEXTS[lang]["channel_links"]:
        channel_id = channel_info["id"]
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                missing_channels_info.append(channel_info["name"])
        except Exception as e:
            print(f"Error checking channel {channel_info['name']} ({channel_id}): {e}")
            missing_channels_info.append(channel_info["name"])

    if not missing_channels_info:
        await state.set_state(Form.publish_consent)
        await callback_query.message.edit_text(
            TEXTS[lang]["publish_consent_prompt"],
            reply_markup=get_publish_consent_keyboard(lang)
        )
        await callback_query.answer("Barcha kanallarga a'zo bo'ldingiz!")
    else:
        missing_channels_text = "\n".join(missing_channels_info)
        new_text = TEXTS[lang]["not_a_member_multiple"].format(missing_channels=missing_channels_text)
        current_text = callback_query.message.text
        
        if new_text == current_text and callback_query.message.reply_markup == get_channel_check_keyboard(lang):
            await callback_query.answer("Siz hali ham barcha kanallarga a'zo emassiz. Iltimos, a'zo bo'lib, qayta tekshiring.")
        else:
            await callback_query.message.edit_text(
                new_text,
                reply_markup=get_channel_check_keyboard(lang)
            )
            await callback_query.answer()


@dp.callback_query(Form.publish_consent, F.data == "consent_yes")
async def process_consent_yes(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    user_id = callback_query.from_user.id
    
    gender = user_data.get("gender")
    country = user_data.get("country")
    region = user_data.get("region")
    city = user_data.get("city")
    looking_for_type = user_data.get("looking_for_type")
    partner_gender = user_data.get("partner_gender")
    partner_age = user_data.get("partner_age")
    partner_info = user_data.get("partner_info")
    characteristics = user_data.get("characteristics")
    about_me = user_data.get("about_me")
    contact_type = user_data.get("contact_type")
    phone_number = user_data.get("phone_number")
    username = user_data.get("username")
    photo_id = user_data.get("photo_id")

    contact_info = ""
    if contact_type == "number":
        contact_info = phone_number
    elif contact_type == "username":
        if username.startswith('@'):
            contact_info = TEXTS[lang]["user_profile_link_template"].format(username=username[1:])
        else:
            contact_info = f"<a href='{username}'>{username}</a>"
    elif contact_type == "both":
        if username.startswith('@'):
            contact_info = f"{phone_number}\n{TEXTS[lang]['user_profile_link_template'].format(username=username[1:])}"
        else:
            contact_info = f"{phone_number}\n<a href='{username}'>{username}</a>"
    else:
        contact_info = TEXTS[lang]["user_id_link_template"].format(user_id=user_id)

    profile_text = TEXTS[lang]["profile_template"].format(
        country=country,
        region=region,
        city=city,
        gender=gender,
        looking_for_type=looking_for_type,
        partner_gender=partner_gender,
        partner_age=partner_age,
        partner_info=partner_info,
        characteristics=characteristics,
        about_me=about_me,
        contact=contact_info
    )

    if not photo_id:
        if gender == GENDER_OPTIONS["male"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["male"]
        elif gender == GENDER_OPTIONS["female"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["female"]
        elif gender == GENDER_OPTIONS["family"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["family"]
        else:
            photo_id = DEFAULT_PHOTO_URLS["default"]

    if photo_id and photo_id.startswith("http"):
        await callback_query.message.edit_media(
            media=types.InputMediaPhoto(media=photo_id, caption=profile_text, parse_mode=ParseMode.HTML),
            reply_markup=get_confirm_keyboard(lang)
        )
    elif photo_id:
        await callback_query.message.edit_media(
            media=types.InputMediaPhoto(media=photo_id, caption=profile_text, parse_mode=ParseMode.HTML),
            reply_markup=get_confirm_keyboard(lang)
        )
    else:
        await callback_query.message.edit_text(profile_text, reply_markup=get_confirm_keyboard(lang))

    await state.set_state(Form.confirm)
    await callback_query.answer()


@dp.callback_query(Form.publish_consent, F.data == "consent_no")
async def process_consent_no(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await callback_query.message.edit_text("Arizangiz rad etildi. Botdan foydalanishni qayta boshlash uchun /start buyrug'ini bosing.", reply_markup=None)
    await state.clear()
    await callback_query.answer()


@dp.callback_query(Form.confirm, F.data == "confirm_yes")
async def process_confirm_yes(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    user_id = callback_query.from_user.id
    
    gender = user_data.get("gender")
    country = user_data.get("country")
    region = user_data.get("region")
    city = user_data.get("city")
    looking_for_type = user_data.get("looking_for_type")
    partner_gender = user_data.get("partner_gender")
    partner_age = user_data.get("partner_age")
    partner_info = user_data.get("partner_info")
    characteristics = user_data.get("characteristics")
    about_me = user_data.get("about_me")
    contact_type = user_data.get("contact_type")
    phone_number = user_data.get("phone_number")
    username = user_data.get("username")
    photo_id = user_data.get("photo_id")
    
    contact_info = ""
    if contact_type == "number":
        contact_info = phone_number
    elif contact_type == "username":
        if username.startswith('@'):
            contact_info = TEXTS[lang]["user_profile_link_template"].format(username=username[1:])
        else:
            contact_info = f"<a href='{username}'>{username}</a>"
    elif contact_type == "both":
        if username.startswith('@'):
            contact_info = f"{phone_number}\n{TEXTS[lang]['user_profile_link_template'].format(username=username[1:])}"
        else:
            contact_info = f"{phone_number}\n<a href='{username}'>{username}</a>"
    else:
        contact_info = TEXTS[lang]["user_id_link_template"].format(user_id=user_id)


    profile_text = TEXTS[lang]["profile_template"].format(
        country=country,
        region=region,
        city=city,
        gender=gender,
        looking_for_type=looking_for_type,
        partner_gender=partner_gender,
        partner_age=partner_age,
        partner_info=partner_info,
        characteristics=characteristics,
        about_me=about_me,
        contact=contact_info
    )

    if not photo_id:
        if gender == GENDER_OPTIONS["male"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["male"]
        elif gender == GENDER_OPTIONS["female"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["female"]
        elif gender == GENDER_OPTIONS["family"][lang]:
            photo_id = DEFAULT_PHOTO_URLS["family"]
        else:
            photo_id = DEFAULT_PHOTO_URLS["default"]

    try:
        if photo_id and photo_id.startswith("http"):
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=profile_text,
                parse_mode=ParseMode.HTML
            )
        elif photo_id:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=profile_text,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=profile_text,
                parse_mode=ParseMode.HTML
            )
        
        # Foydalanuvchiga muvaffaqiyat xabarini yuborish
        await callback_query.message.edit_text(TEXTS[lang]["thank_you"], reply_markup=None) 
        await callback_query.answer() # CallbackQuery ni tugatish
        await state.clear() # Holatni tozalash
        print(f"Ariza kanalga avtomatik joylandi. Foydalanuvchi ID: {user_id}")

    except Exception as e:
        await callback_query.message.answer(TEXTS[lang]["admin_reply_error"]) # Xatolik haqida foydalanuvchiga xabar berish
        print(f"Arizani kanalga joylashda xatolik yuz berdi {user_id}: {e}")
        await callback_query.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await state.clear()


@dp.callback_query(Form.confirm, F.data == "confirm_no")
async def process_confirm_no(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await callback_query.message.edit_text("Arizangiz rad etildi. Botdan foydalanishni qayta boshlash uchun /start buyrug'ini bosing.", reply_markup=None)
    await state.clear()
    await callback_query.answer()


# Admin javob berish funksiyasi
@dp.callback_query(lambda c: c.data and c.data.startswith('admin_reply_to_user_'))
async def admin_initiate_reply(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != BOT_ADMIN_ID:
        await callback_query.answer("Siz admin emassiz!", show_alert=True)
        return

    user_to_reply_id = int(callback_query.data.split('_')[-1])
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")

    await state.update_data(user_to_reply_id=user_to_reply_id)
    await state.set_state(Form.admin_reply)
    await callback_query.message.answer(TEXTS[lang]["admin_reply_prompt"])
    await callback_query.answer()

# Adminning foydalanuvchiga javob yuborish handler'i (barcha media turlarini qo'llab-quvvatlaydi)
@dp.message(Form.admin_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_to_reply_id = user_data.get("user_to_reply_id")
    lang = user_data.get("lang", "uz")

    if user_to_reply_id:
        try:
            await bot.copy_message(
                chat_id=user_to_reply_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            await message.answer(TEXTS[lang]["admin_reply_sent"])
        except Exception as e:
            await message.answer(TEXTS[lang]["admin_reply_error"])
            print(f"Admin javobini foydalanuvchiga {user_to_reply_id} yuborishda xatolik: {e}")
    await state.clear()


@dp.message(F.content_type.in_({'photo', 'video', 'document', 'audio', 'voice', 'video_note', 'sticker', 'animation', 'text'}))
async def forward_unhandled_messages_to_admin(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if message.from_user.id != BOT_ADMIN_ID and current_state is None:
        try:
            await bot.forward_message(
                chat_id=BOT_ADMIN_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            lang = (await state.get_data()).get("lang", "uz")
            await message.answer(TEXTS[lang].get("message_received_by_admin", "Xabaringiz adminlarga yuborildi. Tez orada javob olasiz."))
        except Exception as e:
            print(f"Xabarni adminlarga yo'naltirishda xatolik: {e}")


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
