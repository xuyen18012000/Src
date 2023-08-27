import logging
import re
import asyncio
import sqlite3
import pyperclip
import aiosqlite
import random
import os
import time
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import types
from datetime import datetime, timedelta
from keep_alive import keep_alive
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType
from aiogram.types import ParseMode
import telebot
API_TOKEN = '6477551243: AAEU5DPOvohKlzZQkLars0dASZia4UFdUaQ'

bot_ten = "xuynok_bot "
#Source by diggory and Bot Chatgpt

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
user_refref = {}
# Thiết lập logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Tạo kết nối đến database
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Tạo bảng để lưu trữ thông tin tài khoản người dùng
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, phone_number TEXT, name TEXT, balance INTEGER DEFAULT 0)''')

# Kiểm tra bảng withdraw đã tồn tại chưa
c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='withdraw' ''')
if c.fetchone()[0] == 1:
    print('Bảng withdraw đã tồn tại')
else:
    # Tạo bảng withdraw nếu chưa tồn tại
    c.execute('''CREATE TABLE withdraw (phone_number TEXT, amount INTEGER, user_id INTEGER, timestamp TEXT, telegram_username TEXT)''')
    conn.commit()
    print('Tạo bảng withdraw thành công')

#bảng dữ liệu nhiệm vụ hoàn thành
c.execute('''CREATE TABLE IF NOT EXISTS completed_tasks             (user_id text, phone_number text, task_id text, 
             PRIMARY KEY (user_id, phone_number, task_id))''')
conn.commit()

# Đọc danh sách nhiệm vụ từ file tasks.json
with open('tasks.json', 'r') as f:
    tasks = json.load(f)

# Định nghĩa trạng thái đăng ký
class Registration(StatesGroup):
    phone_number = State()






   











