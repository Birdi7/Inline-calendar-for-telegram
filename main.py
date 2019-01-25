import datetime
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import telebot
from telebot import types
import inline_calendar


tok='199586207:AAETqFv-D3EhFRmRr3pTWf_40DEzkepcFLg'
bot = telebot.TeleBot(token=tok)


@bot.message_handler(commands=['calendar'])
def calendar_test(msg: types.Message):
    inline_calendar.init(datetime.date.today(),
                         datetime.date(year=2018, month=11, day=1),
                         datetime.date(year=2019, month=4, day=1))
    bot.send_message(msg.from_user.id, text='test', reply_markup=inline_calendar.get_keyboard())


@bot.callback_query_handler(func=inline_calendar.is_inline_calendar_callbackquery)
def calendar_callback_handler(q: types.CallbackQuery):
    try:
        return_data = inline_calendar.handler_callback(q.data)
        if return_data is None:
            bot.edit_message_reply_markup(chat_id=q.from_user.id, message_id=q.message.message_id,
                                          reply_markup=inline_calendar.get_keyboard())
        else:
            picked_data = return_data
            bot.edit_message_text(text=picked_data, chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard())

    except inline_calendar.WrongChoiceCallbackException:
        if q.message.text != 'Wrong choice':
            bot.edit_message_text(text='Wrong choice', chat_id=q.from_user.id, message_id=q.message.message_id,
                                  reply_markup=inline_calendar.get_keyboard())


if __name__ == '__main__':
    bot.polling(none_stop=True)
