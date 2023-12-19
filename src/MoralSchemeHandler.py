import configparser
import math
import re

import openai

from src.Logger import log_info, log_error

global_config = configparser.ConfigParser()
global_config.read("config.ini")
openai.api_key = global_config["OpenAI"]["api_key"]
openai.base_url = "https://api.vsegpt.ru:6070/v1/"

class MoralSchemeHandler:
    def __init__(self):
        first_space = {
            0: 'нежелание поддерживать разговор',
            1: 'активная попытка разговорить собеседника',
            2: 'расположенность к разговору',
            3: 'проявление взаимного уважения',
            4: 'поиск общих интересов или целей'
        }

        second_space = {
            0: 'согласие во взглядах',
            1: 'проявление интереса к сотрудничеству',
            2: 'выразить мнение',
            3: 'поделиться опытом',
            4: 'обсудить'
        }

        third_space = {
            0: 'выражение доверия',
            1: 'выражение уверенности',
            2: 'уточнить детали',
            3: 'запланировать'
        }

        self.spaces = [first_space, second_space, third_space]

        self.from1to2 = ''' Кажется вы нашли с человеком общий язык.
           Твоя цель сейчас это перейти к обсуждению возможного сотрудничества.
           Придумай как плавно и аккуратно сменить тему разговора для этого. Нужно перейти на второй этап диалога \n '''

        self.from2to3 = ''' Кажется вы достигли с человеком договоренностей касаемо возможных задач в сотрудничестве.
            Необходимо утвердить сотрудничество, закрепить договоренности. Придумай как плавно и аккуратно сменить тему разговора для этого. Нужно перейти к третьему этапу диалогу\n   '''

        self.current_stage_1 = 'Сейчас вы находитесь на первом этапе диалога\n'
        self.current_stage_2 = 'Сейчас вы находитесь на втором этапе диалога\n'
        self.current_stage_3 = 'Сейчас вы находитесь на третьем этапе диалога\n'

        self.r = 0.1

        self.p = 0.1

        self.appr = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0]]
        self.feelings = [[0, 0.5, 0.5, 0.6, 0.6], [0.6, 0.6, 0.4, 0.6, 0.2], [0.3, 0.3, 0.3, 0.4]]

        self.schemes = [False, False, False]

        self.prev_scheme = 1
        self.current_scheme = 1

    def reply_calc_clear(self, reply):
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", reply)
        # Преобразуем найденные значения в числа float или int, в зависимости от того, есть ли десятичная точка
        numbers = [float(num) if '.' in num else int(num) for num in numbers]
        # Получившийся список чисел
        return (numbers)

    def intensional_calc(self, intens_dict, gpt_model, fraze):
        cat_str = ', '.join(intens_dict.values())
        num = len(intens_dict.values())
        string = f'''
            Ты механизм по определению интенций в речи человека, связанных с его поведением в различных социальных ситуациях.
    Твоей основной задачей является определить вероятность содержания каждой интенции из сказанного предложения от 0 до 1.
    В твоем распоряжении только {num} интенсиональностей для угадывания (они перечислены через запятую):
     {cat_str}
     Вероятность - число от 0 до 1, где 0 - интенция не содержится совсем, а 1 - содержится точно
              Используй интенции только из указанного списка! Выведи {num} значений вероятности каждой интенциональности в фразе:  "{fraze}"
               Выведи только значения через запятую
      '''
        messages = [{"role": "assistant", "content": string}]
        try:
            completion = openai.chat.completions.create(model=gpt_model, messages=messages)
        except Exception as e:
            log_error(f"Exception while getting reply from ChatGPT: {e}")
            return
        reply = completion.choices[0].message.content
        return self.reply_calc_clear(reply)

    def euc_dist(self, a, b):
        if len(a) != len(b):
            raise ValueError("Векторы должны иметь одинаковую длину")

        distance = math.sqrt(sum((a_i - b_i) ** 2 for a_i, b_i in zip(a, b)))
        return distance

    def answer_generate(self, last_message, messages, model, intens_dict, feelings, prev_scheme, current_scheme):
        cat_str = ', '.join(intens_dict.values())
        num = len(intens_dict.values())
        cat_list = list(intens_dict.values())
        prob_int_list = ', '.join(f'{label}: {value}' for label, value in zip(cat_list, feelings))

        changed_message = f'''Последняя реплика человека:{last_message}.
         Сгенерируй фразу - ответ на последнюю реплику человека
         Фраза должна быть не более 20 слов в длину
         Фраза должна содержать не более одного утвердительного предложения или не более одного вопросительного предложения
         Фраза должна быть адекватным и логичным ответом к последней реплике человека.
         Фраза должна быть уместной в контексте всей истории диалога.
         Фраза не должна содержать никакой информации об этапах диалога
          Выведи только новую реплику
       '''

        if current_scheme - prev_scheme == 1 and current_scheme == 2:
            changed_message = self.from1to2 + changed_message
        elif current_scheme - prev_scheme == 1 and current_scheme == 3:
            changed_message = self.from2to3 + changed_message

        messages_opt = list(messages)
        messages_opt.append({"role": "user", "content": changed_message})

        try:
            completion = openai.chat.completions.create(model=model, messages=messages_opt)
        except Exception as e:
            log_error(f"Exception while getting reply from ChatGPT: {e}")
            return
        reply = completion.choices[0].message.content
        return reply

    def get_reply(self, message, messages):
        log_info(f'Сх: {self.schemes}')
        action = self.intensional_calc(self.spaces[self.current_scheme - 1], "gpt-3.5-turbo", message)
        if action is None:
            return
        for i in range(len(self.appr[self.current_scheme - 1])):
            self.appr[self.current_scheme - 1][i] = (1 - self.r) * self.appr[self.current_scheme - 1][i] + self.r * action[i]
        dist = self.euc_dist(self.appr[self.current_scheme - 1], self.feelings[self.current_scheme - 1])
        prev_scheme = self.current_scheme
        if dist > 0.25:
            for i in range(len(self.appr[self.current_scheme - 1])):
                self.feelings[self.current_scheme - 1][i] = (1 - self.p) * self.feelings[self.current_scheme - 1][i] + self.p * (
                            self.appr[self.current_scheme - 1][i] - self.feelings[self.current_scheme - 1][i])
        else:
            self.schemes[self.current_scheme - 1] = True
            self.current_scheme = min(self.current_scheme + 1, 3)
        reply = self.answer_generate(message, messages, "gpt-3.5-turbo", self.spaces[self.current_scheme - 1],
                                self.feelings[self.current_scheme - 1], prev_scheme, self.current_scheme)
        if reply is None:
            return
        log_info(f"параметры_об:{self.appr[self.current_scheme - 1]}")
        log_info(f"параметры_суб:{self.feelings[self.current_scheme - 1]}")
        log_info(f"Расстояние:{dist}")
        for i in range(len(self.appr[self.current_scheme - 1])):
            self.appr[self.current_scheme - 1][i] = (1 - self.r) * self.appr[self.current_scheme - 1][i] + self.r * 0.3 * \
                                          self.feelings[self.current_scheme - 1][i]
        return [reply, self.current_scheme]

    def just_use_unmoral_scheme(self, message, messages):
        messages.append({"role": "user", "content": message})
        completion = openai.chat.completions.create(model='gpt-3.5-turbo', messages=messages)
        return [completion.choices[0].message.content, self.current_scheme]