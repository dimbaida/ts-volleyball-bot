import telebot
import config
import inline_calendar
from datetime import datetime
from common_constants import ICONS
import db_commands as db

bot = telebot.TeleBot(config.bot_token)


@bot.message_handler(commands=['test'], chat_types=['private'])
def test(message):
    """
    Bot command for test purposes. Only available for the developers, telegram ids hardcoded
    If you're a collaborator, add your telegram id into 'developers' var in 'config.py'
    """
    if message.from_user.id in config.developers:
        pass


@bot.message_handler(commands=['get_id'], chat_types=['private'])
def get_id(message):
    bot.send_message(message.from_user.id,
                     f'<code>твой telegram ID: {message.from_user.id}</code>',
                     reply_markup=telebot.types.ReplyKeyboardRemove(),
                     parse_mode='HTML',
                     disable_notification=True)


# TODO: create separate message handler for MANAGE section


@bot.message_handler(commands=['start'], chat_types=['private'])  # TODO: start with the list of events
def start(message):
    if db.check_player(message.from_user.id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"{event.icon}  {event.date_formatted}",
                                                     callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn)
        btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
        keyboard.row(btn_exit)
        bot.send_message(message.from_user.id,
                         '<code>Следующие события:</code>',
                         parse_mode='HTML',
                         reply_markup=keyboard)

    else:
        print(f'[Error] Request from [{message.from_user.id}] — unknown player')
        bot.send_message(message.from_user.id,
                         '<code>Тебя нет в списке игроков. Бот не будет с тобой работать. Для того, чтобы тебя добавили, напиши администратору</code>',
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(commands=['manage'], chat_types=['private'])
def manage(message):
    try:
        player = db.get_player_by_telegram_id(message.from_user.id)
        if player.admin:
            keyboard = telebot.types.InlineKeyboardMarkup()
            for event in db.upcoming_events():
                btn = telebot.types.InlineKeyboardButton(f"Изменить {event.icon} {event.date_formatted}",
                                                         callback_data=f'MANAGE>>EVENT::{event.id}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Создать", callback_data=f'MANAGE>>CREATE::')
            btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
            keyboard.row(btn_new)
            keyboard.row(btn_exit)
            bot.send_message(message.from_user.id,
                             '<code>Следующие события:</code>',
                             parse_mode='HTML',
                             reply_markup=keyboard)

        else:
            print(f'[Error] Request from [{message.from_user.id}] — forbidden to manage, not an admin')
            bot.send_message(message.from_user.id,
                             '<code>Эта секция доступна только пользователям с правами администратора.</code>',
                             parse_mode='HTML',
                             disable_notification=True)

    except IndexError:
        print(f'[Error] Request from [{message.from_user.id}] — unknown player')
        bot.send_message(message.from_user.id,
                         '<code>Тебя нет в списке игроков. Бот не будет с тобой работать. Для того, чтобы тебя добавили, напиши администратору</code>',
                         parse_mode='HTML',
                         disable_notification=True)


@bot.message_handler(content_types=['text'], chat_types=['private'])
def text(message):
    player = db.get_player_by_telegram_id(message.from_user.id)
    menu_state, data = player.read_cache().split('::')
    if menu_state == 'INPUT_GUEST':
        event = db.get_event_by_id(data)
        guest_name = message.text
        event.add_guest(guest_name, player)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn)
        bot.send_message(message.chat.id,
                         f"<code>Гостевой игрок — {guest_name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML',
                         reply_markup=keyboard)
        bot.send_message(config.telegram_group_id,
                         f"<code>{player.lastname} {player.name} добавил гостя {guest_name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML')
        player.purge_cache()

    if menu_state == 'EDIT_GUEST':
        guest = db.get_guest_by_id(data)
        guest_name = message.text
        guest.change_name(guest_name)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn)
        bot.send_message(message.chat.id,
                         f"<code>Новое имя гостя — {guest_name}</code>",
                         parse_mode='HTML',
                         reply_markup=keyboard)
        player.purge_cache()

    if menu_state == 'INPUT_NOTE':
        event = db.get_event_by_id(data)
        note = message.text
        event.update_note(note, player)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
        keyboard.row(btn)
        bot.send_message(message.chat.id,
                         f'<code>Добавлено примечание {event.icon} {event.date_formatted}:\n"{note}"</code>',
                         parse_mode='HTML',
                         reply_markup=keyboard)
        player.purge_cache()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    player = db.get_player_by_telegram_id(call.message.chat.id)
    player.purge_cache()
    print(f'{player.name} {player.lastname} callback', call.data)
    command, data = call.data.split('::')

    # COMMON SECTION

    if command == 'LIST_EVENTS':
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"{event.icon} {event.date_formatted}",
                                                     callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn)
        btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
        keyboard.row(btn_exit)
        bot.edit_message_text('<code>Следующие события:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT':
        event_id, item = data.split(':')
        event = db.get_event_by_id(event_id)
        keyboard = telebot.types.InlineKeyboardMarkup()

        btn_01 = telebot.types.InlineKeyboardButton('YES', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:yes')
        btn_02 = telebot.types.InlineKeyboardButton('NO', callback_data=f'LIST_EVENTS>>EVENT::{event.id}:no')
        btn_03 = telebot.types.InlineKeyboardButton('Гости', callback_data=f'LIST_EVENTS>>EVENT>>GUESTS::{event.id}')
        btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn_01, btn_02)
        keyboard.row(btn_03)
        keyboard.row(btn_back)

        if item == 'yes':
            att = player.check_attendance(event.date)
            if att == False or att is None:
                player.set_decision(event.date, True)
                bot.send_message(config.telegram_group_id,
                                 f"<code>{player.lastname} {player.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted} {ICONS['yes']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        if item == 'no':
            att = player.check_attendance(event.date)
            if att == True or att is None:
                player.set_decision(event.date, False)
                bot.send_message(config.telegram_group_id,
                                 f"<code>{player.lastname} {player.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted} {ICONS['no']}</code>",
                                 parse_mode='HTML',
                                 disable_notification=True)

        event_text = f'{event.icon} {event.date_formatted}:'
        if event.note:
            event_text += f"\n{event.note}"
        event_text += f'\n\n{event.players_formatted()}'

        bot.edit_message_text(f'<code>{event_text}</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS':
        event = db.get_event_by_id(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        guests = event.guests()
        if guests:
            for guest in event.guests():
                btn = telebot.types.InlineKeyboardButton(f"[Гость] {guest.name}", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST::{event.id}:{guest.id}')
                keyboard.row(btn)
            btn_new = telebot.types.InlineKeyboardButton(f"Добавить", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST::{event.id}')
            btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn_new)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>Гости на {event.icon} {event.date_formatted}:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)
        else:
            btn_new = telebot.types.InlineKeyboardButton(f"Добавить", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST::{event.id}')
            btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT::{event.id}:')
            keyboard.row(btn_new)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>{event.icon} {event.date_formatted}\nСписок гостей пуст</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST':
        event_id, guest_id = data.split(':')
        event = db.get_event_by_id(event_id)
        guest = db.get_guest_by_id(guest_id)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton(f"Изменить имя", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>EDIT::{guest.id}')
        btn_02 = telebot.types.InlineKeyboardButton(f"Удалить", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>DELETE::{guest.id}')
        btn_back = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'LIST_EVENTS>>EVENT>>GUESTS::{event.id}')
        keyboard.row(btn_01, btn_02)
        keyboard.row(btn_back)
        bot.edit_message_text(f"<code>[Гость] {guest.name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}:</code>",
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>EDIT':
        guest = db.get_guest_by_id(data)
        player.write_cache(f'EDIT_GUEST::{guest.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Введи новое имя гостя</code>',
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>GUEST>>DELETE':
        guest = db.get_guest_by_id(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'LIST_EVENTS::')
        keyboard.row(btn)
        if guest.added_by == call.message.chat.id or player.admin:
            name = guest.name
            event = db.get_event_by_id(guest.event_id)
            guest.delete()
            bot.edit_message_text(
                f"<code>Гость удален</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)
            bot.send_message(config.telegram_group_id,
                             f"<code>{player.lastname} {player.name} удалил гостя {name} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                             parse_mode='HTML')
        else:
            bot.edit_message_text(
                f"<code>Гостя может удалить только пригласивший его игрок или пользователь с правами администратора</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=keyboard)

    if command == 'LIST_EVENTS>>EVENT>>GUESTS>>INPUT_GUEST':
        event = db.get_event_by_id(data)
        player.write_cache(f'INPUT_GUEST::{event.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Введи имя гостя для {event.icon} {event.date_formatted}</code>',
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    # MANAGE SECTION

    if command == 'MANAGE':
        keyboard = telebot.types.InlineKeyboardMarkup()
        for event in db.upcoming_events():
            btn = telebot.types.InlineKeyboardButton(f"Изменить {event.icon} {event.date_formatted}", callback_data=f'MANAGE>>EVENT::{event.id}')
            keyboard.row(btn)
        btn_new = telebot.types.InlineKeyboardButton(f"Создать", callback_data=f'MANAGE>>CREATE::')
        btn_exit = telebot.types.InlineKeyboardButton(f"Выйти", callback_data=f'EXIT::')
        keyboard.row(btn_new)
        keyboard.row(btn_exit)
        bot.edit_message_text('<code>Следующие события:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>EVENT':
        event = db.get_event_by_id(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton(f"Изменить тип", callback_data=f'MANAGE>>EVENT>>SWITCH_TYPE::{event.id}')
        btn_02 = telebot.types.InlineKeyboardButton(f"Добавить примечание", callback_data=f'MANAGE>>EVENT>>INPUT_NOTE::{event.id}')
        btn_03 = telebot.types.InlineKeyboardButton(f"Удалить", callback_data=f'MANAGE>>EVENT>>DELETE::{event.id}')
        btn_04 = telebot.types.InlineKeyboardButton(f"Назад", callback_data=f'MANAGE::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        keyboard.row(btn_03)
        keyboard.row(btn_04)
        bot.edit_message_text(f'<code>{event.icon} {event.date_formatted}</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>EVENT>>SWITCH_TYPE':
        event = db.get_event_by_id(data)
        old_icon = event.icon
        event.switch_type()
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE>>EVENT::{event.id}')
        keyboard.row(btn)
        bot.edit_message_text(f"<code>Тип события изменен {old_icon} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)
        bot.send_message(config.telegram_group_id,
                         f"<code>{player.name} {player.lastname} изменил {old_icon} {ICONS['right_arrow']} {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML')

    if command == 'MANAGE>>EVENT>>INPUT_NOTE':
        event = db.get_event_by_id(data)
        player.write_cache(f'INPUT_NOTE::{event.id}')
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f'<code>Введи примечание для {event.icon} {event.date_formatted}</code>',
                         parse_mode='HTML',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

    # TODO: Add Clear Note

    if command == 'MANAGE>>EVENT>>DELETE':
        event = db.get_event_by_id(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Да',
                                                    callback_data=f'MANAGE>>EVENT>>DELETE>>CONFIRMED::{event.id}')
        btn_02 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE>>EVENT::{event.id}')
        keyboard.row(btn_01, btn_02)
        bot.edit_message_text(
            f'<code>УВЕРЕН? Все данные о событии будут стерты! {event.icon} {event.date_formatted}</code>',
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard)

    if command == 'MANAGE>>EVENT>>DELETE>>CONFIRMED':
        event = db.get_event_by_id(data)
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
        btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        event.delete()
        print(f'[INFO] Event {event.date} was deleted by {player.lastname} {player.name}')
        bot.edit_message_text(f'<code>Событие {event.icon} {event.date_formatted} удалено</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)

    if command == 'MANAGE>>CREATE':
        bot.edit_message_text(f'<code>Год:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_years(command))

    if command == 'MANAGE>>CREATE>>MONTH':
        year = data
        bot.edit_message_text(f'<code>Месяц:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_months(command, year))

    if command == 'MANAGE>>CREATE>>MONTH>>DAY':
        year, month = data.split('-')
        bot.edit_message_text(f'<code>День:</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=inline_calendar.keyboard_days(command, year, month))

    if command == 'MANAGE>>CREATE>>MONTH>>DAY>>DATE':
        date = data
        year, month, day = date.split('-')
        if day.isdigit() and datetime.strptime(date, '%Y-%m-%d') >= datetime.today():
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_01 = telebot.types.InlineKeyboardButton('Тренировка', callback_data=f'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE::{date}:train')
            btn_02 = telebot.types.InlineKeyboardButton('Игра', callback_data=f'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE::{date}:game')
            btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data="MANAGE::")
            keyboard.row(btn_01, btn_02)
            keyboard.row(btn_back)
            bot.edit_message_text(f'<code>Выбери тип события:</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            btn_back = telebot.types.InlineKeyboardButton('Назад', callback_data="MANAGE::")
            keyboard.add(btn_back)
            bot.edit_message_text(f'<code>Неправильная дата</code>',
                                  call.message.chat.id,
                                  call.message.message_id,
                                  parse_mode='HTML',
                                  reply_markup=keyboard)

    if command == 'MANAGE>>CREATE>>MONTH>>DAY>>DATE>>CREATE':
        date, event_type = data.split(':')
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn_01 = telebot.types.InlineKeyboardButton('Назад', callback_data=f'MANAGE::')
        btn_02 = telebot.types.InlineKeyboardButton('Выйти', callback_data=f'EXIT::')
        keyboard.row(btn_01)
        keyboard.row(btn_02)
        event = db.create_event(date, event_type)
        print(f'[INFO] Event {event.date} was created by {player.lastname} {player.name}')
        bot.edit_message_text(f'<code>Событие создано: {event.icon} {event.date_formatted}</code>',
                              call.message.chat.id,
                              call.message.message_id,
                              parse_mode='HTML',
                              reply_markup=keyboard)
        bot.send_message(config.telegram_group_id,
                         f"<code>{player.lastname} {player.name} создал {event.icon} {event.date_formatted}</code>",
                         parse_mode='HTML')

    # GENERAL

    if command == 'EXIT':
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
