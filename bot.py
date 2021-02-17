import asyncio
import logging
import requests
import schedule

from aiogram import Dispatcher, Bot
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import app.handlers.common
from app.handlers.common import register_handlers_common, config, bot, db, SQLighter
from threading import Thread
from time import sleep
import datetime


logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/cancel", description="Отменить отправку"),
        BotCommand(command="/help", description="Напомни, что делать?")
    ]
    await bot.set_my_commands(commands)
    

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")

    #Объявление и инициализация объектов бота и диспетчера
    dp = Dispatcher(bot, storage=MemoryStorage())

    #регистрация хэндлеров
    register_handlers_common(dp)

    #установка команд бота
    await set_commands(bot)

    #Запуск поллинга
    await dp.skip_updates()
    
    await bot.send_message(chat_id=config.tg_bot.admin_id, text="Бот начал работу!")

    await dp.start_polling()
    
    await bot.send_message(chat_id=config.tg_bot.admin_id, text="Бот завершил работу!")
    db.close_db()
    await bot.close()
        
def schedule_checker():#с заданной sleep-периодичностью проверяет дату
    while True:
        schedule.run_pending()#относиться к библиотеке
        sleep(1)

def function_to_run():#функция передаёься в библиотеку для выполнения по расписанию
    current_date = datetime.date.today()
    current_day = int(datetime.datetime.strftime(current_date, "%d"))
    print(current_day)

    db = SQLighter('sqlite_db.db')
    chat_ids = []

    for i in range(1, int(db.how_many_users()) + 1):
        this_id = db.get_tg_id(i)
        chat_ids.append(this_id)

    if current_day in [14,28]:#в указанных числах сбрасываем статус, чтобы потом отправить всем напоминание
        for chat_id in chat_ids:
            try:
                db.set_status(chat_id, False)
            except:
                pass

    if (current_day > 14 and current_day < 17) or (current_day > 28 or current_day < 2):#в середине и в конце месяца отправляем уведомления
        for chat_id in chat_ids:
            if not db.get_status(chat_id):
                request = f"https://api.telegram.org/bot{config.tg_bot.token}/sendMessage?chat_id={chat_id}&text=Не забудь скинуть чек, я его очень жду. Для этого нажми на /start ."
                requests.get(request)

    if current_day == 17 or current_day == 2:
        for chat_id in chat_ids:
            if not db.get_status(chat_id):
                request = f"https://api.telegram.org/bot{config.tg_bot.token}/sendMessage?chat_id={config.tg_bot.admin_id}&text=({db.get_nickname(chat_id)}) - нет чека."
                requests.get(request)


    

        
if __name__ == '__main__':
    schedule.every().day.at("10:55").do(function_to_run)#относиться к библиотеке
    Thread(target=schedule_checker).start()#поток
    asyncio.run(main())
