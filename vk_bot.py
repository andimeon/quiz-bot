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
from redis_handler import RedisHandler

logger = logging.getLogger(__name__)

keyboard = VkKeyboard(one_time=True)
keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.DEFAULT)

redis_base = RedisHandler()


def send_message(event, text):
    vk_api.messages.send(
        user_id=event.user_id,
        message=text,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000)
    )


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
                redis_base.initiate_score(user)
                text = 'Привет! Для начала игры нажми "Новый вопрос"'
                send_message(event, text)
                continue

            if event.text == 'Новый вопрос':
                redis_base.initiate_new_quiz_block()
                print(redis_base.answer)
                send_message(event, redis_base.question)

            elif event.text == 'Сдаться':
                redis_base.set_score()
                text = dedent(f'''
                    Бывает!
                    Правильный ответ - {redis_base.answer}
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif event.text == 'Мой счет':
                text = f'Ваш счет {redis_base.score}'
                send_message(event, text)

            elif event.text == redis_base.answer:
                redis_base.score += 1
                redis_base.set_score()
                text = dedent(f'''
                    Правильно!
                    Для следующего вопроса жми
                    "Новый вопрос"
                ''')
                send_message(event, text)

            elif re.search(event.text, redis_base.offset):
                redis_base.score += 1
                redis_base.set_score()
                text = dedent(f'''
                    Почти попал
                    Правильный ответ - {redis_base.answer}
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