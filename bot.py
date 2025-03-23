import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot_modules.dice import register_dice_handlers
from bot_modules.character import register_character_handlers, init_db
from bot_modules.wizard import register_wizard_handlers
from bot_modules.start import register_start_handlers

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


register_start_handlers(dp)
register_dice_handlers(dp)
register_character_handlers(dp)
register_wizard_handlers(dp)


async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот запущен!")
    asyncio.run(main())