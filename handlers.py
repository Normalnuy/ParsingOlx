from aiogram import F, Router, types, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from states import InputUrlState, InputPasswordState, InputNewUser
from bs4 import BeautifulSoup
from db import UsersDataBase
import requests
import json
import sys
import io
import re
import config
import kb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

router = Router()
bot = None
db = UsersDataBase()

def set_bot(instance: Bot):
    global bot
    bot = instance

def setup_handlers():
    @router.message(Command("start"))
    async def start_handler(msg: Message, state: FSMContext):
        global done_pass
        done_pass = await msg.answer(f"👋 Привет, {msg.from_user.full_name}.\n\n🔢 Введите пароль: ⬇️")
        await state.set_state(InputPasswordState.password)
        
@router.message(InputPasswordState.password)
async def check_password(msg: Message, state: FSMContext) -> None:
    await state.update_data(password=msg.text)
    await done_pass.delete()
    await msg.delete()
    data = await state.get_data()
    await state.clear()
    if data['password'] == config.password:
        await db.add_user(msg.from_user.id, msg.from_user.username)
        await msg.answer(text='✅ Вы успешно зашли как <b>Администратор</b>.', parse_mode='HTML', 
                         reply_markup=kb.keyboard)
    else:
        await msg.answer(text='❌ Ошибка! Неверный пароль.\nИспользуйте /start еще раз.')

        

# --============== ОБРАБОТЧИКИ СОБЫТИЙ ==================-- #

@router.callback_query(F.data == 'user_delete')
async def user_delete(clbck: CallbackQuery, state: FSMContext):
    global delete_msg
    delete_msg = clbck.message
    matches = re.findall(r'@([^ ]+)', clbck.message.text)
    name = matches[0]
    await update_entry(name=name)
    
@router.callback_query(F.data == 'edit_url')
async def edit_url(clbck: CallbackQuery, state: FSMContext):
    matches = re.findall(r'@([^ ]+)', clbck.message.text)
    name = matches[0]
    await state.set_state(InputUrlState.url)
    await state.update_data(name=name)
    global edit_msg
    edit_msg = await clbck.message.edit_text(text=f'✒️ Вставьте URL:\n(В формате: https://www.example.com/)', reply_markup=kb.cancel_keyboard)
    
    
@router.message(InputUrlState.url)
async def edit_url_2(msg: Message, state: FSMContext) -> None:
    await state.update_data(url=msg.text)
    await msg.delete()
    data = await state.get_data()
    await state.clear()
    await update_entry(name=data['name'], new_url=data['url'])  
    
@router.callback_query(F.data == 'repeat_check')
async def repeat_check(clbck: CallbackQuery, state: FSMContext):
    dell = await clbck.message.edit_text(text="⏳ Проверка началась...")
    response = await parsing()
    if response:
        await dell.delete()
        for item in response:
            name = item.get('name')
            url = item.get('url')
            
            await clbck.answer(text=f"<b>Внимание:</b>\n" \
                                f"❌ У пользователя @{name} <a href=\"{url}\">объявление</a> неактивно или удалено!", 
                                                                            parse_mode='HTML', reply_markup=kb.bad_url)
    else:
        await dell.edit_text(text=f"✅ Все объявления <b>активны</b>.", parse_mode='HTML')


@router.callback_query(F.data == 'pass')
async def pass_button(clbck: CallbackQuery, state: FSMContext):
    await clbck.message.delete()


@router.message(F.text.lower() == "добавить пользователя")
async def add_user(msg: Message, state: FSMContext):
    await msg.delete()
    await state.set_state(InputNewUser.new_name)
    global add_msg
    add_msg = await msg.answer('✒️ Укажите никнейм, без символа <b>"@"</b>', parse_mode='HTML', reply_markup=kb.cancel_keyboard)
    
@router.message(InputNewUser.new_name)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(new_name=msg.text)
    await add_msg.edit_text(text=f'👾 Новый пользователь:\n\n<b>Username:</b> {msg.text}\n' \
        '<b>URL:</b> Вставьте ссылку на объявление...', reply_markup=kb.cancel_keyboard)
    await msg.delete()
    await state.set_state(InputNewUser.new_url)
        
@router.message(InputNewUser.new_url)
async def get_name(msg: Message, state: FSMContext):
    await state.update_data(new_url=msg.text)
    await msg.delete()
    data = await state.get_data()
    await state.clear()
    new_entry = {"name": data['new_name'], "url": data['new_url']}

    await add_msg.edit_text(text=f'👾 Новый пользователь:\n\n<b>Username:</b> {data["new_name"]}\n' \
        f'<b>URL:</b> <a href=\"{data["new_url"]}\">объявление</a>.\n\n⏳ Проверка объявления...')

    response = await parsing([new_entry])
    if not response:
        
        with open('urls.json', 'r') as file:
            data_json = json.load(file)

        data_json["urls"].append(new_entry)

        with open('urls.json', 'w') as file:
            json.dump(data_json, file, indent=2)
        
        await add_msg.edit_text(text=f'✅ Пользователь добавлен. Объявление активно.')
        
    else:
        await add_msg.edit_text(text=f'❌ Пользователь не добавлен. Объявление неактивно.')
    
    
