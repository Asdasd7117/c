# ═══════════════════════════════════════════════════════════════
#  بوت شحن الألعاب والتطبيقات الاحترافي | @Charging_Bot_4
#  تم تهيئة الكود بإيموجي ملون + اقتباسات + تنسيق جمالي
# ═══════════════════════════════════════════════════════════════

import telebot
from telebot import types
import sqlite3
from datetime import datetime
import json
import os
import re
import time
from telebot.types import ForceReply
from datetime import datetime

# قائمة المشرفين
ADMINS = [5504502257]

# تهيئة البوت
bot = telebot.TeleBot('8528791257:AAHCaCihNoTd0RV_CSl0sDyU_3YlH2GojDk')

# إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect('games_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الألعاب والتطبيقات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            type TEXT DEFAULT 'game', -- 'game' أو 'app'
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الفئات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            category_name TEXT,
            price INTEGER,
            FOREIGN KEY (game_id) REFERENCES games (game_id)
        )
    ''')
    
    # جدول الطلبات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_id INTEGER,
            category_id INTEGER,
            game_user_id TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (game_id) REFERENCES games (game_id),
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
        )
    ''')
    
    # جدول طرق الشحن (مع العملة)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_methods (
            method_id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT,
            message_text TEXT,
            currency TEXT DEFAULT 'SYP', -- 'SYP' أو 'USD'
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول طلبات الشحن
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recharge_requests (
            recharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method_id INTEGER,
            transaction_info TEXT,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'pending',
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (method_id) REFERENCES payment_methods (method_id)
        )
    ''')
    
    # جدول سعر الصرف
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rate (
            id INTEGER PRIMARY KEY,
            rate REAL DEFAULT 15000,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # إضافة سعر الصرف الافتراضي
    cursor.execute('INSERT OR IGNORE INTO exchange_rate (id, rate) VALUES (1, 15000)')
    
    conn.commit()
    conn.close()

init_db()

# القناة المطلوبة للاشتراك
REQUIRED_CHANNEL = '@Charging_Bot_4'

# التحقق من اشتراك المستخدم
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return False

# إضافة مستخدم جديد
def add_user(user_id, username):
    conn = sqlite3.connect('games_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

# القائمة الرئيسية (مع إيموجي Unicode)
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('شحن الألعاب', 'شحن التطبيقات')
    markup.add('رصيدي', 'شحن الرصيد')
    markup.add('الدعم الفني', 'معلومات البوت')
    return markup

# قائمة الألعاب أو التطبيقات
def games_menu(game_type='game'):
    conn = sqlite3.connect('games_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT game_id, game_name FROM games WHERE type = ?', (game_type,))
    games = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for game_id, game_name in games:
        markup.add(types.InlineKeyboardButton(f'{game_name}', callback_data=f'game_{game_id}'))
    
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='back_to_main_menu'))
    return markup

# قائمة الفئات
def categories_menu(game_id):
    conn = sqlite3.connect('games_bot.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT category_id, category_name, price 
                      FROM categories WHERE game_id = ?''', (game_id,))
    categories = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for cat_id, cat_name, price in categories:
        markup.add(types.InlineKeyboardButton(
            f'{cat_name} - {price:,} ل.س', 
            callback_data=f'category_{cat_id}'
        ))
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='back_to_games'))
    return markup

# قائمة طرق الشحن
def payment_methods_menu():
    conn = sqlite3.connect('games_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT method_id, method_name, currency FROM payment_methods')
    methods = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for method_id, method_name, currency in methods:
        icon = 'USDT' if currency == 'USD' else 'ل.س'
        markup.add(types.InlineKeyboardButton(
            f'{method_name} [{icon}]', 
            callback_data=f'payment_method_{method_id}'
        ))
    markup.add(types.InlineKeyboardButton('رجوع', callback_data='back_to_main'))
    return markup

# إضافة رصيد للمستخدم
def process_add_balance_amount(message, user_id):
    try:
        amount = int(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f'تم إضافة {amount:,} ل.س للمستخدم {user_id}', parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال مبلغ صحيح!', parse_mode='HTML')

# إضافة طريقة شحن جديدة
def process_add_payment_method_name(message):
    method_name = message.text
    user_data[message.from_user.id] = {'new_method_name': method_name}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('ليرة سورية', callback_data='currency_SYP'),
        types.InlineKeyboardButton('دولار أمريكي', callback_data='currency_USD')
    )
    
    bot.send_message(
        message.chat.id,
        'اختر العملة لهذه الطريقة:',
        reply_markup=markup,
        parse_mode='HTML'
    )

