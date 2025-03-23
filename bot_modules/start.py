from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

router = Router()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🧙 Спросить мага"),
            KeyboardButton(text="🎲 Бросить кости")
        ],
        [
            KeyboardButton(text="📖 Персонаж"),
            KeyboardButton(text="❓ Помощь")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери путь познания..."
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        f"{hbold('Приветствую, искатель знаний!')}\n\n"
        "Я - Бальтазар Мудрый, хранитель древних тайн.\n"
        "Чем могу помочь?\n\n"
        "🌀 /ask [вопрос] - Совет мага\n"
        "🎲 /roll [формула] - Бросок костей\n"
        "📖 /character - Создать персонажа\n"
        "🌌 /wise_wizard [вопрос] - Мудрость с визуализацией"
    )
    await message.answer(welcome_text, reply_markup=main_kb)

@router.message(F.text.in_(["❓ Помощь", "help"]))
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        f"{hbold('Список магических команд:')}\n\n"
        "🧙 Мудрость мага:\n"
        "   /ask [вопрос] - Совет архимага\n"
        "   /wise_wizard [вопрос] - Ответ с магическим артефактом\n\n"
        "🎲 Броски костей:\n"
        "   /roll [формула] - Бросок по формуле (например: 2d20+1d4+Сила)\n"
        "   Доступные элементы формулы:\n"
        "     - `XdY` — бросок кубиков (X - количество, Y - грани), например `2d6`\n"
        "     - `+` / `-` — модификаторы (например, `+2`, `-1d4`)\n"
        "     - `Сила`, `Ловкость`, `Интеллект` и другие характеристики\n"
        "     - `БМ` — бонус мастерства, рассчитывается автоматически от уровня\n"
        "📖 Создание персонажа:\n"
        "   /character - Редактирование характеристик\n"
        "   /my_character - Показать характеристики\n\n"
        "⚙️ Прочие команды:\n"
        "   /start - Перезапустить бота\n"
        "   /help - Это сообщение"
    )
    await message.answer(help_text, reply_markup=main_kb)

def register_start_handlers(dp):
    dp.include_router(router)