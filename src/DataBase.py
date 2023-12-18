import configparser

import psycopg2
from src.Logger import log_error, log_info

class DataBase:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        self.dbname = config["DATABASE"]["name"]
        self.user = config["DATABASE"]["user"]
        self.password = config["DATABASE"]["password"]
        self.host = config["DATABASE"]["host"]
        self.port = config["DATABASE"]["port"]

    def _create_connection(self):
        try:
            self.conn = psycopg2.connect(dbname=self.dbname, user=self.user,
                                         password=self.password, host=self.host,
                                         port=self.port)
            self.cursor = self.conn.cursor()
            log_info("Initialized connection to database")
        except psycopg2.OperationalError as e:
            log_error("Could not connect to database. Error:\n" + str(e))

    def _close_connection(self):
        try:
            self.cursor.close()
        except psycopg2.OperationalError as e:
            log_error("Can't close cursor. Error:\n" + str(e))
        try:
            self.conn.close()
        except psycopg2.OperationalError as e:
            log_error("Can't close connection. Error:\n" + str(e))

    def get_chat_history(self, user_id):
        try:
            self._create_connection()
            self.cursor.execute(
                f'''
                    SELECT msg_bot, msg_user FROM
                    chathistory WHERE user_hash_tg_id='{user_id}';
                '''
            )
            res = self.cursor.fetchall()
            self._close_connection()
            return res
        except psycopg2.OperationalError as e:
            log_error("Operational error occurred while getting chat history. Error:\n" + str(e))
            self._close_connection()

    def insert_message_in_chat_history(self, user_id, bot_message, user_message):
        try:
            self._create_connection()
            self.cursor.execute(
                f'''
                    INSERT INTO chathistory (user_hash_tg_id, msg_bot, msg_user)
                    VALUES ('{user_id}', '{bot_message}', '{user_message}');
                '''
            )
            self.conn.commit()
            self._close_connection()
            return True
        except psycopg2.OperationalError as e:
            log_error("Operational error occurred while inserting. Error:\n" + str(e))
            self._close_connection()
            return False
