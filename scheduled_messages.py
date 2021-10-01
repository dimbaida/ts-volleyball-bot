import telebot
import config
import db_commands as db

bot = telebot.TeleBot(config.bot_token)


def send_event_reminder():
    date = db.upcoming_events()[0][0]
    event_type = db.upcoming_events()[0][1]
    naming = {'train': 'тренировку \U0001F3D0', 'game': 'игру \U0001F3C5'}
    event_type = naming[event_type]

    telegram_ids = db.active_telegram_ids()
    date_str = date.strftime("%d.%m.%Y")
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{date}')
    btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{date}')
    keyboard.row(btn_01, btn_02)

    for telegram_id in telegram_ids:
        if not db.check_attendance(telegram_id, date):
            print(f'[INFO] Sending info to {telegram_id}')
            bot.send_message(telegram_id, f'<code>Придешь на {event_type} {date_str}?</code>',
                             reply_markup=keyboard,
                             parse_mode='HTML',
                             disable_notification=True)