def process_add_payment_method_currency(call):
    user_id = call.from_user.id
    currency = call.data.split('_')[1]
    user_data[user_id]['currency'] = currency
    
    msg = bot.send_message(
        call.message.chat.id,
        'الآن أرسل رسالة الشرح التي ستظهر للمستخدم:\n\nيمكنك استخدام:\n<code>للتنسيق</code>\n<blockquote>للاقتباس</blockquote>',
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_add_payment_method_message)

def process_add_payment_method_message(message):
    user_id = message.from_user.id
    if user_id in user_data and 'new_method_name' in user_data[user_id]:
        method_name = user_data[user_id]['new_method_name']
        message_text = message.text
        currency = user_data[user_id]['currency']
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO payment_methods (method_name, message_text, currency) VALUES (?, ?, ?)', 
                      (method_name, message_text, currency))
        conn.commit()
        conn.close()
        
        del user_data[user_id]
        
        bot.send_message(
            message.chat.id,
            f'تم إضافة طريقة الشحن "{method_name}" بنجاح [{currency}]',
            parse_mode='HTML'
        )

# حذف طريقة شحن
def process_delete_payment_method(message):
    try:
        method_id = int(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM payment_methods WHERE method_id = ?', (method_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, 'تم حذف طريقة الشحن', parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال رقم صحيح!', parse_mode='HTML')

# لوحة تحكم المشرفين
def admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('إضافة لعبة', callback_data='admin_add_game'),
        types.InlineKeyboardButton('إضافة تطبيق', callback_data='admin_add_app')
    )
    markup.add(
        types.InlineKeyboardButton('حذف لعبة/تطبيق', callback_data='admin_delete_game'),
        types.InlineKeyboardButton('إضافة فئة', callback_data='admin_add_category')
    )
    markup.add(
        types.InlineKeyboardButton('حذف فئة', callback_data='admin_delete_category'),
        types.InlineKeyboardButton('إدارة طرق الشحن', callback_data='admin_payment_methods')
    )
    markup.add(
        types.InlineKeyboardButton('إضافة رصيد', callback_data='admin_add_balance'),
        types.InlineKeyboardButton('رسالة جماعية', callback_data='admin_broadcast')
    )
    markup.add(
        types.InlineKeyboardButton('إحصائيات', callback_data='admin_stats'),
        types.InlineKeyboardButton('الطلبات', callback_data='admin_orders')
    )
    markup.add(
        types.InlineKeyboardButton('سعر صرف الدولار', callback_data='admin_exchange_rate')
    )
    return markup

# لوحة إدارة طرق الشحن
def admin_payment_methods_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('إضافة طريقة شحن', callback_data='admin_add_payment_method'),
        types.EInlineKeyboardButton('حذف طريقة شحن', callback_data='admin_delete_payment_method')
    )
    markup.add(
        types.InlineKeyboardButton('طلبات شحن الرصيد', callback_data='admin_recharge_requests'),
        types.InlineKeyboardButton('رجوع', callback_data='admin_panel')
    )
    return markup

# التحقق من كون المستخدم مشرف
def is_admin(user_id):
    return user_id in ADMINS

