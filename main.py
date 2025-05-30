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
    proof_voice = State()
    country = State()
    region = State()
    custom_region = State()
    district = State()
    custom_district = State()
    age = State()
    looking_for_type = State()
    partner_gender = State()
    partner_age = State()
    partner_description = State()
    about_me = State()
    contact = State()
    photo = State()
    channel_check = State()
    confirm = State()

# --- Multilingual Texts ---
TEXTS = {
    "uz": {
        "start_message": "Assalomu alaykum! Arizani to'ldirish uchun tilni tanlang:",
        "gender_prompt": "Jinsingizni tanlang:",
        "gender_male": "♂️ Erkak",
        "gender_female": "♀️ Ayol",
        "gender_family": "👨‍👩‍👧‍👦 Oila",
        "proof_voice_prompt": "Jinsingizni tasdiqlash uchun quyidagi matnni ovozli xabar qilib yuboring:\n\n<b>'{proof_text}'</b>",
        "voice_received": "Rahmat, ovozli xabar qabul qilindi.",
        "invalid_voice": "Noto'g'ri format. Iltimos, ovozli xabar yuboring.",
        "country_prompt": "Qaysi davlatdansiz?",
        "region_prompt": "Qaysi viloyatdansiz?",
        "other_region_option": "✍️ Boshqa viloyat",
        "custom_region_prompt": "Iltimos, viloyatingiz nomini kiriting:",
        "district_prompt": "{region_name} viloyatining qaysi tumanidan/shahrinidansiz? (Majburiy emas)",
        "no_district_option": "❌ Tuman tanlamayman",
        "other_district_option": "✍️ Boshqa tuman/shahar",
        "custom_district_prompt": "Iltimos, tumaningiz/shaharingiz nomini kiriting:",
        "age_prompt": "Yoshingizni tanlang:",
        "looking_for_type_prompt": "Qanday munosabat istayapsiz?",
        "partner_gender_prompt": "Kimni qidiryapsiz?",
        "partner_age_prompt": "Qidirayotgan sherigingiz necha yoshgacha bo'lishini kiriting (raqam va so'zlar orqali):",
        "partner_description_prompt": "Qidirayotgan sherigingiz qanday bo'lishini istaysiz?",
        "about_me_prompt": "Iltimos, o'zingiz haqingizda ma'lumot qoldiring (kamida 50 belgi):",
        "about_me_too_short": "Ma'lumot kamida 50 belgidan iborat bo'lishi kerak. Iltimos, to'liqroq yozing.",
        "contact_prompt": "Bog'lanish uchun raqamingizni (masalan: +998XXYYYYYYY) yoki telegram username'ingizni (masalan: @username) qoldiring:",
        "photo_prompt": "Iltimos, profilingiz uchun rasm yuboring (majburiy):",
        "invalid_photo": "Iltimos, rasm yuboring.",
        "channel_check_prompt": "Iltimos, arizangiz tasdiqlanishidan oldin quyidagi kanalimizga a'zo bo'ling: {channel_link}\n\nKanalga a'zo bo'lganingizdan so'ng, 'A'zolikni tekshirish' tugmasini bosing.", # NEW
        "channel_check_button": "✅ A'zolikni tekshirish", # NEW
        "not_a_member": "Siz kanalga a'zo emassiz yoki a'zolikni tekshirishda xatolik yuz berdi. Iltimos, kanalga a'zo bo'lib, qayta urinib ko'ring.", # NEW
        "membership_verified": "A'zoligingiz tasdiqlandi. Arizangizni tasdiqlashingiz mumkin.", # NEW
        "confirm_prompt": "Yuqoridagi ma'lumotlar to'g'rimi? Tasdiqlasangiz, arizangiz kanalda e'lon qilinadi.",
        "confirm_yes": "✅ Tasdiqlayman",
        "confirm_no": "✏️ Qayta kiritish",
        "application_accepted": "Arizangiz qabul qilindi va kanalda e'lon qilindi. Rahmat!",
        "application_error": "Arizani e'lon qilishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "application_cancelled": "Arizangiz bekor qilindi. Qayta to'ldirish uchun /start buyrug'ini bosing.",
        "back_button": "⬅️ Orqaga",
        "invalid_callback_input": "Iltimos, inline tugmalar orqali tanlov qiling yoki orqaga qaytish tugmasidan foydalaning.",
        "unknown": "Noma'lum",
        "not_selected": "Tanlanmagan",
        "not_entered": "Kiritilmagan",
        "application_summary_title": "<b>Sizning arizangiz:</b>\n\n",
        "gender_label": "Jins:",
        "country_label": "Davlat:",
        "region_label": "Viloyat:",
        "district_label": "Tuman/Shahar:",
        "age_label": "Yosh:",
        "looking_for_type_label": "Munosabat turi:",
        "partner_gender_label": "Qidirayotgan jins:",
        "partner_age_label": "Sherik yoshi:",
        "partner_description_label": "Sherik haqida:",
        "about_me_label": "O'zi haqida:",
        "contact_label": "Bog'lanish:",
        "new_application_title": "<b>Yangi ariza!</b>\n\n",
        "user_label": "Foydalanuvchi:",
    },
    "ru": {
        "start_message": "Здравствуйте! Выберите язык для заполнения анкеты:",
        "gender_prompt": "Выберите ваш пол:",
        "gender_male": "♂️ Мужчина",
        "gender_female": "♀️ Женщина",
        "gender_family": "👨‍👩‍👧‍👦 Семья",
        "proof_voice_prompt": "Для подтверждения вашего пола отправьте следующее сообщение голосовым сообщением:\n\n<b>'{proof_text}'</b>",
        "voice_received": "Спасибо, голосовое сообщение получено.",
        "invalid_voice": "Неверный формат. Пожалуйста, отправьте голосовое сообщение.",
        "country_prompt": "Из какой вы страны?",
        "region_prompt": "Из какой вы области/региона?",
        "other_region_option": "✍️ Другая область",
        "custom_region_prompt": "Пожалуйста, введите название вашей области:",
        "district_prompt": "Из какого вы района/города {region_name} области? (Необязательно)",
        "no_district_option": "❌ Не выбирать район",
        "other_district_option": "✍️ Другой район/город",
        "custom_district_prompt": "Пожалуйста, введите название вашего района/города:",
        "age_prompt": "Выберите ваш возраст:",
        "looking_for_type_prompt": "Какие отношения вы ищете?",
        "partner_gender_prompt": "Кого вы ищете?",
        "partner_age_prompt": "Укажите до какого возраста должен быть ваш партнер (цифрами и словами):",
        "partner_description_prompt": "Каким вы хотите видеть своего партнера?",
        "about_me_prompt": "Пожалуйста, оставьте информацию о себе (минимум 50 символов):",
        "about_me_too_short": "Информация должна содержать не менее 50 символов. Пожалуйста, напишите подробнее.",
        "contact_prompt": "Оставьте свой номер телефона (например: +998XXYYYYYYY) или имя пользователя Telegram (например: @username) для связи:",
        "photo_prompt": "Пожалуйста, отправьте фотографию для вашего профиля (обязательно):",
        "channel_check_prompt": "Пожалуйста, присоединитесь к нашему каналу перед подтверждением заявки: {channel_link}\n\nПосле присоединения, нажмите кнопку 'Проверить членство'.", # NEW
        "channel_check_button": "✅ Проверить членство", # NEW
        "not_a_member": "Вы не являетесь участником канала или произошла ошибка при проверке. Пожалуйста, присоединитесь к каналу и попробуйте снова.", # NEW
        "membership_verified": "Ваше членство подтверждено. Вы можете подтвердить свою заявку.", # NEW
        "invalid_photo": "Пожалуйста, отправьте фотографию.",
        "confirm_prompt": "Верны ли вышеуказанные данные? Если вы подтвердите, ваша заявка будет опубликована в канале.",
        "confirm_yes": "✅ Подтверждаю",
        "confirm_no": "✏️ Ввести заново",
        "application_accepted": "Ваша заявка принята и опубликована в канале. Спасибо!",
        "application_error": "Произошла ошибка при публикации заявки. Пожалуйста, попробуйте позже.",
        "application_cancelled": "Ваша заявка отменена. Чтобы заполнить заново, нажмите /start.",
        "back_button": "⬅️ Назад",
        "invalid_callback_input": "Пожалуйста, выберите с помощью инлайн-кнопок или используйте кнопку 'Назад'.",
        "unknown": "Неизвестно",
        "not_selected": "Не выбрано",
        "not_entered": "Не введено",
        "application_summary_title": "<b>Ваша заявка:</b>\n\n",
        "gender_label": "Пол:",
        "country_label": "Страна:",
        "region_label": "Регион:",
        "district_label": "Район/Город:",
        "age_label": "Возраст:",
        "looking_for_type_label": "Тип отношений:",
        "partner_gender_label": "Искомый пол:",
        "partner_age_label": "Возраст партнера:",
        "partner_description_label": "О партнере:",
        "about_me_label": "О себе:",
        "contact_label": "Контакт:",
        "new_application_title": "<b>Новая заявка!</b>\n\n",
        "user_label": "Пользователь:",
    },
    "en": {
        "start_message": "Hello! Please select a language to fill out the application:",
        "gender_prompt": "Select your gender:",
        "gender_male": "♂️ Male",
        "gender_female": "♀️ Female",
        "gender_family": "👨‍👩‍👧‍👦 Family",
        "proof_voice_prompt": "To confirm your gender, send the following text as a voice message:\n\n<b>'{proof_text}'</b>",
        "voice_received": "Thank you, voice message received.",
        "invalid_voice": "Invalid format. Please send a voice message.",
        "country_prompt": "Which country are you from?",
        "region_prompt": "Which region are you from?",
        "other_region_option": "✍️ Other region",
        "custom_region_prompt": "Please enter the name of your region:",
        "district_prompt": "Which district/city of {region_name} region are you from? (Optional)",
        "no_district_option": "❌ Do not select a district",
        "other_district_option": "✍️ Other district/city",
        "custom_district_prompt": "Please enter the name of your district/city:",
        "age_prompt": "Select your age:",
        "looking_for_type_prompt": "What kind of relationship are you looking for?",
        "partner_gender_prompt": "Who are you looking for?",
        "partner_age_prompt": "Enter the desired age range for your partner (in numbers and words):",
        "partner_description_prompt": "What kind of partner are you looking for?",
        "about_me_prompt": "Please leave information about yourself (at least 50 characters):",
        "about_me_too_short": "Information must be at least 50 characters long. Please write more completely.",
        "contact_prompt": "Leave your phone number (e.g., +998XXYYYYYYY) or Telegram username (e.g., @username) for contact:",
        "photo_prompt": "Please send a photo for your profile (mandatory):",
        "channel_check_prompt": "Please join our channel before confirming your application: {channel_link}\n\nAfter joining, click the 'Check Membership' button.", # NEW
        "channel_check_button": "✅ Check Membership", # NEW
        "not_a_member": "You are not a member of the channel or an error occurred during checking. Please join the channel and try again.", # NEW
        "membership_verified": "Your membership has been verified. You can now confirm your application.", # NEW
        "invalid_photo": "Please send a photo.",
        "confirm_prompt": "Is the above information correct? If you confirm, your application will be published on the channel.",
        "confirm_yes": "✅ Confirm",
        "confirm_no": "✏️ Re-enter",
        "application_accepted": "Your application has been accepted and published on the channel. Thank you!",
        "application_error": "An error occurred while publishing the application. Please try again later.",
        "application_cancelled": "Your application has been cancelled. To fill it out again, type /start.",
        "back_button": "⬅️ Back",
        "invalid_callback_input": "Please select using the inline buttons or use the 'Back' button.",
        "unknown": "Unknown",
        "not_selected": "Not selected",
        "not_entered": "Not entered",
        "application_summary_title": "<b>Your application:</b>\n\n",
        "gender_label": "Gender:",
        "country_label": "Country:",
        "region_label": "Region:",
        "district_label": "District/City:",
        "age_label": "Age:",
        "looking_for_type_label": "Relationship Type:",
        "partner_gender_label": "Looking for gender:",
        "partner_age_label": "Partner age:",
        "partner_description_label": "About partner:",
        "about_me_label": "About me:",
        "contact_label": "Contact:",
        "new_application_title": "<b>New application!</b>\n\n",
        "user_label": "User:",
    }
}

