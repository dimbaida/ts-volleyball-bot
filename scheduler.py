import telebot
import config
import db_commands as db
import common_constants as cc

bot = telebot.TeleBot(config.bot_token)


def send_event_reminder() -> str:
    """
    Sends the reminder to players who didn't yet make any decision on the nearest upcoming event
    :return: Players list in string format: "name lastname\n name lastname\n ... "
    """
    event_date = db.upcoming_events()[0][0]
    event_type = db.upcoming_events()[0][1]
    telegram_ids = db.active_telegram_ids()
    date_str = event_date.strftime("%d.%m.%Y")
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{event_date}:{event_type}')
    btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{event_date}:{event_type}')
    keyboard.row(btn_01, btn_02)

    unchecked_players = []
    for telegram_id in telegram_ids:
        if not db.check_attendance(telegram_id, event_date):
            print(f'[INFO] Sending reminder to {telegram_id}')
            bot.send_message(telegram_id, f'<code>Определись с посещением: {cc.ICONS[event_type]} {date_str}</code>',
                             reply_markup=keyboard,
                             parse_mode='HTML',
                             disable_notification=True)
            player = db.player_by_telegram_id(telegram_id)
            player = ' '.join(player)
            unchecked_players.append(player)
    unchecked_players = '\n'.join(unchecked_players)
    return unchecked_players


def test():
    print('1111')