import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.utils.defaults import DefaultBotProperties
from aiohttp import web

# --- Bot sozlamalari ---
# Bot tokeningizni shu yerga kiriting. BotFather'dan olishingiz mumkin.
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render environment variables'dan olinadi
# Arizalar joylanadigan kanal ID'si. Misol uchun: -1001234567890.
# Kanal ID'sini olish uchun botni kanalga administrator qilib qo'shing va biror xabar yuboring,
# so'ngra getUpdates API orqali yoki boshqa botlar yordamida olishingiz mumkin.
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) # CHANNEL_ID ni int ga o'tkazish muhim

# Domen nomingiz (ngrok yoki haqiqiy domen).
# Agar lokalda sinov qilsangiz, ngrokdan olingan HTTPS URLni kiriting (masalan: https://xxxxxxxx.ngrok-free.app).
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8000))

# --- FSM (Finite State Machine) holatlari ---
# Foydalanuvchining botdagi har bir bosqichini kuzatish uchun holatlar.
class Form(StatesGroup):
    gender = State()          # Jinsni tanlash
    proof_text = State()      # Ovozli xabar uchun matn
    proof_voice = State()     # Ovozli xabarni yuborish
    region = State()          # Viloyatni tanlash
    district = State()        # Tuman/shaharni tanlash
    looking_for = State()     # Nima qidirayotganini belgilash
    about_me = State()        # O'zi haqida ma'lumot
    contact = State()         # Bog'lanish uchun ma'lumot
    confirm = State()         # Ma'lumotlarni tasdiqlash

# --- Ma'lumotlar bazasi (Misol) ---
# Hozircha foydalanuvchi ma'lumotlari oddiy lug'atda saqlanadi.
# Real loyihada PostgreSQL, SQLite yoki boshqa ma'lumotlar bazasidan foydalanish tavsiya etiladi.
user_data_storage = {}

# --- Hududlar va tumanlar (Misol ma'lumotlar) ---
# Siz bu lug'atni o'zgartirishingiz va ko'proq viloyat/tumanlarni qo'shishingiz mumkin.
REGIONS = {
    "tashkent": {"name": "Toshkent", "districts": ["Bekobod", "Bo‘ka", "Ohangaron", "Oqqo‘rg‘on", "Chinoz", "Qibray", "Quyichirchiq", "Toshkent tumani",
                 "Yangiyo‘l", "Zangiota", "Bekobod shahar", "Ohangaron shahar", "Yangiyo‘l shahar"]},
    "samarkand": {"name": "Samarqand", "districts": ["Samarqand shahar", "Bulung‘ur", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod", "Oqdaryo", "Payariq",
                  "Pastdarg‘om", "Paxtachi", "Qo‘shrabot", "Samarqand tumani", "Toyloq"]},
    "bukhara": {"name": "Buxoro", "districts": ["Buxoro shahar", "Buxoro tumani", "G‘ijduvon", "Jondor", "Kogon", "Qorako‘l", "Olot", "Peshku",
               "Romitan", "Shofirkon", "Vobkent"]},
    "andijan": {"name": "Andijon", "districts": ["Andijon shahar", "Asaka", "Baliqchi", "Bo‘ston", "Izboskan", "Qo‘rg‘ontepa", "Shahrixon", "Ulug‘nor",
                "Xo‘jaobod", "Yuzboshilar", "Hokim"]},
    "fergana": {"name": "Farg'ona", "districts": ["Farg'ona shahar", "Farg'ona tumani", "Beshariq", "Bog‘dod", "Buvayda", "Dang‘ara", "Qo‘qon", "Quva",
                 "Rishton", "Rishton tumani", "Toshloq", "Oltiariq", "Quvasoy shahar"]},
    "namangan": {"name": "Namangan", "districts": ["Namangan shahar", "Chust", "Kosonsoy", "Mingbuloq", "Namangan tumani", "Pop", "To‘raqo‘rg‘on",
                 "Uychi", "Yangiqo‘rg‘on"]},
    "sirdaryo": {"name": "Sirdaryo", "districts": ["Guliston shahar", "Boyovut", "Guliston tumani", "Mirzaobod", "Oqoltin", "Sayxunobod", "Sardoba",
                 "Sirdaryo tumani", "Xovos"]},
    "jizzakh": {"name": "Jizzax", "districts": ["Jizzax shahar", "Arnasoy", "Baxmal", "Dashtobod", "Forish", "G‘allaorol", "Zarbdor", "Zomin",
               "Mirzacho‘l", "Paxtakor", "Sharof Rashidov"]},
    "kashkadarya": {"name": "Qashqadaryo", "districts": ["Qarshi shahar", "Chiroqchi", "G‘uzor", "Dehqonobod", "Koson", "Kitob", "Mirishkor", "Muborak",
                    "Nishon", "Qarshi tumani", "Shahrisabz", "Yakkabog‘"]},
    "surkhandarya": {"name": "Surxondaryo", "districts": ["Termiz shahar", "Angor", "Boysun", "Denov", "Jarqo‘rg‘on", "Muzrabot", "Sariosiyo", "Sherobod",
                    "Sho‘rchi", "Termiz tumani"]},
    "navoi": {"name": "Navoiy", "districts": ["Navoiy shahar", "Karmana", "Konimex", "Navbahor", "Nurota", "Tomdi", "Uchquduq", "Xatirchi"]},
    "khorezm": {"name": "Xorazm", "districts": ["Urganch shahar", "Bog‘ot", "Gurlan", "Xiva shahar", "Qo‘shko‘pir", "Shovot", "Urganch tumani", "Xonqa",
               "Yangiariq"]},
    "karakalpakstan": {"name": "Qoraqalpog'iston", "districts": ["Nukus shahar", "Amudaryo", "Beruniy", "Bo‘zatov", "Kegayli", "Qonliko‘l",
                                      "Qo‘ng‘irot",
                                      "Qorao‘zak", "Shumanay", "Taxtako‘pir", "To‘rtko‘l", "Xo‘jayli",
                                      "Chimboy", "Mo‘ynoq", "Ellikqal‘a"]},
}