# ═══════════════════════════════════════════════════════════════
#  بدء تشغيل البوت
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بدون معرف"
    
    add_user(user_id, username)
    
    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('انضم للقناة', url=f'https://t.me/{REQUIRED_CHANNEL[1:]}'))
        markup.add(types.InlineKeyboardButton('تحقق من الاشتراك', callback_data='check_subscription'))
        
        bot.send_message(
            message.chat.id,
            f'''<blockquote>أهلاً بك {message.from_user.first_name}!

يجب عليك الانضمام إلى قناتنا أولاً لاستخدام البوت:</blockquote>

{REQUIRED_CHANNEL}''',
            reply_markup=markup,
            parse_mode='HTML'
        )
        return
    
    if is_admin(user_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('لوحة التحكم', 'شحن الألعاب', 'شحن التطبيقات')
        bot.send_message(message.chat.id, 'أهلاً بك أيها المشرف!', reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 
                        f'''<blockquote>أهلاً بك {message.from_user.first_name}!

بوت شحن الألعاب والتطبيقات الرسمي
شحن جميع الألعاب والتطبيقات بأفضل الأسعار</blockquote>''', 
                        reply_markup=main_menu(),
                        parse_mode='HTML')

# معالجة الرسائل النصية
user_data = {}

# ═══════════════════════════════════════════════════════════════
#  وظائف المشرفين
# ═══════════════════════════════════════════════════════════════

def process_add_game(message, game_type='game'):
    game_name = message.text
    conn = sqlite3.connect('games_bot.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO games (game_name, type) VALUES (?, ?)', (game_name, game_type))
        conn.commit()
        if game_type == 'game':
            bot.send_message(message.chat.id, f'تم إضافة اللعبة {game_name} بنجاح', parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, f'تم إضافة التطبيق {game_name} بنجاح', parse_mode='HTML')
    except sqlite3.IntegrityError:
        bot.send_message(message.chat.id, 'هذا الاسم موجود مسبقاً!', parse_mode='HTML')
    conn.close()

def process_add_category_name(message, game_id):
    category_name = message.text
    msg = bot.send_message(message.chat.id, 'الآن أرسل سعر الفئة:', parse_mode='HTML')
    bot.register_next_step_handler(msg, process_add_category_price, game_id, category_name)

def process_add_category_price(message, game_id, category_name):
    try:
        price = int(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (game_id, category_name, price) VALUES (?, ?, ?)', 
                      (game_id, category_name, price))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, 
                        f'تم إضافة الفئة "{category_name}" بسعر {price:,} ل.س', 
                        parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال سعر صحيح!', parse_mode='HTML')

def process_delete_game(message):
    try:
        game_id = int(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM categories WHERE game_id = ?', (game_id,))
        cursor.execute('DELETE FROM games WHERE game_id = ?', (game_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, 'تم الحذف بنجاح', parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال رقم صحيح!', parse_mode='HTML')

def process_delete_category(message):
    try:
        category_id = int(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categories WHERE category_id = ?', (category_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, 'تم حذف الفئة', parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال رقم صحيح!', parse_mode='HTML')

def process_add_balance_user(message):
    try:
        user_id = int(message.text)
        msg = bot.send_message(message.chat.id, 'أرسل المبلغ الذي تريد إضافته:', parse_mode='HTML')
        bot.register_next_step_handler(msg, process_add_balance_amount, user_id)
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال أي دي مستخدم صحيح!', parse_mode='HTML')

# ═══════════════════════════════════════════════════════════════
#  معالجة الأزرار (Inline)
# ═══════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if not check_subscription(user_id):
        bot.answer_callback_query(call.id, 'يجب الاشتراك في القناة أولاً!')
        return
    
    if call.data == 'check_subscription':
        if check_subscription(user_id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            start_command(call.message)
        else:
            bot.answer_callback_query(call.id, 'لم تشترك بعد!')
    
    elif call.data == 'back_to_main':
        bot.edit_message_text(
            'الرجاء اختيار القسم المطلوب:',
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(),
            parse_mode='HTML'
        )

    # ═══════════════════════════════════════════════════════════════
    #  إدارة طرق الشحن
    # ═══════════════════════════════════════════════════════════════

    elif call.data == 'admin_payment_methods':
        if is_admin(user_id):
            bot.edit_message_text(
                'لوحة إدارة طرق الشحن',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=admin_payment_methods_panel(),
                parse_mode='HTML'
            )

    elif call.data == 'admin_add_payment_method':
        if is_admin(user_id):
            msg = bot.edit_message_text(
                'أرسل اسم طريقة الشحن الجديدة:',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_add_payment_method_name)

    elif call.data.startswith('currency_'):
        if is_admin(user_id):
            process_add_payment_method_currency(call)

    elif call.data == 'admin_delete_payment_method':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT method_id, method_name, currency FROM payment_methods')
            methods = cursor.fetchall()
            conn.close()
            
            if methods:
                methods_list = "\n".join([f"{m[0]} - {m[1]} [{m[2]}]" for m in methods])
                msg = bot.edit_message_text(
                    f'اختر رقم طريقة الشحن التي تريد حذفها:\n\n{methods_list}',
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                bot.register_next_step_handler(msg, process_delete_payment_method)
            else:
                bot.answer_callback_query(call.id, 'لا توجد طرق شحن!')

    elif call.data == 'admin_exchange_rate':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT rate FROM exchange_rate WHERE id = 1')
            rate = cursor.fetchone()[0]
            conn.close()
            
            msg = bot.send_message(
                call.message.chat.id,
                f'سعر الصرف الحالي: 1$ = {rate:,} ل.س\n\nأرسل السعر الجديد:',
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_exchange_rate)

    elif call.data == 'admin_recharge_requests':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('''SELECT r.recharge_id, r.user_id, r.amount, r.currency, m.method_name, r.transaction_info, r.status 
                              FROM recharge_requests r 
                              JOIN payment_methods m ON r.method_id = m.method_id 
                              WHERE r.status = "pending"''')
            requests = cursor.fetchall()
            conn.close()
            
            if requests:
                for req in requests:
                    recharge_id, customer_id, amount, currency, method_name, transaction_info, status = req
                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton('قبول الطلب', callback_data=f'admin_accept_recharge_{recharge_id}'),
                        types.InlineKeyboardButton('رفض الطلب', callback_data=f'admin_reject_recharge_{recharge_id}')
                    )
                    
                    bot.send_message(
                        call.message.chat.id,
                        f'''طلب شحن رصيد جديد:
رقم الطلب: {recharge_id}
المستخدم: {customer_id}
الطريقة: {method_name}
المبلغ: {amount} {currency}
معلومات التحويل: {transaction_info}''',
                        reply_markup=markup,
                        parse_mode='HTML'
                    )
            else:
                bot.answer_callback_query(call.id, 'لا توجد طلبات شحن رصيد معلقة')

    # ═══════════════════════════════════════════════════════════════
    #  اختيار طريقة الشحن
    # ═══════════════════════════════════════════════════════════════

    elif call.data.startswith('payment_method_'):
        method_id = int(call.data.split('_')[2])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT method_name, message_text, currency FROM payment_methods WHERE method_id = ?', (method_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            method_name, message_text, currency = result
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('إلغاء', callback_data='cancel_recharge'))
            
            bot.edit_message_text(
                message_text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            user_data[user_id] = {
                'recharge_method_id': method_id,
                'recharge_method_name': method_name,
                'currency': currency,
                'step': 'waiting_transaction_info'
            }

    elif call.data == 'cancel_recharge':
        if user_id in user_data and 'recharge_method_id' in user_data[user_id]:
            del user_data[user_id]
        
        bot.edit_message_text(
            'تم إلغاء عملية الشحن',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )

    # ═══════════════════════════════════════════════════════════════
    #  قبول أو رفض طلب الشحن
    # ═══════════════════════════════════════════════════════════════

    elif call.data.startswith('admin_accept_recharge_'):
        recharge_id = int(call.data.split('_')[3])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, amount, currency FROM recharge_requests WHERE recharge_id = ?', (recharge_id,))
        result = cursor.fetchone()
        
        if result:
            customer_id, amount, currency = result
            
            cursor.execute('SELECT rate FROM exchange_rate WHERE id = 1')
            rate = cursor.fetchone()[0]
            
            final_amount = amount if currency == 'SYP' else int(amount * rate)
            
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (final_amount, customer_id))
            cursor.execute('UPDATE recharge_requests SET status = "completed" WHERE recharge_id = ?', (recharge_id,))
            conn.commit()
            
            try:
                bot.send_message(
                    customer_id,
                    f'تم قبول طلب شحن الرصيد بنجاح!\nتم إضافة {final_amount:,} ل.س إلى رصيدك',
                    parse_mode='HTML'
                )
            except:
                pass
            
            bot.edit_message_text(
                f'تم قبول طلب الشحن #{recharge_id}\nالمبلغ: {amount} {currency} → {final_amount:,} ل.س',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        
        conn.close()

    elif call.data.startswith('admin_reject_recharge_'):
        recharge_id = int(call.data.split('_')[3])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, amount, currency FROM recharge_requests WHERE recharge_id = ?', (recharge_id,))
        result = cursor.fetchone()
        
        if result:
            customer_id, amount, currency = result
            
            cursor.execute('UPDATE recharge_requests SET status = "rejected" WHERE recharge_id = ?', (recharge_id,))
            conn.commit()
            
            try:
                bot.send_message(
                    customer_id,
                    f'تم رفض طلب شحن الرصيد\nالمبلغ: {amount} {currency}\nللاستفسار تواصل مع الدعم الفني',
                    parse_mode='HTML'
                )
            except:
                pass
            
            bot.edit_message_text(
                f'تم رفض طلب الشحن #{recharge_id}',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        
        conn.close()

    # ═══════════════════════════════════════════════════════════════
    #  التنقل بين الأقسام
    # ═══════════════════════════════════════════════════════════════

    elif call.data == 'back_to_games':
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT type FROM games ORDER BY game_id LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        
        game_type = result[0] if result else 'game'
        
        if game_type == 'game':
            bot.edit_message_text(
                'اختر اللعبة التي تريد شحنها:',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=games_menu('game'),
                parse_mode='HTML'
            )
        else:
            bot.edit_message_text(
                'اختر التطبيق الذي تريد شحنه:',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=games_menu('app'),
                parse_mode='HTML'
            )
    
    elif call.data.startswith('game_'):
        game_id = int(call.data.split('_')[1])
        bot.edit_message_text(
            'اختر الفئة المطلوبة:',
            call.message.chat.id,
            call.message.message_id,
            reply_markup=categories_menu(game_id),
            parse_mode='HTML'
        )
    
    elif call.data.startswith('category_'):
        category_id = int(call.data.split('_')[1])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT c.category_name, c.price, g.game_name, g.type 
                          FROM categories c 
                          JOIN games g ON c.game_id = g.game_id 
                          WHERE c.category_id = ?''', (category_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            category_name, price, game_name, game_type = result
            item_type = "التطبيق" if game_type == 'app' else "اللعبة"
            
            bot.edit_message_text(
                f'''{item_type}: {game_name}
الفئة: {category_name}
السعر: {price:,} ل.س

الرجاء إرسال الـ ID الخاص بك في {item_type}:''',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            
            user_data[user_id] = {
                'game_name': game_name,
                'category_name': category_name,
                'price': price,
                'category_id': category_id,
                'type': game_type
            }

    # ═══════════════════════════════════════════════════════════════
    #  لوحة التحكم + إضافة وحذف
    # ═══════════════════════════════════════════════════════════════

    elif call.data == 'admin_panel':
        if is_admin(user_id):
            bot.edit_message_text(
                'لوحة تحكم المشرفين',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=admin_panel(),
                parse_mode='HTML'
            )
    
    elif call.data == 'admin_add_game':
        if is_admin(user_id):
            msg = bot.edit_message_text(
                'أرسل اسم اللعبة الجديدة:',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_add_game, 'game')
    
    elif call.data == 'admin_add_app':
        if is_admin(user_id):
            msg = bot.edit_message_text(
                'أرسل اسم التطبيق الجديد:',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_add_game, 'app')
    
    elif call.data == 'admin_add_category':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT game_id, game_name, type FROM games')
            games = cursor.fetchall()
            conn.close()
            
            if games:
                markup = types.InlineKeyboardMarkup()
                for game_id, game_name, game_type in games:
                    icon = 'التطبيق' if game_type == 'app' else 'اللعبة'
                    markup.add(types.InlineKeyboardButton(f'{icon} {game_name}', callback_data=f'select_game_{game_id}'))
                markup.add(types.InlineKeyboardButton('رجوع', callback_data='admin_panel'))
                bot.edit_message_text(
                    'اختر اللعبة أو التطبيق لإضافة الفئة:',
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(call.id, 'لا توجد ألعاب أو تطبيقات!')
    
    elif call.data.startswith('select_game_'):
        game_id = int(call.data.split('_')[2])
        msg = bot.edit_message_text(
            'أرسل اسم الفئة الجديدة:',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        bot.register_next_step_handler(msg, process_add_category_name, game_id)
    
    elif call.data == 'admin_delete_game':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT game_id, game_name, type FROM games')
            games = cursor.fetchall()
            conn.close()
            
            if games:
                games_list = "\n".join([f"{game_id} - {'التطبيق' if game_type == 'app' else 'اللعبة'} {game_name}" for game_id, game_name, game_type in games])
                msg = bot.edit_message_text(
                    f'اختر رقم اللعبة/التطبيق الذي تريد حذفه:\n\n{games_list}',
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                bot.register_next_step_handler(msg, process_delete_game)
            else:
                bot.answer_callback_query(call.id, 'لا توجد ألعاب أو تطبيقات!')
    
    elif call.data == 'admin_delete_category':
        if is_admin(user_id):
            conn = sqlite3.connect('games_bot.db')
            cursor = conn.cursor()
            cursor.execute('''SELECT c.category_id, c.category_name, g.game_name, g.type 
                              FROM categories c 
                              JOIN games g ON c.game_id = g.game_id''')
            categories = cursor.fetchall()
            conn.close()
            
            if categories:
                categories_list = "\n".join([f"{cat_id} - {'التطبيق' if game_type == 'app' else 'اللعبة'} {game_name}: {cat_name}" for cat_id, cat_name, game_name, game_type in categories])
                msg = bot.edit_message_text(
                    f'اختر رقم الفئة التي تريد حذفها:\n\n{categories_list}',
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
                bot.register_next_step_handler(msg, process_delete_category)
            else:
                bot.answer_callback_query(call.id, 'لا توجد فئات!')
    
    elif call.data == 'admin_add_balance':
        if is_admin(user_id):
            msg = bot.edit_message_text(
                'أرسل أي دي المستخدم الذي تريد إضافة رصيد له:',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_add_balance_user)

    # ═══════════════════════════════════════════════════════════════
    #  تأكيد الطلبات
    # ═══════════════════════════════════════════════════════════════

    elif call.data.startswith('confirm_order_'):
        parts = call.data.split('_')
        category_id = int(parts[2])
        game_user_id = parts[3]
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('''SELECT c.price, g.game_name, c setzte_name, g.type 
                          FROM categories c 
                          JOIN games g ON c.game_id = g.game_id 
                          WHERE c.category_id = ?''', (category_id,))
        result = cursor.fetchone()
        
        if result:
            price, game_name, category_name, game_type = result
            item_type = "التطبيق" if game_type == 'app' else "اللعبة"
            
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            user_balance = cursor.fetchone()[0]
            
            if user_balance >= price:
                cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (price, user_id))
                cursor.execute('''INSERT INTO orders (user_id, game_id, category_id, game_user_id, amount) 
                                  SELECT ?, g.game_id, ?, ?, ? 
                                  FROM categories c 
                                  JOIN games g ON c.game_id = g.game_id 
                                  WHERE c.category_id = ?''', 
                              (user_id, category_id, game_user_id, price, category_id))
                order_id = cursor.lastrowid
                conn.commit()
                
                for admin_id in ADMINS:
                    try:
                        markup = types.InlineKeyboardMarkup()
                        markup.add(
                            types.InlineKeyboardButton('تأكيد التنفيذ', callback_data=f'admin_confirm_{order_id}'),
                            types.InlineKeyboardButton('رفض الطلب', callback_data=f'admin_reject_{order_id}')
                        )
                        
                        bot.send_message(
                            admin_id,
                            f'''طلب شحن جديد:
رقم الطلب: {order_id}
المستخدم: {user_id}
{item_type}: {game_name}
الفئة: {category_name}
المبلغ: {price:,} ل.س
ID {item_type}: {game_user_id}''',
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                bot.edit_message_text(
                    'تم إرسال طلبك بنجاح! جاري معالجة الطلب...',
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    f'رصيدك غير كافي!\nرصيدك الحالي: {user_balance:,} ل.س\nالمطلوب: {price:,} ل.س',
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
        
        conn.close()
    
    elif call.data == 'cancel_order':
        bot.edit_message_text(
            'تم إلغاء الطلب',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
    
    elif call.data.startswith('admin_confirm_'):
        order_id = int(call.data.split('_')[2])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('UPDATE orders SET status = "completed" WHERE order_id = ?', (order_id,))
        
        cursor.execute('''SELECT o.user_id, o.amount, g.game_name, c.category_name, g.type 
                          FROM orders o 
                          JOIN categories c ON o.category_id = c.category_id 
                          JOIN games g ON o.game_id = g.game_id 
                          WHERE o.order_id = ?''', (order_id,))
        result = cursor.fetchone()
        
        if result:
            customer_id, amount, game_name, category_name, game_type = result
            item_type = "التطبيق" if game_type == 'app' else "اللعبة"
            
            try:
                bot.send_message(
                    customer_id,
                    f'تم معالجة طلبك بنجاح!\n{game_name} - {category_name}',
                    parse_mode='HTML'
                )
            except:
                pass
            
            bot.edit_message_text(
                f'تم تأكيد الطلب #{order_id} بنجاح',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        
        conn.commit()
        conn.close()
    
    elif call.data.startswith('admin_reject_'):
        order_id = int(call.data.split('_')[2])
        
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, amount FROM orders WHERE order_id = ?', (order_id,))
        result = cursor.fetchone()
        
        if result:
            customer_id, amount = result
            
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, customer_id))
            cursor.execute('UPDATE orders SET status = "rejected" WHERE order_id = ?', (order_id,))
            
            try:
                bot.send_message(
                    customer_id,
                    f'تم رفض طلبك وتم إعادة {amount:,} ل.س إلى رصيدك',
                    parse_mode='HTML'
                )
            except:
                pass
            
            bot.edit_message_text(
                f'تم رفض الطلب #{order_id} وإعادة الرصيد',
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML'
            )
        
        conn.commit()
        conn.close()

# ═══════════════════════════════════════════════════════════════
#  رسائل النص العادية
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        return
    
    if message.text == 'شحن الألعاب':
        bot.send_message(message.chat.id, 
                        'اختر اللعبة التي تريد شحنها:',
                        reply_markup=games_menu('game'),
                        parse_mode='HTML')
    
    elif message.text == 'شحن التطبيقات':
        bot.send_message(message.chat.id, 
                        'اختر التطبيق الذي تريد شحنه:',
                        reply_markup=games_menu('app'),
                        parse_mode='HTML')
    
    elif message.text == 'رصيدي':
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        conn.close()
        
        bot.send_message(message.chat.id, 
                        f'رصيدك الحالي: <b>{balance:,} ل.س</b>',
                        parse_mode='HTML')
    
    elif message.text == 'شحن الرصيد':
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM payment_methods')
        methods_count = cursor.fetchone()[0]
        conn.close()
        
        if methods_count > 0:
            bot.send_message(message.chat.id, 
                            'اختر طريقة الشحن المناسبة:',
                            reply_markup=payment_methods_menu(),
                            parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, 
                            'لا توجد طرق شحن متاحة حالياً',
                            parse_mode='HTML')
    
    elif message.text == 'لوحة التحكم' and is_admin(user_id):
        bot.send_message(message.chat.id, 
                        'لوحة تحكم المشرفين',
                        reply_markup=admin_panel(),
                        parse_mode='HTML')
    
    elif message.text == 'معلومات البوت':
        bot_info = f'''
<b> {message.from_user.first_name}، أهلاً بك في بوت الشحن الرسمي!</b>

<blockquote>بوت شحن الألعاب والتطبيقات

المميزات:
• شحن جميع الألعاب العالمية
• شحن التطبيقات المميزة  
• أسعار تنافسية ومناسبة
• شحن فوري وآمن
• ضمان واسترجاع

طريقة الاستخدام:
1. اشحن رصيدك في البوت
2. اختر اللعبة أو التطبيق
3. حدد الفئة المناسبة
4. تمتع بالشحن الفوري

لماذا تختارنا؟
• دعم فني 24/7
• أمان تام في المعاملات
• سرعة في التنفيذ
• خدمة عملاء متميزة</blockquote>

ابدأ الآن واشحن بأفضل الأسعار!
'''
        bot.send_message(message.chat.id, bot_info, parse_mode='HTML')

    elif message.text == 'الدعم الفني':
        support_message = f'''
<b>مركز الدعم الفني</b>

<blockquote>مرحباً {message.from_user.first_name}!

هل تحتاج مساعدة؟
• مشكلة في شحن لعبة؟
• استفسار حول الرصيد؟
• متابعة طلب؟
• مشكلة تقنية؟

أوقات الدعم:
• 24/7 على مدار الساعة

سيتم الرد عليك في أقرب وقت ممكن</blockquote>

'''
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('تواصل مع الدعم', url='https://wa.me/qr/YV2KEPHAFFPJM1'))
        
        bot.send_message(message.chat.id, support_message, parse_mode='HTML', reply_markup=markup)    
    
    elif user_id in user_data and 'game_name' in user_data[user_id]:
        game_user_id = message.text
        data = user_data[user_id]
        
        item_type = "اللعبة"
        if 'type' in data:
            item_type = "التطبيق" if data['type'] == 'app' else "اللعبة"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('تأكيد الطلب', callback_data=f'confirm_order_{data["category_id"]}_{game_user_id}'),
            types.InlineKeyboardButton('إلغاء', callback_data='cancel_order')
        )
        
        bot.send_message(
            message.chat.id,
            f'''تفاصيل الطلب:
{item_type}: {data["game_name"]}
الفئة: {data["category_name"]}
السعر: {data["price"]:,} ل.س
ID {item_type}: {game_user_id}

الرجاء التأكد من صحة المعلومات قبل التأكيد''',
            reply_markup=markup,
            parse_mode='HTML'
        )
        
        del user_data[user_id]

    elif user_id in user_data and 'step' in user_data[user_id]:
        if user_data[user_id]['step'] == 'waiting_transaction_info':
            transaction_info = message.text
            user_data[user_id]['transaction_info'] = transaction_info
            user_data[user_id]['step'] = 'waiting_amount'
            
            currency = user_data[user_id]['currency']
            unit = 'دولار' if currency == 'USD' else 'ليرة سورية'
            
            msg = bot.send_message(
                message.chat.id,
                f'الآن أرسل المبلغ الذي قمت بتحويله بالـ {unit} :',
                parse_mode='HTML'
            )
            
        elif user_data[user_id]['step'] == 'waiting_amount':
            try:
                amount = float(message.text)
                method_id = user_data[user_id]['recharge_method_id']
                transaction_info = user_data[user_id]['transaction_info']
                currency = user_data[user_id]['currency']
                
                conn = sqlite3.connect('games_bot.db')
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO recharge_requests (user_id, method_id, transaction_info, amount, currency) 
                                  VALUES (?, ?, ?, ?, ?)''', 
                              (user_id, method_id, transaction_info, amount, currency))
                recharge_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                for admin_id in ADMINS:
                    try:
                        markup = types.InlineKeyboardMarkup()
                        markup.add(
                            types.InlineKeyboardButton('قبول الطلب', callback_data=f'admin_accept_recharge_{recharge_id}'),
                            types.InlineKeyboardButton('رفض الطلب', callback_data=f'admin_reject_recharge_{recharge_id}')
                        )
                        
                        bot.send_message(
                            admin_id,
                            f'''طلب شحن رصيد جديد:
رقم الطلب: {recharge_id}
المستخدم: {user_id}
الطريقة: {user_data[user_id]['recharge_method_name']}
المبلغ: {amount} {currency}
معلومات التحويل: {transaction_info}''',
                            reply_markup=markup,
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                del user_data[user_id]
                
                bot.send_message(
                    message.chat.id,
                    'تم إرسال طلبك بنجاح! جاري التحقق من المعلومات...',
                    parse_mode='HTML'
                )
                
            except ValueError:
                bot.send_message(message.chat.id, 'الرجاء إدخال مبلغ صحيح!', parse_mode='HTML')

# ═══════════════════════════════════════════════════════════════
#  تحديث سعر الصرف
# ═══════════════════════════════════════════════════════════════

def process_exchange_rate(message):
    try:
        new_rate = float(message.text)
        conn = sqlite3.connect('games_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE exchange_rate SET rate = ?, last_updated = CURRENT_TIMESTAMP WHERE id = 1', (new_rate,))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f'تم تحديث سعر الصرف إلى: 1$ = {new_rate:,} ل.س', parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, 'الرجاء إدخال رقم صحيح!', parse_mode='HTML')

# ═══════════════════════════════════════════════════════════════
#  تشغيل البوت
# ═══════════════════════════════════════════════════════════════

print("البوت يعمل الآن...")
bot.polling(none_stop=True)
