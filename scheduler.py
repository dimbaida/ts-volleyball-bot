import logging
import telebot
import config
import datetime
from common_constants import ICONS
import db_commands as db

logging.basicConfig(filename='.log',
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s >> %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')


def send_event_reminder() -> None:
    """
    Sends the reminder to players who didn't yet make any decision on the nearest upcoming event
    """
    events = db.upcoming_events()
    if events:
        event = events[0]
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('ТАК', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:yes')
        btn_02 = telebot.types.InlineKeyboardButton('НІ', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:no')
        keyboard.row(btn_01, btn_02)
        bot = telebot.TeleBot(config.bot_token)
        for player in db.get_active_players():
            if player.check_attendance(event.id) is None:
                event_text = f"Нагадування: {event.icon} {event.date_formatted}"
                if event.note:
                    event_text += f"\n{event.note}"
                if event.type == 'train' or (event.type == 'game' and player.team):
                    logging.info(f'Sending reminder [{event.id}]{event.date_formatted} to [{player.id}]{player.lastname} {player.name}')
                    try:
                        bot.send_message(player.telegram_id,
                                         f'<code>{event_text}</code>',
                                         reply_markup=keyboard,
                                         parse_mode='HTML')
                    except telebot.apihelper.ApiTelegramException as e:
                        logging.error(f'Failed to send message to [{player.id}]{player.lastname} {player.name}: {e}')


def send_birthday_reminder() -> None:
    """
    Sends the reminder to the group about players who have birthday today
    """
    players = db.get_all_players()
    today = datetime.datetime.now()
    bot = telebot.TeleBot(config.bot_token)
    for player in players:
        if player.birthdate.month == today.month and player.birthdate.day == today.day:
            logging.info(f"[{player.id}]{player.lastname} {player.name} birthday")
            bot.send_message(config.telegram_group_id,
                             f"<code>{player.name} {player.lastname} сьогодні святкує свій день народження! {ICONS['party']}</code>",
                             parse_mode='HTML')
