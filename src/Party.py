import configparser
from enum import Enum

import telebot
from openai import OpenAI

from src.DataBase import DataBase
from src.Logger import log_info, log_init, log_error, log_debug
from src.MoralSchemeHandler import MoralSchemeHandler

commandList = [
    "/start_conversation_moral",
    "/start_conversation_unmoral",
    "/end_conversation",
    "/clear_history",
    "/help"
]

class UserState(Enum):
    COMMAND = 1
    MORAL = 2
    NOT_MORAL = 3

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

        self.user_data = {-1: {"state": UserState.COMMAND}}

        self.database = DataBase()

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            if not message.chat.id in self.user_data.keys():
                self.user_data[message.chat.id] = {"state": UserState.COMMAND}
            if self.user_data[message.chat.id]["state"] == UserState.COMMAND:
                if message.text == "/start_conversation_moral":
                    self.user_data[message.chat.id]["state"] = UserState.MORAL
                elif message.text == "/start_conversation_unmoral":
                    self.user_data[message.chat.id]["state"] = UserState.NOT_MORAL
                elif message.text == "/clear_history":
                    if self.database.delete_chat_history(message.chat.id):
                        self.bot.send_message(message.chat.id, "История очищена")
                    else:
                        self.bot.send_message(message.chat.id, "Ошибка")
                elif message.text == "/help":
                    self.bot.send_message(message.chat.id, "Доступные команды:\n" + "\n".join(commandList))
                else:
                    self.bot.send_message(message.chat.id, "Напишите /help.")
            else:
                self.bot_conversation(message, self.user_data[message.chat.id]["state"])

    def bot_conversation(self, message, state):
        log_debug("handling message: " + message.text)
        if message.text == "/end_conversation":
            self.user_data[message.chat.id]["state"] = UserState.COMMAND
            return
        messages = self.messages.copy()
        chat_history = self.database.get_chat_history(message.chat.id)
        if chat_history is None:
            self.bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
            return
        messages[message.chat.id] = [messages[-1][0]]
        for his_mes in chat_history:
            messages[message.chat.id].append({"role": "user", "content": his_mes[1]})
            messages[message.chat.id].append({"role": "assistant", "content": his_mes[0]})
        handler = MoralSchemeHandler()
        if self.user_data[message.chat.id]["state"] == UserState.MORAL:
            reply = handler.get_reply(message.text, messages[message.chat.id])
        elif self.user_data[message.chat.id]["state"] == UserState.NOT_MORAL:
            reply = handler.just_use_unmoral_scheme(message.text, messages[message.chat.id])
        else:
            reply = None
        if reply is None:
            self.bot.send_message(message.chat.id, "Ошибка с получением ответ от сервера OpenAI.")
            return

        log_info(f"ChatGPT: {reply}")
        self.bot.send_message(message.chat.id, reply)

        if not self.database.insert_message_in_chat_history(message.chat.id, reply[0], reply[1], message.text):
            self.bot.send_message(message.chat.id, "Не удалось запомнить ответ. Ошибка подключения к базе данных.")

    def run(self):
        self.bot.infinity_polling()