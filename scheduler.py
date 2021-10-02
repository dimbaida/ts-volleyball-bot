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
    print("[INFO] Starting the scheduled event reminder")
    event = db.upcoming_events()[0]
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'YES::{event.id}')
    btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'NO::{event.id}')
    keyboard.row(btn_01, btn_02)
    players = db.get_active_players()
    players_unchecked = ''
    for player in players:
        if player.check_attendance(event.date) is None:
            print(f'[INFO] Sending reminder to {player.name} {player.lastname}')
            bot.send_message(381956774, f'<code>Определись с посещением: {event.icon}  {event.date_formatted}</code>',
                             reply_markup=keyboard,
                             parse_mode='HTML',
                             disable_notification=True)
            players_unchecked += f"{player.name} {player.lastname}\n"
    return players_unchecked
