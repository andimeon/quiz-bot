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

from redis_connection import get_database_access

logger = logging.getLogger(__name__)

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)

global quiz_block

redis_base = get_database_access()


def send_message(event, text):
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


def get_quiz_block():
    global redis_key
    redis_key = redis_base.randomkey()
    redis_value = redis_base.get(redis_key)

    return json.loads(redis_value)


def write_to_database(user_id):
    global score
    user = f'user_vk_{user_id}'

    user_info = json.dumps({
        'last_asked_question': redis_key,
        'score': score})

    redis_base.set(user, user_info)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
                        
    load_dotenv()
    vk_session = vk_api.VkApi(token=os.getenv('VK_TOKEN'))

    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user = f'user_vk_{event.user_id}'

            if event.text == 'Start':
                if redis_base.get(user):
                    user_info_str = redis_base.get(user)
                    user_info = json.loads(user_info_str)
                    score = user_info['score']
                else:
                    score = 0

                text = 'Привет! Для начала игры нажми "Новый вопрос"'
                send_message(event, text)
                continue

            if event.text == 'Новый вопрос':
                quiz_block = get_quiz_block()
                send_message(event, quiz_block['question'])

            elif event.text == 'Сдаться':
                write_to_database(event.user_id)
                text = dedent(f'''
                    Бывает!
                    Правильный ответ - {quiz_block['answer']}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif event.text == 'Мой счет':
                text = f'Ваш счет {score}'
                send_message(event, text)

            elif event.text == quiz_block['answer']:
                score += 1
                write_to_database(event.user_id)
                text = dedent(f'''
                    Правильно!
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif re.search(event.text, quiz_block['offset']):
                score += 1
                write_to_database(event.user_id)
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