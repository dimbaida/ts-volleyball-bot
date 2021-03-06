import telebot
import config
import datetime
from common_constants import ICONS
import db_commands as db


def send_event_reminder() -> None:
    """
    Sends the reminder to players who didn't yet make any decision on the nearest upcoming event
    """
    print("[INFO] Starting the scheduled event reminder")
    events = db.upcoming_events()
    if events:
        event = events[0]
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:yes')
        btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:no')
        keyboard.row(btn_01, btn_02)
        players = db.get_active_players()
        bot = telebot.TeleBot(config.bot_token)
        for player in players:
            if player.check_attendance(event.date) is None:
                print(f'[INFO] Sending reminder on {event.date} to {player.name} {player.lastname}')
                event_text = f"Напоминание: {event.icon} {event.date_formatted}"
                if event.note:
                    event_text += f"\n{event.note}"
                bot.send_message(player.telegram_id,
                                 f'<code>{event_text}</code>',
                                 reply_markup=keyboard,
                                 parse_mode='HTML')


def send_birthday_reminder() -> None:
    """
    Sends the reminder to the group about players who have birthday today
    """
    players = db.get_all_players()
    today = datetime.datetime.now()
    bot = telebot.TeleBot(config.bot_token)
    for player in players:
        print(f"[INFO] Checking birthday {player.name} {player.lastname} -> {player.birthdate}")
        if player.birthdate.month == today.month and player.birthdate.day == today.day:
            print("[INFO] Date match. Sending to chat")
            bot.send_message(config.telegram_group_id,
                             f"<code>{player.name} {player.lastname} празднует сегодня день рождения! {ICONS['party']}</code>",
                             parse_mode='HTML')
    print(f"[INFO] Birthdays check finished")
