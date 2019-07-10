import datetime
import logging

from aiogram import types, Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import inline_calendar

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

YOUR_TOKEN = ''

bot = Bot(token=YOUR_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['calendar'])
async def calendar_test(msg: types.Message):
    inline_calendar.init(msg.from_user.id,
                         datetime.date.today(),
                         datetime.date.today() - datetime.timedelta(weeks=16),
                         datetime.date.today() + datetime.timedelta(weeks=16))
    await bot.send_message(msg.from_user.id, text='test', reply_markup=inline_calendar.get_keyboard(msg.from_user.id))


@dp.callback_query_handler(fun=inline_calendar.is_inline_calendar_callbackquery)
async def calendar_callback_handler(q: types.CallbackQuery):
    await bot.answer_callback_query(q.id)

    return_data = inline_calendar.handler_callback(q.from_user.id, q.data)
    if return_data is None:
        await bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                            reply_markup=inline_calendar.get_keyboard(q.from_user.id))
    else:
        picked_data = return_data
        await bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                    reply_markup=inline_calendar.get_keyboard(q.from_user.id))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
