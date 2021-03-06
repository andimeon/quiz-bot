import re
import glob
import json
import os
import logging

from dotenv import load_dotenv
import redis

from redis_handler import RedisHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def get_quiz_for_bot(files_path, redis_base, max_number_read_files):
    quiz_files = glob.glob(files_path)
    
    quiz_for_bot = {}
    count = 0
    
    for quiz_file in quiz_file[:max_number_read_files]:
        with open(quiz_file, 'r', encoding='koi8-r') as file:
            quizzes = file.read()
        
        questions_and_answers = re.split(r'Вопрос\s\d+:', quizzes)
        questions_and_answers.pop(0)
        
        for question_and_answer in questions_and_answers:
            quiz_block = get_quiz_block(question_and_answer)
            count += 1
            question_num = f'question_{count}'
            question_block_as_str = json.dumps(quiz_block, ensure_ascii=False)
            
            redis_base.set(question_num, question_block_as_str)
    
    return quiz_for_bot


def get_quiz_block(question_and_answer):
    question, answer, offset, fail, comment = '', '', '', '', ''
    question_and_answer_blocks = question_and_answer.split('\n\n')

    question = question_and_answer_blocks.pop(0).replace('\n', ' ')

    for question_and_answer_block in question_and_answer_blocks:
        if re.search(r'Ответ:', question_and_answer_block):
            answer = get_clean_text('Ответ:', question_and_answer_block)
            continue
        if re.search(r'Зачет:', question_and_answer_block):
            offset = get_clean_text('Зачет:', question_and_answer_block)
            continue
        if re.search(r'Комментарий:', question_and_answer_block):
            comment = get_clean_text('Комментарий:', question_and_answer_block)
            continue
        if re.search(r'^Незачет:', question_and_answer_block):
            fail = get_clean_text('Незачет:', question_and_answer_block)
    
    return {
        'question': question,
        'answer': answer,
        'offset': offset,
        'fail': fail,
        'comment': comment,
    }


def clean_text(text, text_block):
    if text == 'Комментарий:':
        return re.split(text, text_block).pop(1).replace('\n', ' ')
    else:
        text = re.split(text, text_block).pop(1).replace('\n', ' ')
        return text.replace('.', '').replace('"', '').strip()


def main():
    load_dotenv()
    max_number_read_files = os.getenv('MAX_NUMBER_READ_FILES')
    files_path = os.getenv('QUIZ_FILES_PATH')
    redis_base = RedisHandler()

    get_quiz_for_bot(files_path, redis_base, max_number_read_files)
    print('Done!')


if __name__ == "__main__":
    main()