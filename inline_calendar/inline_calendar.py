import datetime
import logging
import shelve
from calendar import monthrange
from enum import Enum, auto
from typing import List, Dict

from aiogram import types
from aiogram.utils.callback_data import CallbackData, CallbackDataFilter


# todo move from shelve to json

class WrongCallbackException(Exception):
    pass


class WrongChoiceCallbackException(Exception):
    pass


class NotInitedException(Exception):
    pass


class Actions(Enum):
    WRONG_CHOICE = auto()
    PREVIOUS_MONTH = auto()
    NEXT_MONTH = auto()
    PICK_DAY = auto()


# constants
_INLINE_CALENDAR_NAME = 'inline_calendar'
_MIN_DATE = '_MIN_DATE'
_MAX_DATE = '_MAX_DATE'
_CURRENT_DATE = '_CURRENT_DATE'
_MONTH_NAMES = '_MONTH_NAMES'
_DAYS_NAMES = '_DAYS_NAMES'
_CALLBACK_DATA_PREFIX = 'inline_calendar'
CALLBACK = CallbackData(_CALLBACK_DATA_PREFIX, 'action', 'data')
CALLBACK_WRONG_CHOICE = CALLBACK.new(action=Actions.WRONG_CHOICE.name, data='-')
CALLBACK_PREVIOUS_MONTH = CALLBACK.new(action=Actions.PREVIOUS_MONTH.name, data='-')
CALLBACK_NEXT_MONTH = CALLBACK.new(action=Actions.NEXT_MONTH.name, data='-')
MAX_DAYS_IN_MONTH = 32
CALLBACK_DAYS = [CALLBACK.new(action=Actions.PICK_DAY.name, data=i) for i in range(MAX_DAYS_IN_MONTH)]

# user vars
_SHELVE_DB_NAME = "INLINE_CALENDAR_DB"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _db_read(chat_id: str, attr_name: str):
    try:
        with shelve.open(_SHELVE_DB_NAME) as db:
            return db[chat_id][attr_name]
    except KeyError:
        logging.log(level=logging.CRITICAL, msg='KeyError was raised while getting attribute {} for {}'
                    .format(attr_name, chat_id))
        # idk why it happens sometimes. Didn't see any affection on work of calendar


def _db_write(chat_id: str, attr_name: str, data):
    with shelve.open(_SHELVE_DB_NAME, writeback=True) as db:
        db.setdefault(chat_id, {})[attr_name] = data
    logger.debug(f'_db_write({chat_id}, {attr_name}. {data})')


def _db_delete(chat_id: str):
    with shelve.open(_SHELVE_DB_NAME, writeback=True) as db:
        del db[chat_id]


def _create_header(chat_id: str) -> List[types.InlineKeyboardButton]:
    c_date = _db_read(chat_id, _CURRENT_DATE)
    user_months = _db_read(chat_id, _MONTH_NAMES)
    return [types.InlineKeyboardButton("{month} {year}".format(month=user_months[c_date.month],
                                                               year=c_date.year),
                                       callback_data=CALLBACK_WRONG_CHOICE)]


def _create_bottom(chat_id: str) -> List[types.InlineKeyboardButton]:
    result = []

    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)
    max_date = _db_read(chat_id, _MAX_DATE)
    if c_date > min_date:
        result.append(types.InlineKeyboardButton('<', callback_data=CALLBACK_PREVIOUS_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))
    result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))
    if c_date < max_date:
        result.append(types.InlineKeyboardButton('>', callback_data=CALLBACK_NEXT_MONTH))
    else:
        result.append(types.InlineKeyboardButton(' ', callback_data=CALLBACK_WRONG_CHOICE))

    return result


def _create_weekdays_buttons(chat_id: str) -> List[types.InlineKeyboardButton]:
    d_names = _db_read(chat_id, _DAYS_NAMES)
    return [types.InlineKeyboardButton(d_names[i], callback_data=CALLBACK_WRONG_CHOICE) for i in range(0, 7)]


def _inc_month(chat_id):
    c_date = _db_read(chat_id, _CURRENT_DATE)
    last_day = c_date.replace(day=monthrange(c_date.year, c_date.month)[1])
    _db_write(chat_id, _CURRENT_DATE, last_day + datetime.timedelta(days=1))