# --- Countries, Regions, and Districts ---
# Expanded data structure (truncated for brevity, assume full data is present)
COUNTRIES = {
    "uzbekistan": {
        "name_uz": "O'zbekiston", "name_ru": "Узбекистан", "name_en": "Uzbekistan",
        "regions": {
            "tashkent": {"name_uz": "Toshkent", "name_ru": "Ташкент", "name_en": "Tashkent", "districts_uz": ["Bekobod", "Bo‘ka", "Ohangaron", "Oqqo‘rg‘on", "Chinoz", "Qibray", "Quyichirchiq", "Toshkent tumani", "Yangiyo‘l", "Zangiota", "Bekobod shahar", "Ohangaron shahar", "Yangiyo‘l shahar"], "districts_ru": ["Бекабад", "Бука", "Ахангаран", "Аккурган", "Чиноз", "Кибрай", "Куйичирчик", "Ташкентский район", "Янгиюль", "Зангиата", "Город Бекабад", "Город Ахангаран", "Город Янгиюль"], "districts_en": ["Bekabad", "Buka", "Ahangaran", "Akkuorgan", "Chinoz", "Kibray", "Kuyichirchik", "Tashkent district", "Yangiyul", "Zangiata", "Bekabad city", "Ahangaran city", "Yangiyul city"]},
            "samarkand": {"name_uz": "Samarqand", "name_ru": "Самарканд", "name_en": "Samarkand", "districts_uz": ["Samarqand shahar", "Bulung‘ur", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod", "Oqdaryo", "Payariq", "Pastdarg‘om", "Paxtachi", "Qo‘shrabot", "Samarqand tumani", "Toyloq"], "districts_ru": ["Город Самарканд", "Булунгур", "Джамбай", "Каттакурган", "Нарпай", "Нуробод", "Акдарья", "Пайарик", "Пастдаргом", "Пахтачи", "Кошрабад", "Самаркандский район", "Тайлак"], "districts_en": ["Samarkand city", "Bulungur", "Jomboy", "Kattakurgan", "Narpay", "Nurobod", "Akdarya", "Payariq", "Pastdargom", "Pakhtachi", "Koshrobot", "Samarkand district", "Tayloq"]},
            "bukhara": {"name_uz": "Buxoro", "name_ru": "Бухара", "name_en": "Bukhara", "districts_uz": ["Buxoro shahar", "Buxoro tumani", "G‘ijduvon", "Jondor", "Kogon", "Qorako‘l", "Olot", "Peshku", "Romitan", "Shofirkon", "Vobkent"], "districts_ru": ["Город Бухара", "Бухарский район", "Гиждуван", "Жондор", "Каган", "Каракуль", "Алат", "Пешку", "Ромитан", "Шафиркан", "Вабкент"], "districts_en": ["Bukhara city", "Bukhara district", "Gijduvan", "Jondor", "Kogon", "Karakul", "Olot", "Peshku", "Romitan", "Shofirkon", "Vobkent"]},
            "andijan": {"name_uz": "Andijon", "name_ru": "Андижан", "name_en": "Andijan", "districts_uz": ["Andijon shahar", "Asaka", "Baliqchi", "Bo‘ston", "Izboskan", "Qo‘rg‘ontepa", "Shahrixon", "Ulug‘nor", "Xo‘jaobod", "Yuzboshilar", "Hokim"], "districts_ru": ["Город Андижан", "Асака", "Балыкчи", "Бустан", "Избаскан", "Кургантепа", "Шахрихан", "Улугнар", "Ходжаабад", "Юзбошилар", "Хоким"], "districts_en": ["Andijan city", "Asaka", "Baliqchi", "Boʻston", "Izboskan", "Qoʻrgʻontepa", "Shahrixon", "Ulugʻnor", "Xoʻjaobod", "Yuzboshilar", "Hokim"]},
            "fergana": {"name_uz": "Farg'ona", "name_ru": "Фергана", "name_en": "Fergana", "districts_uz": ["Farg'ona shahar", "Farg'ona tumani", "Beshariq", "Bog‘dod", "Buvayda", "Dang‘ara", "Qo‘qon", "Quva", "Rishton", "Rishton tumani", "Toshloq", "Oltiariq", "Quvasoy shahar"], "districts_ru": ["Город Фергана", "Ферганский район", "Бешарык", "Багдад", "Бувайда", "Дангара", "Коканд", "Кува", "Риштан", "Риштанский район", "Ташлак", "Алтыарык", "Город Кувасай"], "districts_en": ["Fergana city", "Fergana district", "Besharik", "Bog'dod", "Buvayda", "Dang'ara", "Kokand", "Quva", "Rishton", "Rishton district", "Toshloq", "Oltiariq", "Quvasoy city"]},
            "namangan": {"name_uz": "Namangan", "name_ru": "Наманган", "name_en": "Namangan", "districts_uz": ["Namangan shahar", "Chust", "Kosonsoy", "Mingbuloq", "Namangan tumani", "Pop", "To‘raqo‘rg‘on", "Uychi", "Yangiqo‘rg‘on"], "districts_ru": ["Город Наманган", "Чуст", "Касансай", "Мингбулак", "Наманганский район", "Пап", "Туракурган", "Уйчи", "Янгикурган"], "districts_en": ["Namangan city", "Chust", "Kosonsoy", "Mingbuloq", "Namangan district", "Pop", "To'raqo'rg'on", "Uychi", "Yangiqo'rg'on"]},
            "sirdaryo": {"name_uz": "Sirdaryo", "name_ru": "Сырдарья", "name_en": "Sirdaryo", "districts_uz": ["Guliston shahar", "Boyovut", "Guliston tumani", "Mirzaobod", "Oqoltin", "Sayxunobod", "Sardoba", "Sirdaryo tumani", "Xovos"], "districts_ru": ["Город Гулистан", "Баяут", "Гулистанский район", "Мирзаабад", "Околтин", "Сайхунабад", "Сардоба", "Сырдарьинский район", "Ховос"], "districts_en": ["Guliston city", "Boyovut", "Guliston district", "Mirzaobod", "Oqoltin", "Sayxunobod", "Sardoba", "Sirdaryo district", "Xovos"]},
            "jizzakh": {"name_uz": "Jizzax", "name_ru": "Джизак", "name_en": "Jizzakh", "districts_uz": ["Jizzax shahar", "Arnasoy", "Baxmal", "Dashtobod", "Forish", "G‘allaorol", "Zarbdor", "Zomin", "Mirzacho‘l", "Paxtakor", "Sharof Rashidov"], "districts_ru": ["Город Джизак", "Арнасай", "Бахмал", "Даштабад", "Фориш", "Галляарал", "Зарбдор", "Замин", "Мирзачуль", "Пахтакор", "Шароф Рашидов"], "districts_en": ["Jizzakh city", "Arnasoy", "Baxmal", "Dashtobod", "Forish", "G'allaorol", "Zarbdor", "Zomin", "Mirzacho'l", "Pakhtakor", "Sharof Rashidov"]},
            "kashkadarya": {"name_uz": "Qashqadaryo", "name_ru": "Кашкадарья", "name_en": "Kashkadarya", "districts_uz": ["Qarshi shahar", "Chiroqchi", "G‘uzor", "Dehqonobod", "Koson", "Kitob", "Mirishkor", "Muborak", "Nishon", "Qarshi tumani", "Shahrisabz", "Yakkabog‘"], "districts_ru": ["Город Карши", "Чирокчи", "Гузар", "Дехканабад", "Касан", "Китаб", "Миришкор", "Мубарек", "Нишон", "Каршинский район", "Шахрисабз", "Яккабаг"], "districts_en": ["Qarshi city", "Chiroqchi", "G'uzor", "Dehqonobod", "Koson", "Kitob", "Mirishkor", "Muborak", "Nishon", "Qarshi district", "Shahrisabz", "Yakkabog'"]},
            "surkhandarya": {"name_uz": "Surxondaryo", "name_ru": "Сурхандарья", "name_en": "Surkhandarya", "districts_uz": ["Termiz shahar", "Angor", "Boysun", "Denov", "Jarqo‘rg‘on", "Muzrabot", "Sariosiyo", "Sherobod", "Sho‘rchi", "Termiz tumani"], "districts_ru": ["Город Термез", "Ангор", "Байсун", "Денау", "Джаркурган", "Музрабад", "Сариасия", "Шерабад", "Шурчи", "Термезский район"], "districts_en": ["Termiz city", "Angor", "Boysun", "Denov", "Jarqo'rg'on", "Muzrabot", "Sariosiyo", "Sherobod", "Sho'rchi", "Termiz district"]},
            "navoi": {"name_uz": "Navoiy", "name_ru": "Навои", "name_en": "Navoiy", "districts_uz": ["Navoiy shahar", "Karmana", "Konimex", "Navbahor", "Nurota", "Tomdi", "Uchquduq", "Xatirchi"], "districts_ru": ["Город Навои", "Кармана", "Канимех", "Навбахор", "Нурата", "Тамды", "Учкудук", "Хатирчи"], "districts_en": ["Navoiy city", "Karmana", "Konimex", "Navbahor", "Nurota", "Tomdi", "Uchquduq", "Xatirchi"]},
            "khorezm": {"name_uz": "Xorazm", "name_ru": "Хорезм", "name_en": "Khorezm", "districts_uz": ["Urganch shahar", "Bog‘ot", "Gurlan", "Xiva shahar", "Qo‘shko‘pir", "Shovot", "Urganch tumani", "Xonqa", "Yangiariq"], "districts_ru": ["Город Ургенч", "Багат", "Гурлен", "Город Хива", "Кошкупыр", "Шават", "Ургенчский район", "Ханка", "Янгиарик"], "districts_en": ["Urganch city", "Bog'ot", "Gurlan", "Khiva city", "Qo'shko'pir", "Shovot", "Urganch district", "Xonqa", "Yangiariq"]},
            "karakalpakstan": {"name_uz": "Qoraqalpog'iston", "name_ru": "Каракалпакстан", "name_en": "Karakalpakstan", "districts_uz": ["Nukus shahar", "Amudaryo", "Beruniy", "Bo‘zatov", "Kegayli", "Qonliko‘l", "Qo‘ng‘irot", "Qorao‘zak", "Shumanay", "Taxtako‘pir", "To‘rtko‘l", "Xo‘jayli", "Chimboy", "Mo‘ynoq", "Ellikqal‘a"], "districts_ru": ["Город Нукус", "Амударья", "Беруни", "Бозатау", "Кегейли", "Канлыкуль", "Кунград", "Караузяк", "Шуманай", "Тахтакупыр", "Турткуль", "Ходжейли", "Чимбай", "Муйнак", "Элликкала"], "districts_en": ["Nukus city", "Amudaryo", "Beruniy", "Bo'zatov", "Kegayli", "Qonliko'l", "Qo'ng'irot", "Qorao'zak", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli", "Chimboy", "Mo'ynoq", "Ellikqal'a"]},
        }
    },
    "russia": {
        "name_uz": "Rossiya", "name_ru": "Россия", "name_en": "Russia",
        "regions": {
            "moscow": {"name_uz": "Moskva", "name_ru": "Москва", "name_en": "Moscow", "districts_uz": [], "districts_ru": [], "districts_en": []},
            "saint_petersburg": {"name_uz": "Sankt-Peterburg", "name_ru": "Санкт-Петербург", "name_en": "Saint Petersburg", "districts_uz": [], "districts_ru": [], "districts_en": []},
        }
    },
    "kazakhstan": {
        "name_uz": "Qozog'iston", "name_ru": "Казахстан", "name_en": "Kazakhstan",
        "regions": {
            "almaty_oblast": {"name_uz": "Olmaota viloyati", "name_ru": "Алматинская область", "name_en": "Almaty Oblast", "districts_uz": ["Almati", "Talgar", "Esik"], "districts_ru": ["Алматы", "Талгар", "Есик"], "districts_en": ["Almaty", "Talgar", "Esik"]},
            "astana": {"name_uz": "Ostona", "name_ru": "Астана", "name_en": "Astana", "districts_uz": ["Almati tumani", "Sariarka tumani"], "districts_ru": ["Район Алматы", "Район Сарыарка"], "districts_en": ["Almaty District", "Saryarka District"]},
        }
    },
    "kyrgyzstan": {
        "name_uz": "Qirg'iziston", "name_ru": "Кыргызстан", "name_en": "Kyrgyzstan",
        "regions": {
            "chuy_oblast": {"name_uz": "Chuy viloyati", "name_ru": "Чуйская область", "name_en": "Chuy Oblast", "districts_uz": ["Bishkek", "Kant"], "districts_ru": ["Бишкек", "Кант"], "districts_en": ["Bishkek", "Kant"]},
        }
    },
    "tajikistan": {
        "name_uz": "Tojikiston", "name_ru": "Таджикистан", "name_en": "Tajikistan",
        "regions": {
            "sughd_oblast": {"name_uz": "So'g'd viloyati", "name_ru": "Согдийская область", "name_en": "Sughd Oblast", "districts_uz": ["Xo'jand", "Istaravshan"], "districts_ru": ["Худжанд", "Истаравшан"], "districts_en": ["Khujand", "Istaravshan"]},
        }
    },
    "turkmenistan": {
        "name_uz": "Turkmaniston", "name_ru": "Туркменистан", "name_en": "Turkmenistan",
        "regions": {
            "ahal_velayat": {"name_uz": "Ahal viloyati", "name_ru": "Ахалский велаят", "name_en": "Ahal Province", "districts_uz": [], "districts_ru": [], "districts_en": []},
        }
    },
}

# --- Age, Looking For, Partner Gender Options (assumed from context) ---
AGE_OPTIONS = {
    "18-25": "18-25",
    "26-35": "26-35",
    "36-45": "36-45",
    "46-55": "46-55",
    "55+": "55+",
}

LOOKING_FOR_OPTIONS = {
    "serious_relationship": {"uz": "Jiddiy munosabat", "ru": "Серьезные отношения", "en": "Serious relationship"},
    "marriage": {"uz": "Nikoh", "ru": "Брак", "en": "Marriage"},
    "friendship": {"uz": "Do'stlik", "ru": "Дружба", "en": "Friendship"},
    "just_chat": {"uz": "Faqat suhbat", "ru": "Просто общение", "en": "Just chat"},
}

PARTNER_GENDER_OPTIONS = {
    "male": {"uz": "♂️ Erkak", "ru": "♂️ Мужчина", "en": "♂️ Male"},
    "female": {"uz": "♀️ Ayol", "ru": "♀️ Женщина", "en": "♀️ Female"},
    "any": {"uz": "Farqi yo'q", "ru": "Неважно", "en": "Any"},
}



# --- Keyboard Generation Functions (assumed from context and adjusted) ---
def get_back_button(target_state_name: str, lang: str):
    return InlineKeyboardButton(text=TEXTS[lang]["back_button"], callback_data=f"back_to_{target_state_name}")

def get_language_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_gender_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton(text=TEXTS[lang]["gender_male"], callback_data="gender_male")],
        [InlineKeyboardButton(text=TEXTS[lang]["gender_female"], callback_data="gender_female")],
        [InlineKeyboardButton(text=TEXTS[lang]["gender_family"], callback_data="gender_family")],
        [get_back_button("language", lang)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_countries_keyboard(lang: str):
    buttons = []
    for key, value in COUNTRIES.items():
        buttons.append([InlineKeyboardButton(text=value[f"name_{lang}"], callback_data=f"country_{key}")])
    buttons.append([get_back_button("gender", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_regions_keyboard(country_key: str, lang: str):
    buttons = []
    if country_key in COUNTRIES:
        for key, value in COUNTRIES[country_key]["regions"].items():
            buttons.append([InlineKeyboardButton(text=value[f"name_{lang}"], callback_data=f"region_{key}")])
        buttons.append([InlineKeyboardButton(text=TEXTS[lang]["other_region_option"], callback_data="region_other")])
    buttons.append([get_back_button("country", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_districts_keyboard(country_key: str, region_key: str, lang: str):
    buttons = []
    # If a custom region was entered, we don't have predefined districts for it
    if region_key == "custom":
        buttons.append([InlineKeyboardButton(text=TEXTS[lang]["no_district_option"], callback_data="district_none")])
        buttons.append([InlineKeyboardButton(text=TEXTS[lang]["other_district_option"], callback_data="district_other")])
    elif country_key in COUNTRIES and region_key in COUNTRIES[country_key]["regions"]:
        districts = COUNTRIES[country_key]["regions"][region_key][f"districts_{lang}"]
        for district in districts:
            buttons.append([InlineKeyboardButton(text=district, callback_data=f"district_{district}")])
        buttons.append([InlineKeyboardButton(text=TEXTS[lang]["no_district_option"], callback_data="district_none")])
        buttons.append([InlineKeyboardButton(text=TEXTS[lang]["other_district_option"], callback_data="district_other")])
    buttons.append([get_back_button("region", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_age_keyboard(lang: str):
    buttons = []
    for key in AGE_OPTIONS:
        buttons.append([InlineKeyboardButton(text=AGE_OPTIONS[key], callback_data=f"age_{key}")])
    buttons.append([get_back_button("district", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_looking_for_keyboard(lang: str):
    buttons = []
    for key, value in LOOKING_FOR_OPTIONS.items():
        buttons.append([InlineKeyboardButton(text=value[lang], callback_data=f"looking_{key}")])
    buttons.append([get_back_button("age", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_partner_gender_keyboard(lang: str):
    buttons = []
    for key, value in PARTNER_GENDER_OPTIONS.items():
        buttons.append([InlineKeyboardButton(text=value[lang], callback_data=f"pgender_{key}")])
    buttons.append([get_back_button("looking_for_type", lang)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard(lang: str):
    buttons = [
        [InlineKeyboardButton(text=TEXTS[lang]["confirm_yes"], callback_data="confirm_yes")],
        [InlineKeyboardButton(text=TEXTS[lang]["confirm_no"], callback_data="confirm_no")],
        [get_back_button("channel_check", lang)] # Changed back button target
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Utility Functions ---
def generate_random_proof_text(lang: str) -> str:
    """Generates a random text for voice proof."""
    phrases = {
        "uz": [
            "Men bot orqali ariza to'ldirmoqdaman.",
            "Bu mening haqiqiy ovozim.",
            "Men shaxsiy ma'lumotlarimni tasdiqlayman."
        ],
        "ru": [
            "Я заполняю анкету через бота.",
            "Это мой настоящий голос.",
            "Я подтверждаю свои личные данные."
        ],
        "en": [
            "I am filling out an application through the bot.",
            "This is my real voice.",
            "I confirm my personal data."
        ]
    }
    return random.choice(phrases[lang])

async def generate_summary_message(user_data: dict, lang: str) -> str:
    """Generates a summary message of the user's application."""
    gender_display = TEXTS[lang].get(f"gender_{user_data.get('gender', 'unknown')}", TEXTS[lang]["unknown"])
    country_display = user_data.get("country_name", TEXTS[lang]["not_selected"])
    region_display = user_data.get("region_name", TEXTS[lang]["not_selected"])
    district_display = user_data.get("district_name", TEXTS[lang]["not_selected"])
    age_display = user_data.get("age", TEXTS[lang]["not_entered"])
    looking_for_type_display = user_data.get("looking_for_type", TEXTS[lang]["not_selected"])
    partner_gender_display = user_data.get("partner_gender", TEXTS[lang]["not_selected"])
    partner_age_display = user_data.get("partner_age", TEXTS[lang]["not_entered"])
    partner_description_display = user_data.get("partner_description", TEXTS[lang]["not_entered"])
    about_me_display = user_data.get("about_me", TEXTS[lang]["not_entered"])
    contact_display = user_data.get("contact", TEXTS[lang]["not_entered"])

    summary_message = (
        f"{TEXTS[lang]['application_summary_title']}"
        f"<b>{TEXTS[lang]['gender_label']}</b> {gender_display}\n"
        f"<b>{TEXTS[lang]['country_label']}</b> {country_display}\n"
        f"<b>{TEXTS[lang]['region_label']}</b> {region_display}\n"
        f"<b>{TEXTS[lang]['district_label']}</b> {district_display}\n"
        f"<b>{TEXTS[lang]['age_label']}</b> {age_display}\n"
        f"<b>{TEXTS[lang]['looking_for_type_label']}</b> {looking_for_type_display}\n"
        f"<b>{TEXTS[lang]['partner_gender_label']}</b> {partner_gender_display}\n"
        f"<b>{TEXTS[lang]['partner_age_label']}</b> {partner_age_display}\n"
        f"<b>{TEXTS[lang]['partner_description_label']}</b> {partner_description_display}\n"
        f"<b>{TEXTS[lang]['about_me_label']}</b> {about_me_display}\n"
        f"<b>{TEXTS[lang]['contact_label']}</b> {contact_display}\n\n"
        f"{TEXTS[lang]['confirm_prompt']}"
    )
    return summary_message

# --- Bot Initialization ---
dp = Dispatcher(storage=MemoryStorage())  # Yangi usulda dispatcher yaratish

# --- Handlers ---
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Handle /start command."""
    await state.clear()
    await state.set_state(Form.language)
    await message.answer(TEXTS["uz"]["start_message"], reply_markup=get_language_keyboard())

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
    await state.update_data(gender=gender_key)

    if gender_key in ["male", "female"]:
        proof_text = generate_random_proof_text(lang)
        await state.update_data(proof_text=proof_text)
        await state.set_state(Form.proof_voice)
        await callback_query.message.edit_text(TEXTS[lang]["proof_voice_prompt"].format(proof_text=proof_text))
    else: # family
        await state.set_state(Form.country)
        await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_countries_keyboard(lang))
    await callback_query.answer()

@dp.message(Form.proof_voice, F.content_type == types.ContentType.VOICE)
async def process_proof_voice(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    if message.voice:
        await state.set_state(Form.country)
        await message.answer(TEXTS[lang]["voice_received"], reply_markup=get_countries_keyboard(lang))
    else:
        await message.answer(TEXTS[lang]["invalid_voice"])

@dp.message(Form.proof_voice)
async def process_proof_voice_invalid(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["invalid_voice"])

@dp.callback_query(Form.country, F.data.startswith("country_"))
async def process_country(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = callback_query.data.split("_")[1]
    if country_key in COUNTRIES:
        await state.update_data(country_key=country_key, country_name=COUNTRIES[country_key][f"name_{lang}"])
        await state.set_state(Form.region)
        await callback_query.message.edit_text(
            TEXTS[lang]["region_prompt"],
            reply_markup=get_regions_keyboard(country_key, lang)
        )
    else:
        await callback_query.message.edit_text(
            TEXTS[lang]["invalid_callback_input"],
            reply_markup=get_countries_keyboard(lang)
        )
    await callback_query.answer()

@dp.callback_query(Form.region, F.data.startswith("region_"))
async def process_region(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    country_key = user_data.get("country_key")
    region_key = callback_query.data.split("_")[1]

    if region_key == "other": # Handle "Other region" selection
        await state.set_state(Form.custom_region)
        await callback_query.message.edit_text(TEXTS[lang]["custom_region_prompt"])
    elif country_key in COUNTRIES and region_key in COUNTRIES[country_key]["regions"]:
        await state.update_data(region_key=region_key, region_name=COUNTRIES[country_key]["regions"][region_key][f"name_{lang}"])
        await state.set_state(Form.district)
        current_region_name = user_data.get("region_name", TEXTS[lang]["not_selected"])
        await callback_query.message.edit_text(
            TEXTS[lang]["district_prompt"].format(region_name=current_region_name),
            reply_markup=get_districts_keyboard(country_key, region_key, lang)
        )
    else:
        await callback_query.message.edit_text(
            TEXTS[lang]["invalid_callback_input"],
            reply_markup=get_regions_keyboard(country_key, lang)
        )
    await callback_query.answer()

@dp.message(Form.custom_region, F.text) # NEW HANDLER FOR CUSTOM REGION INPUT
async def process_custom_region(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    custom_region_name = message.text
    await state.update_data(region_name=custom_region_name, region_key="custom")
    await state.set_state(Form.district)
    selected_country_key = user_data.get("country_key")
    current_region_name = user_data.get("region_name", TEXTS[lang]["not_selected"])
    await message.answer(
        TEXTS[lang]["district_prompt"].format(region_name=current_region_name),
        reply_markup=get_districts_keyboard(selected_country_key, "custom", lang)
    )

@dp.callback_query(Form.district, F.data.startswith("district_"))
async def process_district(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    district_key = callback_query.data.split("_")[1]

    if district_key == "other": # Handle "Other district/city" selection
        await state.set_state(Form.custom_district)
        await callback_query.message.edit_text(TEXTS[lang]["custom_district_prompt"])
    elif district_key == "none":
        await state.update_data(district_name=TEXTS[lang]["not_selected"], district_key="none")
        await state.set_state(Form.age)
        await callback_query.message.edit_text(TEXTS[lang]["age_prompt"], reply_markup=get_age_keyboard(lang))
    else:
        await state.update_data(district_name=district_key, district_key=district_key)
        await state.set_state(Form.age)
        await callback_query.message.edit_text(TEXTS[lang]["age_prompt"], reply_markup=get_age_keyboard(lang))
    await callback_query.answer()

@dp.message(Form.custom_district, F.text) # NEW HANDLER FOR CUSTOM DISTRICT INPUT
async def process_custom_district(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    custom_district_name = message.text
    await state.update_data(district_name=custom_district_name, district_key="custom")
    await state.set_state(Form.age)
    await message.answer(TEXTS[lang]["age_prompt"], reply_markup=get_age_keyboard(lang))

@dp.callback_query(Form.age, F.data.startswith("age_"))
async def process_age(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    age = callback_query.data.split("_")[1]
    if age in AGE_OPTIONS:
        await state.update_data(age=AGE_OPTIONS[age])
        await state.set_state(Form.looking_for_type)
        await callback_query.message.edit_text(TEXTS[lang]["looking_for_type_prompt"], reply_markup=get_looking_for_keyboard(lang))
    else:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_age_keyboard(lang))
    await callback_query.answer()

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
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_looking_for_keyboard(lang))
    await callback_query.answer()

@dp.callback_query(Form.partner_gender, F.data.startswith("pgender_"))
async def process_partner_gender(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_gender_key = callback_query.data.split("_")[1]
    if partner_gender_key in PARTNER_GENDER_OPTIONS:
        await state.update_data(partner_gender=PARTNER_GENDER_OPTIONS[partner_gender_key][lang])
        await state.set_state(Form.partner_age)
        await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    else:
        await callback_query.message.edit_text(TEXTS[lang]["invalid_callback_input"], reply_markup=get_partner_gender_keyboard(lang))
    await callback_query.answer()

@dp.message(Form.partner_age, F.text)
async def process_partner_age(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_age_text = message.text
    await state.update_data(partner_age=partner_age_text)
    await state.set_state(Form.partner_description)
    await message.answer(TEXTS[lang]["partner_description_prompt"])

@dp.message(Form.partner_description, F.text)
async def process_partner_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    partner_description_text = message.text
    await state.update_data(partner_description=partner_description_text)
    await state.set_state(Form.about_me)
    await message.answer(TEXTS[lang]["about_me_prompt"])

@dp.message(Form.about_me, F.text)
async def process_about_me(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    about_me_text = message.text
    if len(about_me_text) >= 50:
        await state.update_data(about_me=about_me_text)
        await state.set_state(Form.contact)
        await message.answer(TEXTS[lang]["contact_prompt"])
    else:
        await message.answer(TEXTS[lang]["about_me_too_short"])

@dp.message(Form.contact, F.text)
async def process_contact(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    contact_info = message.text
    await state.update_data(contact=contact_info)
    await state.set_state(Form.photo)
    await message.answer(TEXTS[lang]["photo_prompt"])

@dp.message(Form.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)

    # NEW: Transition to channel_check instead of confirm
    await state.set_state(Form.channel_check)
    # Construct channel link (assuming CHANNEL_ID is a raw chat ID like -100xxxxxxxxxx)
    channel_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
    await message.answer(
        TEXTS[lang]["channel_check_prompt"].format(channel_link=channel_link),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["channel_check_button"], callback_data="check_channel_membership")]
        ])
    )

@dp.message(Form.photo)
async def process_photo_invalid(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["invalid_photo"])

@dp.callback_query(Form.channel_check, F.data == "check_channel_membership")
async def check_channel_membership(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    user_id = callback_query.from_user.id

    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            await state.set_state(Form.confirm)
            summary_message = await generate_summary_message(user_data, lang)
            await callback_query.message.edit_text(
                summary_message,
                reply_markup=get_confirm_keyboard(lang)
            )
            await callback_query.answer(TEXTS[lang]["membership_verified"])
        else:
            channel_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
            await callback_query.message.edit_text(
                TEXTS[lang]["not_a_member"] + f"\n\n{TEXTS[lang]['channel_check_prompt'].format(channel_link=channel_link)}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=TEXTS[lang]["channel_check_button"], callback_data="check_channel_membership")]
                ])
            )
            await callback_query.answer(TEXTS[lang]["not_a_member"], show_alert=True)
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        channel_link = f"https://t.me/c/{str(CHANNEL_ID)[4:]}"
        await callback_query.message.edit_text(
            TEXTS[lang]["not_a_member"] + f"\n\n{TEXTS[lang]['channel_check_prompt'].format(channel_link=channel_link)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=TEXTS[lang]["channel_check_button"], callback_data="check_channel_membership")]
            ])
        )
        await callback_query.answer("A'zolikni tekshirishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.", show_alert=True)


@dp.callback_query(Form.confirm, F.data.startswith("confirm_"))
async def process_confirm(callback_query: CallbackQuery, state: FSMContext):
    confirmation = callback_query.data.split("_")[1]
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")

    if confirmation == "yes":
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username if callback_query.from_user.username else "Noma'lum"
        full_name = callback_query.from_user.full_name

        application_text = (
            f"{TEXTS[lang]['new_application_title']}"
            f"<b>{TEXTS[lang]['user_label']}</b> <a href='tg://user?id={user_id}'>{full_name} (@{username})</a>\n"
           f"<b>{TEXTS[lang]['gender_label']}</b> {TEXTS[lang].get(f'gender_{user_data.get('gender')}', TEXTS[lang]['unknown'])}"
            f"<b>{TEXTS[lang]['country_label']}</b> {user_data.get('country_name', TEXTS[lang]['not_selected'])}\n"
            f"<b>{TEXTS[lang]['region_label']}</b> {user_data.get('region_name', TEXTS[lang]['not_selected'])}\n"
            f"<b>{TEXTS[lang]['district_label']}</b> {user_data.get('district_name', TEXTS[lang]['not_selected'])}\n"
            f"<b>{TEXTS[lang]['age_label']}</b> {user_data.get('age', TEXTS[lang]['not_entered'])}\n"
            f"<b>{TEXTS[lang]['looking_for_type_label']}</b> {user_data.get('looking_for_type', TEXTS[lang]['not_selected'])}\n"
            f"<b>{TEXTS[lang]['partner_gender_label']}</b> {user_data.get('partner_gender', TEXTS[lang]['not_selected'])}\n"
            f"<b>{TEXTS[lang]['partner_age_label']}</b> {user_data.get('partner_age', TEXTS[lang]['not_entered'])}\n"
            f"<b>{TEXTS[lang]['partner_description_label']}</b> {user_data.get('partner_description', TEXTS[lang]['not_entered'])}\n"
            f"<b>{TEXTS[lang]['about_me_label']}</b> {user_data.get('about_me', TEXTS[lang]['not_entered'])}\n"
            f"<b>{TEXTS[lang]['contact_label']}</b> {user_data.get('contact', TEXTS[lang]['not_entered'])}\n"
        )
        photo_id = user_data.get("photo_id")

        try:
            if photo_id:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=application_text, parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(chat_id=CHANNEL_ID, text=application_text, parse_mode=ParseMode.HTML)
            await callback_query.message.edit_text(TEXTS[lang]["application_accepted"])
        except Exception as e:
            print(f"Error publishing application: {e}")
            await callback_query.message.edit_text(TEXTS[lang]["application_error"])
        await state.clear()
    else: # confirm_no
        await state.set_state(Form.language)
        await callback_query.message.edit_text(TEXTS[lang]["application_cancelled"])
        await state.clear()
    await callback_query.answer()

# --- Back button handler ---
@dp.callback_query(F.data.startswith("back_to_"))
async def back_button_handler(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    target_state_name = callback_query.data.split("_")[2]

    if target_state_name == "language":
        await state.set_state(Form.language)
        await callback_query.message.edit_text(TEXTS["uz"]["start_message"], reply_markup=get_language_keyboard())
    elif target_state_name == "gender":
        await state.set_state(Form.gender)
        await callback_query.message.edit_text(TEXTS[lang]["gender_prompt"], reply_markup=get_gender_keyboard(lang))
    elif target_state_name == "proof_voice":
        proof_text = user_data.get("proof_text")
        if not proof_text:
            proof_text = generate_random_proof_text(lang)
            await state.update_data(proof_text=proof_text)
        await state.set_state(Form.proof_voice)
        await callback_query.message.edit_text(TEXTS[lang]["proof_voice_prompt"].format(proof_text=proof_text))
    elif target_state_name == "country":
        await state.set_state(Form.country)
        await callback_query.message.edit_text(TEXTS[lang]["country_prompt"], reply_markup=get_countries_keyboard(lang))
    elif target_state_name == "region":
        selected_country_key = user_data.get("country_key")
        if selected_country_key and selected_country_key in COUNTRIES:
            await state.set_state(Form.region)
            await callback_query.message.edit_text(
                TEXTS[lang]["region_prompt"],
                reply_markup=get_regions_keyboard(selected_country_key, lang)
            )
        else:
            await state.set_state(Form.country)
            await callback_query.message.edit_text(
                TEXTS[lang]["country_prompt"],
                reply_markup=get_countries_keyboard(lang)
            )
    elif target_state_name == "district":
        selected_country_key = user_data.get("country_key")
        selected_region_key = user_data.get("region_key")
        if selected_country_key and selected_region_key:
            await state.set_state(Form.district)
            current_region_name = user_data.get("region_name", TEXTS[lang]["not_selected"])
            await callback_query.message.edit_text(
                TEXTS[lang]["district_prompt"].format(region_name=current_region_name),
                reply_markup=get_districts_keyboard(selected_country_key, selected_region_key, lang)
            )
        else:
            await state.set_state(Form.region)
            await callback_query.message.edit_text(
                TEXTS[lang]["region_prompt"],
                reply_markup=get_regions_keyboard(selected_country_key, lang)
            )
    elif target_state_name == "age":
        await state.set_state(Form.age)
        await callback_query.message.edit_text(TEXTS[lang]["age_prompt"], reply_markup=get_age_keyboard(lang))
    elif target_state_name == "looking_for_type":
        await state.set_state(Form.looking_for_type)
        await callback_query.message.edit_text(TEXTS[lang]["looking_for_type_prompt"], reply_markup=get_looking_for_keyboard(lang))
    elif target_state_name == "partner_gender":
        await state.set_state(Form.partner_gender)
        await callback_query.message.edit_text(TEXTS[lang]["partner_gender_prompt"], reply_markup=get_partner_gender_keyboard(lang))
    elif target_state_name == "partner_age":
        await state.set_state(Form.partner_age)
        await callback_query.message.edit_text(TEXTS[lang]["partner_age_prompt"])
    elif target_state_name == "partner_description":
        await state.set_state(Form.partner_description)
        await callback_query.message.edit_text(TEXTS[lang]["partner_description_prompt"])
    elif target_state_name == "about_me":
        await state.set_state(Form.about_me)
        await callback_query.message.edit_text(TEXTS[lang]["about_me_prompt"])
    elif target_state_name == "contact":
        await state.set_state(Form.contact)
        await callback_query.message.edit_text(TEXTS[lang]["contact_prompt"])
    elif target_state_name == "photo":
        await state.set_state(Form.photo)
        await callback_query.message.edit_text(TEXTS[lang]["photo_prompt"])
    elif target_state_name == "channel_check": # NEW BACK HANDLING
        await state.set_state(Form.photo)
        await callback_query.message.edit_text(TEXTS[lang]["photo_prompt"])

    await callback_query.answer()

# --- Invalid input handlers (assumed from context) ---
@dp.message(StateFilter(Form.partner_age))
async def handle_invalid_partner_age_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["partner_age_prompt"]) # Re-prompt for text input

@dp.message(StateFilter(Form.partner_description))
async def handle_invalid_partner_description_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(TEXTS[lang]["partner_description_prompt"]) # Re-prompt for text input

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

        while True:
            await asyncio.sleep(3600)
    else:
        # Polling mode
        print("Starting bot in polling mode...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
