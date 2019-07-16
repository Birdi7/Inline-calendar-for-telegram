import datetime
import logging
from calendar import monthrange
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Optional

from aiogram import types
from aiogram.types import User
from aiogram.utils.callback_data import CallbackData, CallbackDataFilter
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


@dataclass
class InlineCalendarData:
    chat_id: int
    min_date: datetime.datetime
    max_date: datetime.datetime
    current_date: datetime.datetime
    month_names: List[str]
    days_names: List[str]


class InlineCalendar:
    # constants
    _CALLBACK_DATA_PREFIX = 'inline_calendar'
    BASE_CALLBACK = CallbackData(_CALLBACK_DATA_PREFIX, 'action', 'data')
    CALLBACK_WRONG_CHOICE = BASE_CALLBACK.new(action=Actions.WRONG_CHOICE.name, data='-')
    CALLBACK_PREVIOUS_MONTH = BASE_CALLBACK.new(action=Actions.PREVIOUS_MONTH.name, data='-')
    CALLBACK_NEXT_MONTH = BASE_CALLBACK.new(action=Actions.NEXT_MONTH.name, data='-')
    __MAX_DAYS_IN_MONTH = 32

    def __init__(self, db_name: Optional[Path] = None):
        """
        :param db_name: if back
        :param restore: restore from backup if available
        """
        if db_name is None:
            db_name = Path().cwd() / "inline_calendar_db.json"
        self.db_name = db_name

        self.data: Dict[int, str] = {}

    def _get_user_info(self, chat_id: int) -> Optional[InlineCalendarData]:
        return self.data.get(chat_id, None)

    def _set_user_info(self, chat_id: int, user_data: InlineCalendarData):
        self.data[chat_id] = user_data

    def _db_delete(self, chat_id: int):
        del self.data[chat_id]

    def _create_header(self, chat_id: int) -> List[types.InlineKeyboardButton]:
        user_info = self._get_user_info(chat_id=chat_id)

        buttons = [types.InlineKeyboardButton("{month} {year}".format(
            month=user_info.month_names[user_info.current_date.month],
            year=user_info.current_date.year), callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE)
                   ]
        return buttons

    def _create_bottom(self, chat_id: int) -> List[types.InlineKeyboardButton]:
        result = []
        user_info = self._get_user_info(chat_id=chat_id)

        if user_info.current_date > user_info.min_date:
            result.append(types.InlineKeyboardButton('<', callback_data=InlineCalendar.CALLBACK_PREVIOUS_MONTH))
        else:
            result.append(types.InlineKeyboardButton(' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))
        result.append(types.InlineKeyboardButton(' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))
        if user_info.current_date < user_info.max_date:
            result.append(types.InlineKeyboardButton('>', callback_data=InlineCalendar.CALLBACK_NEXT_MONTH))
        else:
            result.append(types.InlineKeyboardButton(' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))

        return result

    def _create_weekdays_buttons(self, chat_id: int) -> List[types.InlineKeyboardButton]:
        return [
            types.InlineKeyboardButton(
                self._get_user_info(chat_id).days_names[i],
                callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE
            ) for i in range(0, 7)
        ]

    def _inc_month(self, chat_id: int):
        user_data = self._get_user_info(chat_id)
        user_data.current_date += relativedelta(months=1)
        self._set_user_info(chat_id, user_data)

    def _dec_month(self, chat_id: int):
        user_data = self._get_user_info(chat_id)
        user_data.current_date -= relativedelta(months=1)
        self._set_user_info(chat_id, user_data)

    def init(self,
             base_date: datetime.date,
             min_date: datetime.date,
             max_date: datetime.date,
             chat_id: Optional[int] = None,
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
        if chat_id is None:
            chat_id = User.get_current().id

        if not (min_date <= base_date <= max_date):
            raise ValueError("Base_date is less than min_date or more than max_date")

        if month_names is None:
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
        if len(month_names) != 12:
            raise ValueError('Length of month_names != 12')

        if days_names is None:
            days_names = ['Mon', 'Tu', 'Wed', 'Th', 'Fr', 'Sat', 'Sun']
        if len(days_names) != 7:
            raise ValueError('Length of days_names != 7')

        self._set_user_info(
            chat_id,
            InlineCalendarData(chat_id, min_date, max_date, base_date, month_names, days_names)
        )

    def reset(self, chat_id: Optional[int] = None):
        if chat_id is None:
            chat_id = User.get_current().id
        self._db_delete(chat_id)

    def is_inited(self, chat_id: Optional[int] = None):
        if chat_id is None:
            chat_id = User.get_current().id
        return self._get_user_info(chat_id) is not None

    def get_keyboard(self, chat_id: Optional[int] = None):
        if chat_id is None:
            chat_id = User.get_current().id

        if not self.is_inited(chat_id):
            raise NotInitedException('inline_calendar is not inited properly')

        user_info = self._get_user_info(chat_id)

        kb = types.InlineKeyboardMarkup()
        kb.row(*self._create_header(chat_id))  # create header with month name and year aka "Aug 2019"
        kb.row(*self._create_weekdays_buttons(chat_id))  # create buttons with week days

        f_row = []
        mrange = monthrange(user_info.current_date.year, user_info.current_date.month)
        for i in range(mrange[0]):  # adding the days which were passed
            f_row.append(types.InlineKeyboardButton(text=' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))

        rows = [f_row]
        for i in range(1, mrange[1] + 1):  # adding active days
            curr_date = datetime.date(day=i, month=user_info.current_date.month, year=user_info.current_date.year)
            if curr_date.weekday() == 0:
                rows.append([])
            if curr_date < user_info.min_date:
                rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))
            else:
                rows[-1].append(types.InlineKeyboardButton(text=str(i), callback_data=InlineCalendar.BASE_CALLBACK.new(
                    action=Actions.PICK_DAY.name, data=str(i)
                )))

        curr_date = datetime.date(day=mrange[1], month=user_info.current_date.month, year=user_info.current_date.year)

        for i in range(curr_date.weekday() + 1, 7):  # adding inactive days
            rows[-1].append(types.InlineKeyboardButton(text=' ', callback_data=InlineCalendar.CALLBACK_WRONG_CHOICE))

        for r in rows:
            kb.row(*r)

        kb.row(*self._create_bottom(chat_id))  # adding buttons for pagination
        return kb

    def filter(self, **config) -> CallbackDataFilter:
        return InlineCalendar.BASE_CALLBACK.filter(**config)

    def handle_callback(self, chat_id: int, callback_data: Dict[str, str]):
        """
        A method for handling callbacks
        :param chat_id: chat id of user
        :param callback_data:
        :return: datetime.date object if some date was picked else None
        """

        if not self.is_inited(chat_id):
            raise NotInitedException('inline_calendar is not inited properly')

        user_info = self._get_user_info(chat_id)
        if callback_data['action'] == Actions.PREVIOUS_MONTH.name and user_info.current_date > user_info.min_date:
            self._dec_month(chat_id)

        if callback_data['action'] == Actions.NEXT_MONTH.name and user_info.current_date < user_info.max_date:
            self._inc_month(chat_id)

        if callback_data['action'] == Actions.PICK_DAY.name:
            return user_info.current_date.replace(day=int(callback_data['data']))

    def close(self):
        raise NotImplementedError

    def _read_info(self):
        raise NotImplemented

    def _write_info(self, destination):
        raise NotImplemented
