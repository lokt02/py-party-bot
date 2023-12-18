import configparser

import openai
import telebot
from openai import OpenAI

from src.DataBase import DataBase
from src.Logger import log_info, log_init, log_error, log_debug

global_config = configparser.ConfigParser()
global_config.read("config.ini")
openai.api_key = global_config["OpenAI"]["api_key"]
commandList = ["/help"]

class Party:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        self.bot = telebot.TeleBot(config["Telegram"]["token"])

        with open("start_prompt.txt", encoding='utf-8') as f:
            self.start_prompt = f.read()

        self.client = OpenAI(
            api_key=config["OpenAI"]["api_key"]
        )

        self.messages = {
            -1: [{"role": "assistant", "content": self.start_prompt}]
        }

        self.database = DataBase()

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            log_debug("handling message: " + message.text)
            messages = self.messages.copy()
            chat_history = self.database.get_chat_history(message.chat.id)
            if chat_history is None:
                self.bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
                return
            messages[message.chat.id] = [messages[-1][0]]
            for his_mes in chat_history:
                messages[message.chat.id].append({"role": "user", "content": his_mes[1]})
                messages[message.chat.id].append({"role": "assistant", "content": his_mes[0]})
            messages[message.chat.id].append({"role": "user", "content": message.text})
            # if message.chat.id in messages.keys():
            #     messages[message.chat.id].append({"role": "user", "content": message.text})
            # else:
            #     messages[message.chat.id] = [
            #         messages[-1],
            #         {"role": "user", "content": message.text}
            #     ]
            # completion = openai.chat.completions.create(model='gpt-3.5-turbo', messages=self.messages[message.chat.id])
            # reply = completion.choices[0].message.content
            reply = "test reply"
            log_info(f"ChatGPT: {reply}")
            self.bot.send_message(message.chat.id, reply)
            messages[message.chat.id].append({"role": "assistant", "content": str(reply)})

            if not self.database.insert_message_in_chat_history(message.chat.id, reply, message.text):
                self.bot.send_message(message.chat.id, "Не удалось запомнить ответ. Ошибка подключения к базе данных.")


    def run(self):
        self.bot.infinity_polling()