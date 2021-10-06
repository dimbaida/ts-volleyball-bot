import datetime
import calendar
from keyboa import Keyboa, Button
from telebot import types


def keyboard_years(command: str) -> types.InlineKeyboardMarkup():
    """
    Assemble a keyboard with two buttons: current year and the following one
    :param command: the string command for callback_data
    :return: Keyboard with two years
    """
    keyboard = types.InlineKeyboardMarkup()
    year_curr = datetime.datetime.today().year
    btn_year_curr = types.InlineKeyboardButton(year_curr, callback_data=f'{command}>>MONTH::{year_curr}')
    btn_year_next = types.InlineKeyboardButton(year_curr + 1, callback_data=f'{command}>>MONTH::{year_curr + 1}')
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::")
    keyboard.row(btn_year_curr, btn_year_next)
    # keyboard.row(btn_back)
    return keyboard


def keyboard_months(command: str, year:str) -> types.InlineKeyboardMarkup():
    keyboard = types.InlineKeyboardMarkup()
    btn_jan = Button(button_data=("JAN", 1),  front_marker=f"{command}>>DAY::{year}-").button
    btn_feb = Button(button_data=("FEB", 2),  front_marker=f"{command}>>DAY::{year}-").button
    btn_mar = Button(button_data=("MAR", 3),  front_marker=f"{command}>>DAY::{year}-").button
    btn_apr = Button(button_data=("APR", 4),  front_marker=f"{command}>>DAY::{year}-").button
    btn_may = Button(button_data=("MAY", 5),  front_marker=f"{command}>>DAY::{year}-").button
    btn_jun = Button(button_data=("JUN", 6),  front_marker=f"{command}>>DAY::{year}-").button
    btn_jul = Button(button_data=("JUL", 7),  front_marker=f"{command}>>DAY::{year}-").button
    btn_aug = Button(button_data=("AUG", 8),  front_marker=f"{command}>>DAY::{year}-").button
    btn_sep = Button(button_data=("SEP", 9),  front_marker=f"{command}>>DAY::{year}-").button
    btn_oct = Button(button_data=("OCT", 10), front_marker=f"{command}>>DAY::{year}-").button
    btn_nov = Button(button_data=("NOV", 11), front_marker=f"{command}>>DAY::{year}-").button
    btn_dec = Button(button_data=("DEC", 12), front_marker=f"{command}>>DAY::{year}-").button
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::")
    keyboard.row(btn_jan, btn_feb, btn_mar, btn_apr)
    keyboard.row(btn_may, btn_jun, btn_jul, btn_aug)
    keyboard.row(btn_sep, btn_oct, btn_nov, btn_dec)
    # keyboard.row(btn_back)
    return keyboard


def keyboard_days(command, year, month):
    num_days = calendar.monthrange(int(year), int(month))[1]
    days = list(range(1, num_days + 1))
    for i in range(32 - len(days)):
        days.append('.')
    days_btns = Keyboa(items=days, items_in_row=8, front_marker=f"{command}>>DATE::{year}-{month}-")
    # btn_back = types.InlineKeyboardButton('Назад', callback_data=f"{'>>'.join(command.split('>>')[:-1])}::{year}")
    keyboard = days_btns.keyboard
    # keyboard.row(btn_back)
    return keyboard



