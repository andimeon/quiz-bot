import os
import logging
from dotenv import load_dotenv
import random
import re
from textwrap import dedent
import json

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from quiz_dict import get_quiz_for_bot
from redis_connection import get_database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)

global quiz_block

redis_base = get_database()


def send_message(event, text):
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


def get_quiz_block(user_id):
    redis_key = redis_base.randomkey()
    redis_value = redis_base.get(redis_key)
    quiz_block = json.loads(redis_value)

    user = f'user_vk_{user_id}'
    print(user)

    last_asked_question = json.dumps({
        'last_asked_question': redis_key})

    redis_base.set(user, last_asked_question)

    return quiz_block


if __name__ == "__main__":
    load_dotenv()
    vk_session = vk_api.VkApi(token=os.getenv('VK_TOKEN'))

    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:

            if event.text == 'Start':
                text = 'Привет! Для начала игры нажми "Новый вопрос"'
                send_message(event, text)

            if event.text == 'Новый вопрос':
                quiz_block = get_quiz_block(event.user_id)
                print(quiz_block['answer'])
                send_message(event, quiz_block['question'])

            elif event.text == 'Сдаться':
                text = dedent(f'''
                    Бывает!
                    Правильный ответ - {quiz_block['answer']}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif event.text == 'Мой счет':
                text = 'Пока счета нет'
                send_message(event, text)

            elif event.text == quiz_block['answer']:
                text = dedent(f'''
                    Правильно!
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif re.search(event.text, quiz_block['offset']):
                text = dedent(f'''
                    Почти попал
                    Правильный ответ - {quiz_block['answer']}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)
            
            else:
                text = dedent(f'''
                    Упс, неправильно!
                    Попробуй еще раз
                ''')
                send_message(event, text)