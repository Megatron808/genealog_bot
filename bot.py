import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class Form(StatesGroup):
    waiting_contact = State()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_contact)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Подтвердить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer(
        "👋 Здравствуйте!\n\n"
        "Вы обратились за услугой генеалога.\n\n"
        "🎁 *Бесплатная консультация!*\n\n"
        "Для получения консультации, пожалуйста, подтвердите свой номер телефона — "
        "это нужно, чтобы убедиться, что вы реальный человек.\n\n"
        "Нажмите кнопку ниже 👇",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@dp.message(Form.waiting_contact, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact

    # Проверка, что пользователь поделился СВОИМ контактом
    if contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Пожалуйста, поделитесь именно *своим* номером через кнопку ниже.",
            parse_mode="Markdown",
        )
        return

    await state.clear()

    # Уведомление админу (вам) с данными пользователя
    username = f"@{message.from_user.username}" if message.from_user.username else "нет username"
    try:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🔔 *Новая заявка на консультацию!*\n\n"
            f"👤 Имя: {message.from_user.full_name}\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"📞 Телефон: `{contact.phone_number}`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")

    # Перенаправление пользователя в чат с вами
    await message.answer(
        "✅ Спасибо! Номер подтверждён.\n\n"
        "Сейчас перенаправляю вас в чат с генеалогом для бесплатной консультации 👇",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Кнопка-ссылка на ваш личный чат
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать генеалогу",
                    url=f"https://t.me/{ADMIN_USERNAME}",
                )
            ]
        ]
    )

    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть чат и написать мне:",
        reply_markup=kb,
    )


@dp.message(Form.waiting_contact)
async def wrong_input(message: Message):
    await message.answer(
        "Пожалуйста, воспользуйтесь кнопкой *«📱 Подтвердить номер»* ниже, "
        "чтобы поделиться своим контактом.",
        parse_mode="Markdown",
    )


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())