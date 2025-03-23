import os
import asyncpg
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command


load_dotenv()

router = Router()


pool = None

class StatsStates(StatesGroup):
    CHOOSING_STAT = State()
    ENTERING_VALUE = State()

def register_character_handlers(dp):
    dp.include_router(router)

async def init_db():
    global pool
    pool = await asyncpg.create_pool(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB'),
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', 5432))
    )
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                strength INTEGER DEFAULT 0,
                dexterity INTEGER DEFAULT 0,
                constitution INTEGER DEFAULT 0,
                wisdom INTEGER DEFAULT 0,
                charisma INTEGER DEFAULT 0,
                intelligence INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
            """
        )

async def get_user_stats(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM user_stats WHERE user_id = $1", 
            str(user_id)
        )
    return parse_stats(row) if row else default_stats()

async def set_user_stat(user_id: int, stat_name: str, value: int):
    column = stat_to_column(stat_name)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO user_stats (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
                str(user_id)
            )
            await conn.execute(
                f"UPDATE user_stats SET {column} = $1 WHERE user_id = $2",
                value, str(user_id)
            )

@router.message(Command("character_list", "cl", "character", "char"))
@router.message(F.text.in_(["📖 Персонаж"]))
async def character_list(message: Message, state: FSMContext):
    stats = await get_user_stats(message.from_user.id)
    builder = InlineKeyboardBuilder()
    
    stats_order = ["Сила", "Ловкость", "Стойкость", "Мудрость", "Харизма", "Интеллект"]
    for stat in stats_order:
        builder.button(text=stat, callback_data=f"set_stat_{stat}")
    
    builder.button(text="Уровень 🔢", callback_data="set_stat_Уровень")
    builder.button(text="📊 Показать все", callback_data="show_stats")
    builder.adjust(2)

    await message.answer(
        "🗂 Управление характеристиками персонажа:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(StatsStates.CHOOSING_STAT)

@router.message(Command("my_character"))
async def show_character_cmd(message: Message):
    await show_character(message)

@router.callback_query(F.data == "show_stats")
async def show_character_callback(callback: CallbackQuery):
    await show_character(callback.message, callback.from_user.id)
    await callback.answer()

async def show_character(message: Message, user_id: int = None):
    target_id = user_id or message.from_user.id
    stats = await get_user_stats(target_id)
    
    if all(v == 0 for k, v in stats.items() if k != "Уровень"):
        stats_text = "⛔ Характеристики не заданы!\nИспользуйте /character для создания"
    else:
        stats_text = "\n".join(
            f"🔹 {k}: {v}{' 🎓' if k == 'Уровень' else ''}" 
            for k, v in stats.items()
        )
    
    await message.answer(
        f"📜 Персонаж {'вас' if user_id is None else 'пользователя'}:\n\n{stats_text}",
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("set_stat_"))
async def stat_select_handler(callback: CallbackQuery, state: FSMContext):
    stat = callback.data.split("_")[-1]
    await state.update_data(chosen_stat=stat)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data="cancel_input")
    
    await callback.message.edit_text(
        f"✏ Введите новое значение для {stat}:\n"
        f"(От 1 до 20 для Уровня, 0-99 для остальных)",
        reply_markup=builder.as_markup()
    )
    await state.set_state(StatsStates.ENTERING_VALUE)

@router.callback_query(F.data == "cancel_input")
async def cancel_input_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Ввод отменён.")
    await callback.answer()

@router.message(StatsStates.ENTERING_VALUE)
async def stat_value_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    stat = data.get("chosen_stat")
    
    try:
        value = int(message.text)
        if stat == "Уровень":
            if not 1 <= value <= 20:
                raise ValueError("Уровень должен быть между 1 и 20")
        elif not 0 <= value <= 99:
            raise ValueError("Значение должно быть между 0 и 99")
            
        await set_user_stat(message.from_user.id, stat, value)
        await message.answer(f"✅ {stat} успешно изменена на {value}")
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()

def parse_stats(row):
    return {
        "Сила": row['strength'],
        "Ловкость": row['dexterity'],
        "Стойкость": row['constitution'],
        "Мудрость": row['wisdom'],
        "Харизма": row['charisma'],
        "Интеллект": row['intelligence'],
        "Уровень": row['level']
    }

def default_stats():
    return {
        "Сила": 0,
        "Ловкость": 0,
        "Стойкость": 0,
        "Мудрость": 0,
        "Харизма": 0,
        "Интеллект": 0,
        "Уровень": 1
    }

def stat_to_column(stat_name: str):
    mapping = {
        "Сила": "strength",
        "Ловкость": "dexterity",
        "Стойкость": "constitution",
        "Мудрость": "wisdom",
        "Харизма": "charisma",
        "Интеллект": "intelligence",
        "Уровень": "level"
    }
    return mapping.get(stat_name, "level")