@router.message(F.text.lower() == "статистика")
async def stats(msg: Message, state: FSMContext):
    await msg.delete()
    start = await msg.answer('⏳ Идет проверка...')
    
    with open('urls.json', 'r') as file:
        data = json.load(file)
    
    urls = data.get("urls", [])
    
    message = ''
    for url in urls:
        response = await parsing([url])
        if response:
            message += f'@{url["name"]} - <a href=\"{url["url"]}\">объявление</a> неактивно ❌\n'
        else:
            message += f'@{url["name"]} - <a href=\"{url["url"]}\">объявление</a> активно ✅\n'
    await start.edit_text(text=message)


@router.message(F.text.lower() == 'пользователи')
async def show_users(msg: Message):
    if msg:
        await msg.delete()
    start = await msg.answer("⏳ Идет поиск...")
    with open('urls.json', 'r') as file:
        data = json.load(file)
    
    urls = data.get("urls", [])
        
    inline_keyboard = []

    buttons_per_row = 3
    current_row = []
    
    for url in urls:
        button_text = f'{url["name"]}'
        button_callback_data = f'show_user_{url["name"]}'
        current_row.append(InlineKeyboardButton(text=button_text, callback_data=button_callback_data))

        if len(current_row) == buttons_per_row:
            inline_keyboard.append(current_row)
            current_row = []

    if current_row:
        inline_keyboard.append(current_row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    
    global show_user_btn
    show_user_btn = await msg.answer("👾 Список пользователей:", reply_markup=keyboard)
    await start.delete()

@router.callback_query(lambda c: c.data.startswith('show_user'))
async def show_user(clbck: CallbackQuery, state: FSMContext):
    button_text = next((button.text for row in clbck.message.reply_markup.inline_keyboard for button in row if button.callback_data == clbck.data), None)
    
    with open('urls.json', 'r') as file:
        data = json.load(file)

    urls = data.get("urls", [])

    for url in urls:
        if url["name"] == button_text:
            await show_user_btn.edit_text(text=f'👾 Пользователь @{button_text} - <a href=\"{url["url"]}\">объявление</a>', 
                                          reply_markup=kb.users)
            return  
    
    
@router.callback_query(F.data == 'close')
async def back_button(clbck: CallbackQuery, state: FSMContext):
    await show_user_btn.delete()
    
@router.callback_query(F.data == 'cancel')
async def back_button(clbck: CallbackQuery, state: FSMContext):
    await clbck.message.delete()

    
# --===================== ФУНКЦИИ =======================-- #

async def bad_urls(name, url):
    users = await db.get_all_users()
    for user in users:
        
        await bot.send_message(chat_id=user[0], text=f"<b>Внимание:</b>\n" \
            f"❌ У пользователя @{name} <a href=\"{url}\">объявление</a> неактивно или удалено!", 
            parse_mode='HTML', reply_markup=kb.bad_url)



# --============ СИСТЕМНЫЕ ФУНКЦИИ =======================-- #

async def update_entry(name, new_url=None):
    with open('urls.json', 'r') as file:
        data = json.load(file)

    urls = data.get("urls", [])

    for url in urls:
        if url.get("name") == name:
            if new_url:
                url["url"] = new_url
                await edit_msg.edit_text(text=f'✅ Ссылка @{name} на <a href="{new_url}">объявление</a> изменена.', parse_mode='HTML')
            else:
                urls = [url for url in urls if url.get("name") != name]
                await delete_msg.edit_text(text=f"✅ Пользователь @{name} удалён из системы.")
            break

    else:
        if delete_msg:
            try:
                await delete_msg.edit_text(text=f"❌ Пользователь @{name} не найден в системе.")
                return
            except Exception:
                return
                    
            
    data["urls"] = urls

    with open('urls.json', 'w') as file:
        json.dump(data, file, indent=4)

async def parsing(data=None):
    
    try:
        standart_title = 'Оголошення OLX.ua:'
        resultat = []
        
        if not data:
            urls = get_urls()
        else:
            urls = data
        for item in urls:
            name = item.get('name')
            url = item.get('url')
            html = get_html(url)
            if html:
            
                html = BeautifulSoup(html, "html.parser")
                nofind = html.select('.c-wrapper > p')
                deleteurl = html.select('title')
                
                if nofind:
                    data = {
                            'name': name,
                            'url': url
                        }
                    resultat.append(data)
                elif deleteurl:
                    if standart_title in deleteurl[0].text:
                        data = {
                            'name': name,
                            'url': url
                        }
                        resultat.append(data)
                continue
                
            else:
                data = {
                            'name': name,
                            'url': url
                        }
                resultat.append(data)
        return resultat
    except Exception as e:
        
        data = {
                'name': name,
                'url': url
            }
        resultat.append(data)

        return resultat

def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        return None

def get_urls():
    with open('urls.json', 'r') as file:
        data = json.load(file)
    urls_data = data.get('urls', [])
    return urls_data


__all__ = ["set_bot", "setup_handlers"]
