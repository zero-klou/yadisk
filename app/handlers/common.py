from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ContentType
import yadisk
import datetime
import os
from app.config_reader import load_config
import sqlite3

config = load_config("config/bot.ini")
bot = Bot(token=config.tg_bot.token)

class SendFiles(StatesGroup):
    waiting_for_send = State()
    sended = State()

class SQLighter():
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()
        print('Соединение установлено')
        db_version = self.cursor.execute('select sqlite_version();').fetchall()
        print(f'Версия базы данных: {db_version}')
        self.cursor.close()

    def close_db(self):
        self.cursor.close()
        self.connection.close()
        print('Соединение закрыто')

    def add_user(self, tg_id, nick, status=False):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute('INSERT INTO `tg_users` (`tg_id`, `status`, `nick`) VALUES (?,?,?)', (tg_id, status, nick))

    def set_status(self, tg_id, status):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute('UPDATE `tg_users` SET `status` = ? WHERE `tg_id` = ?', (status, tg_id))

    def get_tg_id(self, id):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute('SELECT `tg_id` FROM `tg_users` WHERE `id` = ?', (id,)).fetchall()[0][0]

    def how_many_users(self):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute('SELECT MAX(`id`) FROM tg_users').fetchall()[0][0]

    def get_status(self, tg_id):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute("SELECT `status` FROM `tg_users` WHERE `tg_id` = ?", (tg_id,)).fetchall()[0][0]

    def get_nickname(self, tg_id):
        with self.connection as c:
            self.cursor = c.cursor()
            return self.cursor.execute("SELECT `nick` FROM `tg_users` WHERE `tg_id` = ?", (tg_id,)).fetchall()[0][0]


db = SQLighter('sqlite_db.db')

y = yadisk.YaDisk(token=config.tg_bot.yadisk_config)

async def cmd_process_start(message: types.Message, state: FSMContext):
    await state.finish()
    try:
        db.add_user(message.chat.id, nick=message.from_user.username)
    except:
        print('Пользователь уже существует')
    await message.answer('Здравствуйте, данный бот собирает отчёты.\nВышлите файл в формате .jpg.\nЗа дполнительной информацией обращайтесь к вашему руководителю')
    print(db.how_many_users())
    await SendFiles.first()

async def cmd_process_cancel(message: types.Message, state: FSMContext):
    y.remove(config.photo_name, permanently=True)
    await message.answer('Вы удалили последний присланный файл, пришлите его заново до истечения срока!')
    await bot.send_message(chat_id=config.tg_bot.admin_id, text=f'({message.from_user.username}) - чек удалён. Ожидаю повторной отправки.')

    db.set_status(message.chat.id, False)
    await SendFiles.first()

async def send_file(message: types.Message, state: FSMContext):
    if (not y.check_token()):
        await message.answer('Токен для доступа к яндекс диску не доступен.\nОбратитесь к руководителю.')
        return

    current_date = datetime.date.today()#получаем текущую дату для формирования имени
    photo_name = '_'.join([datetime.datetime.strftime(current_date, "%d_%m_%Y"), message.from_user.username]) + '.jpg'#15_02_2021 - форматируем дату и добавляем имя пользователя
    config.photo_name = photo_name

    await message.photo[-1].download(photo_name)
    y.upload(photo_name, photo_name)#загружаем на ядиск
    os.remove(photo_name)#удаляем из файловой системы сервера
    await message.answer('Отправка файла произведена успешно!')
    await bot.send_message(chat_id=config.tg_bot.admin_id, text=f'({message.from_user.username}) - чек отправлен.')

    db.set_status(message.chat.id, True)
    await SendFiles.next()

async def cmd_process_help(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == "SendFiles:waiting_for_send":
        await message.answer('Жду отправки файла...\nОтправьте мне фотографию в формате .jpg')
    else:
        await message.answer('Файл уже отправлен! Если вы по ошибке отправили другой файл, воспользуйтесь командой /cancel .')

async def cmd_restart(message: types.Message):
    await message.answer('Похоже, что что-то пошло не так. Воспользуйтесь командой /start.')

async def user_fool(message: types.Message):
    await message.answer('Я не знаю, что с этим делать!\nПожалуйста отправьте фотографию чека, если ещё этого не сделали!')

def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_process_start, state='*', commands=['start'])
    dp.register_message_handler(cmd_process_cancel, state=SendFiles.sended, commands=['cancel'])
    dp.register_message_handler(send_file, state=SendFiles.waiting_for_send, content_types=ContentType.PHOTO)
    dp.register_message_handler(cmd_process_help, state='*', commands=["help"])
    dp.register_message_handler(cmd_restart, state=None, content_types=ContentType.ANY)
    dp.register_message_handler(user_fool, state=SendFiles.waiting_for_send, content_types=ContentType.ANY)
