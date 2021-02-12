from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

available_food_names = ["суши", "спагетти", "хачапури"]
available_food_sizes = ["маленькую", "среднюю", "большую"]

class OrderFood(StatesGroup):
    waiting_for_food_name = State()
    waiting_for_food_size = State()

async def food_start(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in available_food_names:
        keyboard.add(name)

    await msg.answer('Выберите юлюдо:', reply_markup=keyboard)
    await OrderFood.first()

async def food_chosen(msg: types.Message, state: FSMContext):
    if msg.text.lower() not in available_food_names:
        await msg.answer('Пожалуйста, используйте предложенные кнопки для выбора блюда')
        return
    
    await state.update_data(chosen_food=msg.text.lower())

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for size in available_food_sizes:
        keyboard.add(size)

    await msg.answer('Теперь выберите размер порции', reply_markup=keyboard)

    await OrderFood.next()

async def size_chosen(msg: types.Message, state: FSMContext):
    if msg.text.lower() not in available_food_sizes:
        await msg.answer('Пожалуйста, используйте предложенные кнопки для выбора размера блюда')
        return
    
    await state.update_data(size_chosen=msg.text.lower())

    user_data = await state.get_data()
    await msg.answer(f"Вы заказали {msg.text.lower()} порцию {user_data.get('chosen_food')}.\n"
                    f"Попробуйте теперь заказать напитки /drinks", reply_markup=types.ReplyKeyboardRemove())
    
    await state.finish()

def register_handlers_food(dp: Dispatcher):
    dp.register_message_handler(food_start, commands=['food'], state='*')
    dp.register_message_handler(food_chosen, state=OrderFood.waiting_for_food_name)
    dp.register_message_handler(size_chosen, state=OrderFood.waiting_for_food_size)