# Foydalanuvchi nima qidirayotganini belgilash uchun opsiyalar.
LOOKING_FOR_OPTIONS = {
    "serious_relationship": "18+ munosabat",
    "friends": "Do'stlik",
    "just_chat": "Shunchaki suhbat",
    "family": "Oilaviy hayot",
    "travel_buddy": "Sayohat sherigi"
}

# --- Bot va Dispatcher obyektlari ---
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# --- Inline tugmalar funksiyalari ---

def get_gender_keyboard():
    """Jinsni tanlash uchun inline tugmalar yaratadi."""
    buttons = [
        [InlineKeyboardButton(text="♂️ Erkak", callback_data="gender_male")],
        [InlineKeyboardButton(text="♀️ Ayol", callback_data="gender_female")],
        [InlineKeyboardButton(text="👨‍👩‍👧‍👦 Oila", callback_data="gender_family")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_button(state_name: str):
    """Orqaga qaytish tugmasini yaratadi."""
    return InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_{state_name}")

def get_regions_keyboard():
    """Viloyatlarni tanlash uchun inline tugmalar yaratadi."""
    buttons = []
    for key, value in REGIONS.items():
        buttons.append([InlineKeyboardButton(text=value["name"], callback_data=f"region_{key}")])
    buttons.append([get_back_button("gender")]) # Oldingi bosqichga qaytish
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_districts_keyboard(region_key: str):
    """Tanlangan viloyatga mos tuman/shaharlarni tanlash uchun inline tugmalar yaratadi."""
    buttons = []
    if region_key in REGIONS:
        for district in REGIONS[region_key]["districts"]:
            buttons.append([InlineKeyboardButton(text=district, callback_data=f"district_{district}")])
    buttons.append([InlineKeyboardButton(text="❌ Tuman tanlamayman", callback_data="district_none")]) # Tashlab ketish tugmasi
    buttons.append([get_back_button("region")]) # Oldingi bosqichga qaytish
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_looking_for_keyboard():
    """Nima qidirayotganini belgilash uchun inline tugmalar yaratadi."""
    buttons = []
    for key, value in LOOKING_FOR_OPTIONS.items():
        buttons.append([InlineKeyboardButton(text=value, callback_data=f"looking_{key}")])
    buttons.append([get_back_button("district")]) # Oldingi bosqichga qaytish
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    """Ma'lumotlarni tasdiqlash uchun inline tugmalar yaratadi."""
    buttons = [
        [InlineKeyboardButton(text="✅ Tasdiqlayman", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="✏️ Qayta kiritish", callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Random matn generatsiyasi ---
def generate_random_proof_text():
    """Jinsni tasdiqlash uchun tasodifiy qisqa matn yaratadi."""
    texts = [
        "Bugun havo juda yaxshi. Sizning kayfiyatingiz qanday?",
        "Salom! Ishlaringiz yaxshimi?",
        "Tez orada yoz keladi. Dam olishga rejalaringiz bormi?",
        "Kitob o'qishni yoqtirasizmi?",
        "Hayot go'zal, shunday emasmi?",
        "Muzqaymoq yeyishni xohlaysizmi?",
        "Eng sevimli rangingiz qaysi?",
        "Yangi kun, yangi imkoniyatlar!"
    ]
    return random.choice(texts)

# --- Start buyrug'i handler'i ---
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """/start buyrug'i kelganda ishga tushadi va jinsni tanlash bosqichiga o'tadi."""
    await state.clear() # Oldingi holatni tozalash
    await state.set_state(Form.gender)
    await message.answer("Assalomu alaykum! Arizani to'ldirish uchun jinsingizni tanlang:",
                         reply_markup=get_gender_keyboard())

# --- Orqaga qaytish handler'i ---
@dp.callback_query(F.data.startswith("back_to_"))
async def back_button_handler(callback_query: CallbackQuery, state: FSMContext):
    """'Orqaga' tugmasi bosilganda oldingi bosqichga qaytaradi."""
    target_state_name = callback_query.data.split("_")[2]
    user_data = await state.get_data()

    if target_state_name == "gender":
        await state.set_state(Form.gender)
        await callback_query.message.edit_text(
            "Jinsingizni tanlang:",
            reply_markup=get_gender_keyboard()
        )
    elif target_state_name == "region":
        # Agar jins "Oila" bo'lsa, to'g'ridan-to'g'ri regionga qaytish
        if user_data.get("gender") == "family":
            await state.set_state(Form.region)
            await callback_query.message.edit_text(
                "Qaysi viloyatdansiz?",
                reply_markup=get_regions_keyboard()
            )
        else: # Erkak yoki Ayol bo'lsa, ovozli tasdiqlashga qaytish
            proof_text = user_data.get("proof_text")
            if not proof_text: # Agar proof_text yo'q bo'lsa, yangisini generatsiya qilish
                proof_text = generate_random_proof_text()
                await state.update_data(proof_text=proof_text)
            await state.set_state(Form.proof_voice)
            await callback_query.message.edit_text(
                f"Jinsingizni tasdiqlash uchun quyidagi matnni ovozli xabar qilib yuboring:\n\n<b>'{proof_text}'</b>"
            )
    elif target_state_name == "district":
        selected_region_key = user_data.get("region_key")
        if selected_region_key and selected_region_key in REGIONS:
            await state.set_state(Form.district)
            await callback_query.message.edit_text(
                f"{REGIONS[selected_region_key]['name']} viloyatining qaysi tumanidan/shahrinidansiz? (Majburiy emas)",
                reply_markup=get_districts_keyboard(selected_region_key)
            )
        else:
            # Agar region topilmasa, viloyat tanlashga qaytarish
            await state.set_state(Form.region)
            await callback_query.message.edit_text(
                "Viloyatni tanlashda xatolik yuz berdi. Qaysi viloyatdansiz?",
                reply_markup=get_regions_keyboard()
            )
    elif target_state_name == "looking_for":
        await state.set_state(Form.looking_for)
        await callback_query.message.edit_text(
            "Nima qidiryapsiz?",
            reply_markup=get_looking_for_keyboard()
        )
    elif target_state_name == "about_me":
        await state.set_state(Form.about_me)
        await callback_query.message.edit_text(
            "Iltimos, o'zingiz haqingizda ma'lumot qoldiring (kamida 50 belgi):"
        )
    elif target_state_name == "contact":
        await state.set_state(Form.contact)
        await callback_query.message.edit_text(
            "Bog'lanish uchun raqamingizni (masalan: +998XXYYYYYYY) yoki telegram username'ingizni (masalan: @username) qoldiring:"
        )

    await callback_query.answer()


# --- Jinsni tanlash handler'i ---
@dp.callback_query(Form.gender, F.data.startswith("gender_"))
async def process_gender(callback_query: CallbackQuery, state: FSMContext):
    """Jins tanlanganda ishga tushadi."""
    gender = callback_query.data.split("_")[1]
    await state.update_data(gender=gender)

    if gender in ["male", "female"]:
        proof_text = generate_random_proof_text()
        await state.update_data(proof_text=proof_text)
        await state.set_state(Form.proof_voice)
        await callback_query.message.edit_text(
            f"Jinsingizni tasdiqlash uchun quyidagi matnni ovozli xabar qilib yuboring:\n\n<b>'{proof_text}'</b>"
        )
    else: # family
        await state.set_state(Form.region)
        await callback_query.message.edit_text(
            "Siz oila sifatida ro'yxatdan o'tyapsiz. Qaysi viloyatdansiz?",
            reply_markup=get_regions_keyboard()
        )
    await callback_query.answer()

# --- Ovozli xabar bilan tasdiqlash handler'i ---
@dp.message(Form.proof_voice, F.content_type == types.ContentType.VOICE)
async def process_proof_voice(message: Message, state: FSMContext):
    """Ovozli xabar qabul qilinganda ishga tushadi."""
    # Eslatma: Bu yerda faqat ovozli xabar kelganligi tekshiriladi.
    # Ovozli xabardagi matnni tekshirish uchun qo'shimcha Speech-to-Text APIlar kerak bo'ladi.
    if message.voice:
        await state.set_state(Form.region)
        await message.answer("Rahmat, ovozli xabar qabul qilindi. Endi qaysi viloyatdansiz?",
                             reply_markup=get_regions_keyboard())
    else:
        await message.answer("Iltimos, yuqoridagi matnni ovozli xabar qilib yuboring.")

@dp.message(Form.proof_voice)
async def process_proof_voice_invalid(message: Message, state: FSMContext):
    """Ovozli xabar o'rniga boshqa turdagi xabar kelganda."""
    await message.answer("Noto'g'ri format. Iltimos, ovozli xabar yuboring.")


# --- Viloyatni tanlash handler'i ---
@dp.callback_query(Form.region, F.data.startswith("region_"))
async def process_region(callback_query: CallbackQuery, state: FSMContext):
    """Viloyat tanlanganda ishga tushadi."""
    region_key = callback_query.data.split("_")[1]
    if region_key in REGIONS:
        await state.update_data(region_key=region_key, region_name=REGIONS[region_key]["name"])
        await state.set_state(Form.district)
        await callback_query.message.edit_text(
            f"{REGIONS[region_key]['name']} viloyatining qaysi tumanidan/shahrinidansiz? (Majburiy emas)",
            reply_markup=get_districts_keyboard(region_key)
        )
    else:
        await callback_query.message.edit_text("Noto'g'ri viloyat tanlandi. Qayta urinib ko'ring.",
                                               reply_markup=get_regions_keyboard())
    await callback_query.answer()

# --- Tuman/shaharni tanlash handler'i ---
@dp.callback_query(Form.district, F.data.startswith("district_"))
async def process_district(callback_query: CallbackQuery, state: FSMContext):
    """Tuman/shahar tanlanganda ishga tushadi."""
    district = callback_query.data.split("_")[1]
    if district == "none":
        await state.update_data(district=None)
        await callback_query.message.edit_text("Tuman tanlanmadi. Endi nima qidiryapsiz?",
                                               reply_markup=get_looking_for_keyboard())
    else:
        user_data = await state.get_data()
        region_key = user_data.get("region_key")
        if region_key and district in REGIONS[region_key]["districts"]:
            await state.update_data(district=district)
            await callback_query.message.edit_text(f"{district} tanlandi. Endi nima qidiryapsiz?",
                                                   reply_markup=get_looking_for_keyboard())
        else:
            await callback_query.message.edit_text("Noto'g'ri tuman tanlandi. Qayta urinib ko'ring.",
                                                   reply_markup=get_districts_keyboard(region_key))
    await state.set_state(Form.looking_for)
    await callback_query.answer()

# --- Nima qidirayotganini belgilash handler'i ---
@dp.callback_query(Form.looking_for, F.data.startswith("looking_"))
async def process_looking_for(callback_query: CallbackQuery, state: FSMContext):
    """Nima qidirayotganini belgilaganda ishga tushadi."""
    looking_for_key = callback_query.data.split("_")[1]
    if looking_for_key in LOOKING_FOR_OPTIONS:
        await state.update_data(looking_for=LOOKING_FOR_OPTIONS[looking_for_key])
        await state.set_state(Form.about_me)
        await callback_query.message.edit_text("Iltimas, o'zingiz haqingizda ma'lumot qoldiring (kamida 50 belgi):")
    else:
        await callback_query.message.edit_text("Noto'g'ri tanlov. Qayta urinib ko'ring.",
                                               reply_markup=get_looking_for_keyboard())
    await callback_query.answer()

# --- O'zi haqida ma'lumot handler'i ---
@dp.message(Form.about_me, F.text)
async def process_about_me(message: Message, state: FSMContext):
    """Foydalanuvchi o'zi haqida ma'lumot yuborganda ishga tushadi."""
    about_me_text = message.text
    if len(about_me_text) < 50:
        await message.answer("Ma'lumot kamida 50 belgidan iborat bo'lishi kerak. Iltimos, to'liqroq yozing.")
        return
    await state.update_data(about_me=about_me_text)
    await state.set_state(Form.contact)
    await message.answer("Bog'lanish uchun raqamingizni (masalan: +998XXYYYYYYY) yoki telegram username'ingizni (masalan: @username) qoldiring:")

# --- Bog'lanish uchun ma'lumot handler'i ---
@dp.message(Form.contact, F.text)
async def process_contact(message: Message, state: FSMContext):
    """Bog'lanish uchun ma'lumot yuborganda ishga tushadi."""
    contact_info = message.text
    await state.update_data(contact=contact_info)
    await state.set_state(Form.confirm)

    user_data = await state.get_data()
    gender_map = {"male": "Erkak", "female": "Ayol", "family": "Oila"}
    gender_display = gender_map.get(user_data.get("gender"), "Noma'lum")
    region_display = user_data.get("region_name", "Noma'lum")
    district_display = user_data.get("district", "Tanlanmagan") if user_data.get("district") else "Tanlanmagan"
    looking_for_display = user_data.get("looking_for", "Noma'lum")
    about_me_display = user_data.get("about_me", "Kiritilmagan")
    contact_display = user_data.get("contact", "Kiritilmagan")

    summary_message = (
        "<b>Sizning arizangiz:</b>\n\n"
        f"<b>Jins:</b> {gender_display}\n"
        f"<b>Viloyat:</b> {region_display}\n"
        f"<b>Tuman/Shahar:</b> {district_display}\n"
        f"<b>Qidiruv:</b> {looking_for_display}\n"
        f"<b>O'zi haqida:</b> {about_me_display}\n"
        f"<b>Bog'lanish:</b> {contact_display}\n\n"
        "Yuqoridagi ma'lumotlar to'g'rimi? Tasdiqlasangiz, arizangiz kanalda e'lon qilinadi."
    )
    await message.answer(summary_message, reply_markup=get_confirm_keyboard())

# --- Tasdiqlash handler'i ---
@dp.callback_query(Form.confirm, F.data.startswith("confirm_"))
async def process_confirm(callback_query: CallbackQuery, state: FSMContext):
    """Arizani tasdiqlaganda yoki bekor qilganda ishga tushadi."""
    confirmation = callback_query.data.split("_")[1]

    if confirmation == "yes":
        user_data = await state.get_data()
        user_id = callback_query.from_user.id
        username = callback_query.from_user.username
        first_name = callback_query.from_user.first_name

        gender_map = {"male": "Erkak", "female": "Ayol", "family": "Oila"}
        gender_display = gender_map.get(user_data.get("gender"), "Noma'lum")
        region_display = user_data.get("region_name", "Noma'lum")
        district_display = user_data.get("district", "Tanlanmagan") if user_data.get("district") else "Tanlanmagan"
        looking_for_display = user_data.get("looking_for", "Noma'lum")
        about_me_display = user_data.get("about_me", "Kiritilmagan")
        contact_display = user_data.get("contact", "Kiritilmagan")

        # Telegram profiliga o'tish havolasi
        # Agar username mavjud bo'lsa, @username ko'rinishida, aks holda tg://user?id= linki orqali.
        user_link_text = f"@{username}" if username else "Profilga havola"
        user_full_link = f"<a href='tg://user?id={user_id}'>{user_link_text}</a>"


        channel_message = (
            f"<b>Yangi ariza!</b>\n\n"
            f"<b>Foydalanuvchi:</b> {user_full_link}\n"
            f"<b>Jins:</b> {gender_display}\n"
            f"<b>Viloyat:</b> {region_display}\n"
            f"<b>Tuman/Shahar:</b> {district_display}\n"
            f"<b>Qidiruv:</b> {looking_for_display}\n"
            f"<b>O'zi haqida:</b> {about_me_display}\n"
            f"<b>Bog'lanish:</b> {contact_display}\n"
        )
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=channel_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            await callback_query.message.edit_text("Arizangiz qabul qilindi va kanalda e'lon qilindi. Rahmat!")
            await state.clear() # Arizani qabul qilgandan keyin holatni tozalash
        except Exception as e:
            await callback_query.message.edit_text(f"Arizani e'lon qilishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
            print(f"Error sending to channel: {e}")
            await state.clear()
    else: # confirm_no - Qayta kiritish
        await callback_query.message.edit_text("Arizangiz bekor qilindi. Qayta to'ldirish uchun /start buyrug'ini bosing.")
        await state.clear()
    await callback_query.answer()

# --- Noto'g'ri kiritishni boshqarish (umumiy handler) ---
@dp.message(StateFilter(
    Form.region,
    Form.district,
    Form.looking_for,
    Form.confirm
))
async def handle_invalid_callback_input(message: Message, state: FSMContext):
    """Inline tugmalar kutilgan bosqichlarda matnli xabar kelganda."""
    await message.answer("Iltimas, inline tugmalar orqali tanlov qiling yoki orqaga qaytish tugmasidan foydalaning.")

@dp.message(StateFilter(Form.about_me))
async def handle_invalid_about_me_input(message: Message, state: FSMContext):
    """'O'zi haqida' bosqichida noto'g'ri turdagi xabar kelganda."""
    await message.answer("Iltimas, o'zingiz haqingizda matn ko'rinishida ma'lumot bering.")

@dp.message(StateFilter(Form.contact))
async def handle_invalid_contact_input(message: Message, state: FSMContext):
    """'Bog'lanish' bosqichida noto'g'ri turdagi xabar kelganda."""
    await message.answer("Iltimas, bog'lanish uchun matn ko'rinishida ma'lumot bering.")


# --- Botni ishga tushirish funksiyasi ---
async def main():
    """Botni webhook rejimida ishga tushiradi."""
    # Oldingi webhookni o'chirish (muammolarni oldini olish uchun)
    await bot.delete_webhook(drop_pending_updates=True)

    # Bot ishga tushganda va o'chganda bajariladigan funksiyalar
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Aiohttp web ilovasini sozlash
    app = web.Application()
    # WEBHOOK_URL environment variable'dan olingani uchun, path'ni undan ajratib olish kerak
    # Yoki shunchaki WEBHOOK_URL ni butunligicha path sifatida ishlatish (agar u faqat path bo'lsa)
    # Bizning holatda WEBHOOK_URL to'liq URL bo'ladi, shuning uchun faqat path qismini ajratamiz
    # Eslatma: Bu yerda WEBHOOK_URL = "https://nightchatbot.onrender.com/webhook" deb qabul qilinadi.
    # Agar webhook_url faqat path bo'lsa (masalan "/webhook"), unda ajratish shart emas.
    # Hozirgi WEBHOOK_URL dan pathni ajratish
    from urllib.parse import urlparse
    parsed_url = urlparse(WEBHOOK_URL)
    webhook_path_for_handler = parsed_url.path if parsed_url.path else "/"


    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=webhook_path_for_handler)
    setup_application(app, dp, bot=bot)

    # Web serverni ishga tushirish
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEB_SERVER_HOST, WEB_SERVER_PORT)
    await site.start()

    print(f"Webhook URL: {WEBHOOK_URL}")
    # Telegramga webhook URLni o'rnatish
    await bot.set_webhook(WEBHOOK_URL)
    print("Bot ishga tushdi va webhook tinglamoqda...")

    # Serverni doimiy ishlashini ta'minlash
    while True:
        await asyncio.sleep(3600) # Har soatda tekshirish, adjust as needed

async def on_startup(bot: Bot):
    """Bot ishga tushganda bajariladi."""
    print("Bot muvaffaqiyatli ishga tushdi!")

async def on_shutdown(bot: Bot):
    """Bot o'chirilganda bajariladi."""
    print("Bot o'chirilmoqda!")
    await bot.delete_webhook() # Webhookni o'chirish
    await bot.session.close() # Bot sessiyasini yopish

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot foydalanuvchi tomonidan to'xtatildi.")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