# Xử lý khi người dùng sử dụng lệnh /start
async def start_handler(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    # Đặt trạng thái về trạng thái ban đầu
    await state.reset_state()

    # Kiểm tra xem người dùng đã tồn tại trong database chưa
    c.execute("SELECT * FROM users WHERE user_id = ?", (chat_id,))
    result = c.fetchone()
    if result is None:
        # Nếu không tồn tại, yêu cầu người dùng nhập số điện thoại để đăng ký
        await message.answer("Xin chào! Vui lòng nhập số điện thoại để đăng ký tài khoản:\n\n (Lưu ý: Đây là số momo để rút tiền về nhập sai sẽ không thể rút tiền.)")
        await Registration.phone_number.set()

    
    else:
        # Nếu đã tồn tại, thông báo tài khoản đã được đăng kí
        await message.answer(f"Chào mừng bạn đến với {bot_ten}\n. Hãy bắt đầu tham gia kiếm tiền ngay, tiếp tục chọn các chức năng bên dưới!", reply_markup=keyboard1)


# Định nghĩa hàm xử lý nhập số điện thoại
async def phone_number_handler(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    phone_number = message.text.strip()
    # Loại bỏ tất cả các ký tự không phải số
    phone_number = re.sub(r'\D', '', phone_number)

    # Nếu số điện thoại không có 10 số, báo lỗi
    if len(phone_number) != 10:
        await message.answer("Số điện thoại không hợp lệ, vui lòng nhập lại!")
        return

    # Kiểm tra xem số điện thoại đã tồn tại trong database chưa
    c.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
    result = c.fetchone()

    if result is None:
        # Nếu không tồn tại, tạo một tài khoản mới với số dư là 0
        c.execute("INSERT INTO users (user_id, phone_number, name, balance) VALUES (?, ?, '', 0)", (chat_id, phone_number))
        conn.commit()
        await message.answer("Đăng ký tài khoản thành công. Hãy bắt đầu tham gia làm nhiệm vụ kiếm tiền!", reply_markup=keyboard1)
    else:
      
        # Nếu đã tồn tại, thông báo tài khoản đã được đăng kí
        await message.answer("Tài khoản này đã tồn tại!")

    # Kết thúc trạng thái đăng kí số điện thoại
    await state.finish()


dp = Dispatcher(bot, storage=MemoryStorage())

# Đăng ký filters và handlers cho lệnh /start
dp.register_message_handler(start_handler, Command("start"), state="*")
dp.register_message_handler(phone_number_handler, state=Registration.phone_number)


cancel_button = KeyboardButton('❌Hủy')
cancel_markup = ReplyKeyboardMarkup([[cancel_button]], resize_keyboard=True)




# Định nghĩa trạng thái cho lệnh rút tiền
class Withdraw(StatesGroup):
    amount = State()

@dp.message_handler(Text(equals='💲Rút tiền'))
async def withdraw_balance(message: types.Message, state: FSMContext):
    # Lấy thông tin user_id và số dư tài khoản từ database
    user_id = message.from_user.id
    c.execute("SELECT balance, phone_number FROM users WHERE user_id = ?", (user_id,))
    balance, phone_number = c.fetchone()

    # Lưu thông tin user_id, balance và phone_number vào state
    await state.update_data(user_id=user_id, balance=balance, phone_number=phone_number)

    # Kiểm tra số tiền rút có hợp lệ không
    await Withdraw.amount.set()
    await message.answer("Nhập số tiền cần rút:\n(Tối thiểu 50,000 VND)", reply_markup=cancel_markup)

@dp.message_handler(lambda message: message.content_type == ContentType.TEXT and message.text.isdigit(), state=Withdraw.amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    # Lấy giá trị user_id, balance và phone_number từ state
    async with state.proxy() as data:
        user_id = data['user_id']
        balance = data['balance']
        phone_number = data['phone_number']

    withdraw_amount = int(message.text)
    if withdraw_amount < 50000:
        await message.answer("Số tiền rút không hợp lệ. Vui lòng nhập lại:", reply_markup=cancel_markup)
        return
    if withdraw_amount > balance:
        await message.answer("Số dư tài khoản không đủ để thực hiện lệnh rút!", reply_markup=cancel_markup)
        return

    # Cập nhật số dư trong database và thông báo thành công
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (withdraw_amount, user_id))
    conn.commit()
    await message.answer(f"Bạn đã đặt lệnh rút {withdraw_amount} VND. Hệ thống sẽ tiến hành thanh toán cho bạn trong vòng 7 ngày.", reply_markup=ReplyKeyboardRemove())

    # Lưu thông tin lệnh rút vào bảng withdraw
    c.execute("INSERT INTO withdraw (phone_number, amount, user_id, timestamp, telegram_username) VALUES (?, ?, ?, ?, ?)", (phone_number, withdraw_amount, user_id, datetime.now(), message.from_user.username))
    conn.commit()

    # Chuyển trạng thái của user về trạng thái ban đầu
    await state.finish()

@dp.message_handler(Text(equals='❌Hủy'), state=Withdraw.amount)
async def cancel_withdrawal(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Bạn đã hủy lệnh rút tiền!", reply_markup=taikhoan)


# Danh sách tên tài khoản Telegram của admin
admin_usernames = ['diggory347']


# Hàm kiểm tra xem một user có phải là admin hay không
def is_admin(user: types.User) -> bool:
    return user.username in admin_usernames

# Hàm xử lý lệnh /admin
@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    user = message.from_user
    if not is_admin(user):
        await message.answer("Bạn không có quyền truy cập vào tính năng này.")
        return
    text = "Chức năng:\n"
    text += "/list: Xem danh sách tài khoản đã đăng ký.\n"
   
    text += "/update: sửa số điện thoại người dùng.\n"
    text += "/xoads: xóa danh sách nhiệm vụ hoàn thành.\n"
    text += "/dsruttien: danh sách các đơn rút tiền."
    await message.answer(text)

#hàm xử lí lệnh list
@dp.message_handler(commands=['list'])
async def account_list(message: types.Message):
    user = message.from_user
    if not is_admin(user):
        await message.answer("Bạn không có quyền truy cập vào tính năng này.")
        return

    # Code để lấy danh sách các tài khoản đã đăng ký và trả về kết quả
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    accounts = c.fetchall()
    conn.close()

    text = "Danh sách số điện thoại đã đăng ký:\n"
    for account in accounts:
        try:
            user = await bot.get_chat_member(account[0], account[0])
            name = user.user.first_name + " " + user.user.last_name
        except Exception:
            name = "Unknown"

        text += f'<a href="tg://user?id={account[0]}">{name}</a> - <a href="tel:{account[1]}">{account[1]}</a>\n'

    await message.answer(text, parse_mode="HTML")

  
#hàm xử lí lệnh /update
@dp.message_handler(commands=['update'])
async def update_phone_number(message: types.Message):
    user = message.from_user
    if not is_admin(user):
        await message.answer("Bạn không có quyền truy cập vào tính năng này.")
        return
    
    # Lấy số điện thoại cần sửa
    if len(message.text.split()) != 3:
        await message.answer("Vui lòng nhập lệnh như này để sửa số điện thoại:\n /update (Số điện thoại cũ) (Số điện thoại mới)")
        return
    old_phone_number = message.text.split()[1]
    new_phone_number = message.text.split()[2]
    
    # Lấy tài khoản cần sửa
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone_number=?", (old_phone_number,))
    account = c.fetchone()
    conn.close()
    
    # Kiểm tra tài khoản có tồn tại hay không
    if not account:
        await message.answer("Không tìm thấy tài khoản nào có số điện thoại này.")
        return
    
    # Kiểm tra số điện thoại mới đã có ai sử dụng chưa
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone_number=?", (new_phone_number,))
    account = c.fetchone()
    conn.close()
    if account:
        await message.answer("Số điện thoại mới đã được sử dụng bởi một tài khoản khác.")
        return
    
    # Cập nhật số điện thoại mới
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET phone_number=? WHERE phone_number=?", (new_phone_number, old_phone_number))
    conn.commit()
    conn.close()
    
    await message.answer(f"Sửa số điện thoại thành công từ {old_phone_number} thành {new_phone_number}.")

# Hàm xử lý lệnh setmoney


# Khởi tạo một handler mới để xử lý lệnh /dsruttien chỉ dành cho admin
@dp.message_handler(commands=['dsruttien'])
async def show_withdraw_requests_admin(message: types.Message):
    user = message.from_user
    if not is_admin(user):
        await message.answer("Bạn không có quyền truy cập vào tính năng này.")
        return

    # Kết nối đến cơ sở dữ liệu
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Truy vấn danh sách các đơn rút tiền
    c.execute("SELECT amount, phone_number, telegram_username, timestamp FROM withdraw")
    withdraw_requests = c.fetchall()

    # Nếu không có đơn rút tiền nào, thông báo cho admin
    if not withdraw_requests:
        await message.answer("Không có đơn rút tiền nào.")

    # Nếu có đơn rút tiền, gửi danh sách này cho admin
    else:
        # Tạo tên file chứa danh sách các đơn rút tiền dưới dạng "withdraw_requests_DDMMYYYY_HHMMSS.txt"
        file_name = datetime.now().strftime("%d%m%Y") + ".txt"

        # Tạo file và lưu danh sách các đơn rút tiền vào file này
        with open(file_name, "w") as f:
            f.write("Danh sách đơn rút tiền:\n")
            for i, request in enumerate(withdraw_requests, start=1):
                f.write(f"{i}. {request[0]} - {request[1]} - {request[2]} - {request[3]}\n")

        # Gửi danh sách các đơn rút tiền cho admin dưới dạng file đính kèm
        with open(file_name, "rb") as f:
            await message.answer_document(f)

        # Xóa toàn bộ đơn rút tiền đã gửi đi
        c.execute("DELETE FROM withdraw")

        # Lưu lại thay đổi vào cơ sở dữ liệu
        conn.commit()

    # Đóng kết nối đến cơ sở dữ liệu
    conn.close()

#xóa danh sách nhiệm vụ hoàn thành
@dp.message_handler(commands=['xoads'])
async def clear_completed_tasks(message: types.Message):
    user = message.from_user
    if not is_admin(user):
        await message.answer("Bạn không có quyền truy cập vào tính năng này.")
        return
    c.execute("DELETE FROM completed_tasks")
    conn.commit()
    await message.answer("Đã xóa danh sách nhiệm vụ hoàn thành.")

  
completed_tasks = set()  # Danh sách các nhiệm vụ đã hoàn thành
user_task_id = None

#nút button
button1 = KeyboardButton("🏠 Menu Chính")
button2 = KeyboardButton("💳 Tài Khoản")
button3 = KeyboardButton("🎮 Trò Chơi")
button4 = KeyboardButton("💵 Kiếm Tiền")
button5 = KeyboardButton("❓ Hướng Dẫn")
button6 = KeyboardButton("👉Nhận Nhiệm Vụ👈")
button7 = KeyboardButton("💲Rút tiền")

keyboard1 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("💳 Tài Khoản").add("💵 Kiếm Tiền", "🎮 Trò Chơi").add("❓ Hướng Dẫn")

kiemtien = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("👉Nhận Nhiệm Vụ👈", "🎮 Trò Chơi").add("💳 Tài Khoản", "🏠 Menu Chính")

taikhoan = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("💲Rút tiền").add(button4, button3).add("🏠 Menu Chính")

@dp.message_handler()
async def kb_answer(message: types.Message):
    global completed_tasks, reset_time, user_task_id, balance, hoo_balance
  
    if message.text == '🏠 Menu Chính':
        await message.answer(f"Chào mừng bạn đến với {bot_ten} \n. Hãy bắt đầu tham gia kiếm tiền ngay, tiếp tục chọn các chức năng bên dưới!", reply_markup=keyboard1)


    if message.text == '💵 Kiếm Tiền':
        await message.answer("Tiếp tục các lựa chọn bên dưới để tham gia kiếm tiền!", reply_markup=kiemtien)
  
    elif message.text == '💳 Tài Khoản':
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        user_id = message.from_user.id 
        name = f"{first_name} {last_name}" if last_name else first_name
        chat_id = message.chat.id
        c.execute("SELECT name, phone_number, balance FROM users WHERE user_id = ?", (chat_id,))
        result = c.fetchone()
        if result:
            name_db, phone_number, balance = result
            await message.answer(f"<b>☠️ Thông tin tài khoản ☠️</b>\nXin chào <b>{name}</b>👋 \nSố momo: <b>{phone_number}</b> \nSố dư: <b>{balance} VND</b>", parse_mode="HTML", reply_markup=taikhoan)
        else:
            await message.answer(f"Chào {name}, bạn chưa đăng ký tài khoản!") 

    if message.text == '👉Nhận Nhiệm Vụ👈':

        # Lấy danh sách các nhiệm vụ chưa hoàn thành
        incomplete_tasks = {}
        for task_id, task_info in tasks.items():
            if not c.execute("SELECT * FROM completed_tasks WHERE task_id = ? AND user_id = ?", (task_id, message.chat.id)).fetchone():
                incomplete_tasks[task_id] = task_info

        if not incomplete_tasks:
            await message.answer('Bạn đã làm hết các nhiệm vụ.')
            return

        # Chọn một nhiệm vụ ngẫu nhiên từ danh sách các nhiệm vụ chưa hoàn thành
        task_id, task_info = random.choice(list(incomplete_tasks.items()))
        link, code, reward = task_info['link'], task_info['code'], task_info['reward']
        link_button = f'<a href="{link}">click</a>'
        await message.answer(f"Nhận nhiệm vụ thành công\nTiền thưởng {reward} VND\nLink nhiệm vụ: {link_button} để làm nhiệm vụ.\nVui lòng nhập mã nhiệm vụ:", parse_mode=ParseMode.HTML)
        user_task_id = task_id  # Lưu task_id hiện tại cho việc kiểm tra mã xác nhận

    elif message.text.startswith('Mã'):
        code = message.text.split('Mã', 1)[1].strip()
        if user_task_id is None:
            await message.answer("Bạn chưa nhận nhiệm vụ. Vui lòng nhập '👉Nhận Nhiệm Vụ👈' để nhận nhiệm vụ.")
            return

        elif code != tasks[user_task_id]['code']:
            await message.answer("Mã xác nhận không hợp lệ. Vui lòng thử lại.")
            return

        # Kiểm tra xem nhiệm vụ đã hoàn thành chưa
        c.execute("SELECT * FROM completed_tasks WHERE task_id = ? AND user_id = ?", (user_task_id, message.chat.id))
        if c.fetchone():
            await message.answer("Bạn đã hoàn thành nhiệm vụ này rồi.")
            return

        # Lưu thông tin nhiệm vụ hoàn thành vào database
        c.execute("INSERT INTO completed_tasks (user_id, task_id) VALUES (?, ?)", (message.chat.id, user_task_id))
        conn.commit()

        reward = tasks[user_task_id]['reward']
        # Cộng tiền thưởng vào tài khoản người dùng
        user_id = message.chat.id
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
        conn.commit()
        await message.answer(f"Chúc mừng bạn đã hoàn thành nhiệm vụ và nhận được {reward} đồng.")
        return

keep_alive()
async def main():
    # Khởi động bot
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
    executor.start_polling(dp, skip_updates=True)
  
#Đóng kết nối với database
conn.close()