def _dec_month(chat_id):
    c_date = _db_read(chat_id, _CURRENT_DATE)
    first_day = c_date.replace(day=1)
    prev_month_lastday = first_day - datetime.timedelta(days=1)
    _db_write(chat_id, _CURRENT_DATE, prev_month_lastday.replace(day=1))


def init(chat_id,
         base_date: datetime.date,
         min_date: datetime.date,
         max_date: datetime.date,
         month_names: List[str] = None,
         days_names: List[str] = None):
    """
    Default language is English
    :param chat_id: chat id
    :param base_date: a datetime.date object.
    :param min_date: a datetime.date object.
    :param max_date: a datetime.date object.
    :param month_names: 12-element list for month names. If none, then English names will be used
    :param days_names: 7-element list fo2r month names. If none, then English names will be used
    """

    if not (min_date <= base_date <= max_date):
        raise ValueError("Base_date is less than min_date or more than max_date")

    chat_id = str(chat_id)

    _db_write(chat_id, _CURRENT_DATE, base_date)
    _db_write(chat_id, _MIN_DATE, min_date)
    _db_write(chat_id, _MAX_DATE, max_date)

    if month_names is None:
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

    if len(month_names) != 12:
        raise ValueError('Length of month_names != 12')

    _db_write(chat_id, _MONTH_NAMES, month_names)

    if days_names is None:
        days_names = ['Mon', 'Tu', 'Wed', 'Th', 'Fr', 'Sat', 'Sun']
    if len(days_names) != 7:
        raise Exception('Length of days_names != 7')

    _db_write(chat_id, _DAYS_NAMES, days_names)


def reset(chat_id: str):
    _db_delete(chat_id)


def is_inited(chat_id: str):
    with shelve.open(_SHELVE_DB_NAME) as db:
        return chat_id in db


def get_keyboard(chat_id):
    chat_id = str(chat_id)
    if not is_inited(chat_id):
        raise NotInitedException('inline_calendar is not inited properly')

    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)

    kb = types.InlineKeyboardMarkup()
    kb.row(*_create_header(chat_id))  # create header with month name and year aka "Aug 2019"
    kb.row(*_create_weekdays_buttons(chat_id))  # create buttons with week days

    f_row = []
    mrange = monthrange(c_date.year, c_date.month)
    for i in range(mrange[0]):  # adding the days which were passed
        f_row.append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    rows = [f_row]
    for i in range(1, mrange[1] + 1):  # adding active days
        curr_date = datetime.date(day=i, month=c_date.month, year=c_date.year)
        if curr_date.weekday() == 0:
            rows.append([])
        if curr_date < min_date:
            rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))
        else:
            rows[-1].append(types.InlineKeyboardButton(text=str(i), callback_data=CALLBACK_DAYS[i]))

    curr_date = datetime.date(day=mrange[1], month=c_date.month, year=c_date.year)

    for i in range(curr_date.weekday() + 1, 7):  # adding inactive days
        rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=CALLBACK_WRONG_CHOICE))

    for r in rows:
        kb.row(*r)

    kb.row(*_create_bottom(chat_id))  # adding buttons for pagination
    return kb


def filter(**config) -> CallbackDataFilter:
    return CALLBACK.filter(**config)


def handle_callback(chat_id, callback_data: Dict[str, str]):
    """
    A method for handling callbacks
    :param chat_id: chat id of user
    :param callback_data:
    :return: datetime.date object if some date was picked else None
    """
    chat_id = str(chat_id)

    if not is_inited(chat_id):
        raise NotInitedException('inline_calendar is not inited properly')

    c_date = _db_read(chat_id, _CURRENT_DATE)
    min_date = _db_read(chat_id, _MIN_DATE)
    max_date = _db_read(chat_id, _MAX_DATE)
    logger.debug(f"callback_data={callback_data}")
    if callback_data['action'] == Actions.PREVIOUS_MONTH.name and c_date > min_date:
        _dec_month(chat_id)

    if callback_data['action'] == Actions.NEXT_MONTH.name and c_date < max_date:
        _inc_month(chat_id)

    if callback_data['action'] == Actions.PICK_DAY.name:
        logger.debug('pick day!')
        return _db_read(chat_id, _CURRENT_DATE).replace(day=int(callback_data['data']))
