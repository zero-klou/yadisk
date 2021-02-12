from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

available_drink_names = ['колы', "спрайта", "фанты"]
available_drink_sizes = ['маленький', "средний", "большой"]

class OrderDrinks(StatesGroup):
    waiting_for_drink_name = State()
    waiting_for_drink_size = State()

async def start_drink(msg: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in available_drink_names:
        keyboard.add(name)

    await msg.answer("Выберите напиток", reply_markup=keyboard)

    await OrderDrinks.first()

async def drink_chosen(msg: types.Message, state: FSMContext):
    if msg.text.lower() not in available_drink_names:
        await msg.answer("Пожалуйста выюерите напиток, используя предложенные кнопки")
        return

    await state.update_data(chosen_drink=msg.text.lower())

    keyboard = types.ReplyKeyboardMarkup()
    for size in available_drink_sizes:
        keyboard.add(size)

    await msg.answer("Теперь пожалуйста выберите объём напитка", reply_markup=keyboard)

    await OrderDrinks.next()

async def size_chosen(msg: types.Message, state: FSMContext):
    if msg.text.lower() not in available_drink_sizes:
        await msg.answer("Пожалуйста, выберите размер напитка, использую предложенные кнопки")
        return

    await state.update_data(chosen_size=msg.text.lower())

    user_data = await state.get_data()

    await msg.answer(f"Вы заказали {msg.text.lower()} объём {user_data.get('chosen_drink')}."
                    f"Теперь попробуйте зазать еду /food, если ещё не сделали этого)", reply_markup=types.ReplyKeyboardRemove())

    await state.finish()

def register_handlers_drinks(dp: Dispatcher):
    dp.register_message_handler(start_drink, commands=['drinks'], state='*')
    dp.register_message_handler(drink_chosen, state=OrderDrinks.waiting_for_drink_name)
    dp.register_message_handler(size_chosen, state=OrderDrinks.waiting_for_drink_size)