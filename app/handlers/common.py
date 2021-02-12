from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import IDFilter, Text
from aiogram.dispatcher import FSMContext


async def cmd_process_start(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer(f'Здравствуйте, вы попали в бота для заказа еды!'
                    'Выберите, что хотите заказать: напитки (/drinks), блюда(/food)', reply_markup=types.ReplyKeyboardRemove())

async def cmd_cancel_process(msg: types.Message, state: FSMContext):
    await state.finish()
    await msg.answer('Действие отменено.'
                    'Для повторного заказа используйте команды (/drinks) и (/food)')

async def admin_cmd(msg: types.Message):
    await msg.answer('Поздравляю, эта команда доступна только админам!!!')

def register_handlers_common(dp: Dispatcher, admin_id: int):
    dp.register_message_handler(cmd_process_start, state='*', commands=['start'])
    dp.register_message_handler(cmd_cancel_process, state='*', commands=['cancel'])
    dp.register_message_handler(cmd_cancel_process, Text(equals="отмена", ignore_case=True), state='*')
    dp.register_message_handler(admin_cmd, IDFilter(user_id=admin_id), commands=['abracadabra'], state='*')