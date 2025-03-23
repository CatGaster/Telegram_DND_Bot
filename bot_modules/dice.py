import random
import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from bot_modules.character import get_user_stats


router = Router()

class DiceStates(StatesGroup):
    CUSTOM_ROLL = State()

def register_dice_handlers(dp):
    dp.include_router(router)


def get_proficiency_bonus(level):
    proficiency_table = {
        range(1, 5): 2,
        range(5, 9): 3,
        range(9, 13): 4,
        range(13, 17): 5,
        range(17, 21): 6
    }
    return next(bonus for levels, bonus in proficiency_table.items() if level in levels)

def calculate_stat_bonus(value):
    return (value - 10) // 2

@router.message(Command("roll", "ролл", "roll_dice"))
@router.message(F.text.in_(["🎲 Бросить кости"]))
async def roll_dice(message: Message, state: FSMContext = None):
    command_args = message.text.split()[1:] if message.text.startswith('/') else []
    if command_args:
        formula = ' '.join(command_args)
        user_id = message.from_user.id
        stats = await get_user_stats(user_id)
        stats["БМ"] = get_proficiency_bonus(stats.get("Уровень", 1))  
        for stat in stats:
            if stat not in ["Уровень", "БМ"]:
                stats[stat] = calculate_stat_bonus(stats[stat]) 
        response = parse_roll_formula(formula, stats)
        await message.answer(response)
    else:
        builder = InlineKeyboardBuilder()
        buttons = [("1d4", "dice_4"), ("1d6", "dice_6"), ("1d8", "dice_8"),
                   ("1d10", "dice_10"), ("1d12", "dice_12"), ("1d20", "dice_20"),
                   ("Кастомный", "custom_roll")]
        for text, data in buttons:
            builder.button(text=text, callback_data=data)
        await message.answer("Выберите кубик:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("dice_"))
async def handle_dice(callback: CallbackQuery):
    sides = int(callback.data.split("_")[1])
    result = random.randint(1, sides)
    await callback.message.edit_text(f"🎲 1d{sides}: {result}")

@router.callback_query(F.data == "custom_roll")
async def start_custom_roll(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите бросок (например: 2d6+Сила-1d4+БМ+3):")
    await state.set_state(DiceStates.CUSTOM_ROLL)

@router.message(DiceStates.CUSTOM_ROLL)
async def process_custom_roll(message: Message, state: FSMContext):
    formula = message.text
    user_id = message.from_user.id
    stats = await get_user_stats(user_id)
    stats["БМ"] = get_proficiency_bonus(stats.get("Уровень", 1))  
    for stat in stats:
        if stat not in ["Уровень", "БМ"]:
            stats[stat] = calculate_stat_bonus(stats[stat]) 
    response = parse_roll_formula(formula, stats)
    await message.answer(response)
    await state.clear()

def parse_roll_formula(formula: str, stats: dict) -> str:
    try:
        formula = re.sub(r'\s+', '', formula)  
        formula = formula.lower()
    
        tokens = re.split(r"([+-])", formula)
        tokens = [t for t in tokens if t.strip()]
        
        total = 0
        description = []
        current_sign = 1 
        
        for token in tokens:
            if token in '+-':
                current_sign = 1 if token == '+' else -1
                continue
            
            stat_match = next((k for k in stats if k.lower() == token.lower()), None)
            if stat_match:
                value = stats[stat_match]
                description.append(f"{current_sign:+d}{stat_match}({value})")
                total += current_sign * value
                continue
            
            if 'd' in token:
                try:
                    count, sides = map(int, token.split('d'))
                    rolls = [random.randint(1, sides) for _ in range(count)]
                    sum_rolls = sum(rolls)
                    description.append(f"{current_sign:+d}{count}d{sides}({','.join(map(str, rolls))})")
                    total += current_sign * sum_rolls
                except:
                    return f"Ошибка в формате кубика: {token}"
                continue
            
            try:
                value = int(token)
                description.append(f"{current_sign:+d}{value}")
                total += current_sign * value
            except:
                return f"Ошибка в формате числового модификатора: {token}"
        
       
        result = " ".join(description).replace('+1', '+').replace('-1', '-')
        return f"🎲 Результат:\n{result} = {total}"
    
    except Exception as e:
        return f"Ошибка обработки. Пример: /roll 2d20+Сила-1d4+БМ+5"
