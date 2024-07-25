import asyncio
import logging
import config
import sys
import io
import json
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router, set_bot, setup_handlers, parsing, bad_urls
from db import UsersDataBase

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = UsersDataBase()


async def main():
    global bot
    bot = Bot(token=config.TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    set_bot(bot)
    setup_handlers()
    await bot.delete_webhook(drop_pending_updates=True)
    tasks = [dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()), check_urls()]
    await asyncio.gather(*tasks)


async def check_urls():
    
    while True:
        users = await db.get_all_users()
        with open('urls.json', 'r') as file:
            data = json.load(file)
        
        message = ''
        for user in users:
            
            urls = data.get("urls", [])
            
            for url in urls:
                response = await parsing([url])
                if response:
                    message += f'@{url["name"]} - <a href=\"{url["url"]}\">объявление</a> неактивно ❌\n'
                else:
                    continue
            try:
                if message != '':
                    await bot.send_message(chat_id=user[0], text=message)
            except:
                continue
        await asyncio.sleep(60 * 60)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
