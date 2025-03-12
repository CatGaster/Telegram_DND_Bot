import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from openai import OpenAI  
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверка наличия API-ключа
if not OPENROUTER_API_KEY:
    raise ValueError("🧙‍♂️ Врата в башню мага не откроются без ключа.")

# Инициализируем клиента OpenRouter (OpenAI)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Системное сообщение для задания стиля ответа
SYSTEM_PROMPT = (
    "Ты Бальтазар Мудрый - древний архимаг из мира Dungeons & Dragons. "
    "Отвечай, используя архаичную лексику, пословицы и метафоры. "
    "Отвечай сразу, без размышлений, анализов и пояснений процесса мышления. "
    "Вплетай в ответы упоминания древних рун, магических артефактов и судеб. "
    "Перепроверяй правильно ли ты указал нужную характеристику. "
    "Не используй китайские буквы и слова. "
    "Если у предмета или существа есть характеристики (по типу урона длинного лука 1d8 + ловкость), обязательно расскажи о них. "
    "Сохраняй тон мудрого наставника. Говори на русском языке."
)

# Создаём ограничение на количество запросов
semaphore = asyncio.Semaphore(10)  # Разрешаем не более 10 одновременных запросов

def format_question(user_question: str) -> str:
    """
    Форматирование вопроса с дополнительными указаниями.
    """
    return f"{user_question}\n\n⚠️ В ответе не размышляй, сразу отвечай, как если бы истина была известна тебе изначально."

def sync_openai_request(question: str, system_prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.5, # параметр креативности чем выше тем креативнее, но больше ошибок
            max_tokens=800 # Ограничение длины ответа 1 токен ≈ 4 символа на английском/русском
        )
        if completion and completion.choices and completion.choices[0].message:
            return completion.choices[0].message.content
        else:
            return "🌪️ Бальтазар не смог извлечь мудрость из космоса!"
    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        return "🌪️ Бальтазар не может ответить из-за магического сбоя!"

async def async_openai_request(question: str, system_prompt: str) -> str:

    async with semaphore:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, sync_openai_request, question, system_prompt)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Отправь мне свой вопрос, и Бальтазар внемлет ему.")

@dp.message()
async def message_handler(message: Message):
    try:
        # Отправляем "загрузочное" сообщение
        thinking_msg = await message.answer("🔮 Бальтазар изучает магические свитки...")

        formatted_question = format_question(message.text)
        response_text = await async_openai_request(formatted_question, SYSTEM_PROMPT)

        # Редактируем предыдущее сообщение, заменяя его на ответ
        await thinking_msg.edit_text(response_text)

    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")
        await message.answer("🌪️ Бальтазар истощил магическую энергию! Подожди немного и спроси снова.")

async def main():
    print("✅ Бот успешно запущен и слушает сообщения...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
