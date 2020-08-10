import os
from dotenv import load_dotenv
import logging
import random
import re
import json

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

from redis_connection import get_database_access

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

NEW＿QUESTION, ANSWER = range(2)

custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
markup = ReplyKeyboardMarkup(custom_keyboard)

redis_base = get_database_access()


def start(update, context):
    global score
    user = f'user_tg_{update.effective_chat.id}'

    if redis_base.get(user):
        user_info_str = redis_base.get(user)
        user_info = json.loads(user_info_str)
        score = user_info['score']
    else:
        score = 0

    update.message.reply_text(
        'Привет! Я бот для викторин\n'
        'Для начала нажми на "Новый вопрос"\n'
        'Для завершения игры /cancel',
        reply_markup=markup)
    
    return NEW_QUESTION


def get_new_question(update, context):
    global quiz_block
    quiz_block = get_quiz_block()
    update.message.reply_text(text=quiz_block['question'], reply_markup=markup)

    return ANSWER


def get_answer(update, context):
    global score
    message = update.message.text

    if message == quiz_block['answer']:
        score += 1
        write_to_database(update.effective_chat.id)
        update.message.reply_text(
            'Правильно!\n'
            'Для продолжения нажми на "Новый вопрос"',
            reply_markup=markup)
        
        return NEW_QUESTION

    elif re.search(message, quiz_block['offset']):
        score += 1
        write_to_database(update.effective_chat.id)
        update.message.reply_text(
            'Почти в точку! Правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(quiz_block['answer']),
            reply_markup=markup)

        return NEW_QUESTION

    else:
        update.message.reply_text(
            'Неверно, попробуй еще',
            reply_markup=markup)
        
        return ANSWER


def give_up(update, context):
    write_to_database(update.effective_chat.id)
    update.message.reply_text(
            'Бывает, правильный ответ: \n'
            '{}\n\n'
            'Для продолжения нажми на "Новый вопрос"'.format(quiz_block['answer']),
            reply_markup=markup)
    
    return NEW_QUESTION


def get_score(update, context):
    update.message.reply_text(
            'У вас {} очков\n'
            'Для продолжения нажми на "Новый вопрос"\n'
            'Для завершения игры /cancel'.format(score),
            reply_markup=markup)
    
    return NEW_QUESTION


def cancel(update, context):
    write_to_database(update.effective_chat.id)
    update.message.reply_text('Пока, увидимся в следующий раз.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def get_quiz_block():
    global redis_key
    redis_key = redis_base.randomkey()
    redis_value = redis_base.get(redis_key)

    return json.loads(redis_value)


def write_to_database(user_id):
    user = f'user_tg_{user_id}'

    user_info = json.dumps({
        'last_asked_question': redis_key,
        'score': score})

    redis_base.set(user, user_info)


def main():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    
    updater = Updater(tg_token, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            NEW＿QUESTION: [MessageHandler(Filters.regex(r'^Новый вопрос$'), get_new_question),
            
                           MessageHandler(Filters.regex(r'^Мой счет$'), get_score)],

            ANSWER: [MessageHandler(Filters.regex(r'^Сдаться$'), give_up),
            
                     MessageHandler(Filters.text, get_answer),]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    
    updater.start_polling()
    
    updater.idle()


if __name__ == "__main__":
    main()
