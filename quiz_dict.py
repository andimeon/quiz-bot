import re
import glob
import json
import os


def get_quiz_for_bot(files):
    quiz_files = glob.glob(files)
    
    quiz_for_bot = []
    
    for quiz_file in quiz_files:
        with open(quiz_file, 'r', encoding='koi8-r') as file:
            quizzes = file.read()
        
        questions_and_answers = re.split(r'Вопрос\s\d+:', quizzes)
        questions_and_answers.pop(0)
        
        for question_and_answer in questions_and_answers:
            quiz_block = get_quiz_block(question_and_answer)
            quiz_for_bot.append(quiz_block)
    
    return quiz_for_bot


def get_quiz_block(question_and_answer):
    question, answer, offset, comment = '', '', '', ''
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
    
    return {
        'Вопрос': question,
        'Ответ': answer,
        'Зачет': offset,
        'Комментарий': comment,
    }


def get_clean_text(text, text_block):
    if text == 'Комментарий:':
        return re.split(text, text_block).pop(1).replace('\n', ' ')
    else:
        text = re.split(text, text_block).pop(1).replace('\n', ' ')
        return text.replace('.', '').replace('"', '').strip()
