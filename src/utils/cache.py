import sqlite3
import json
from datetime import datetime
import threading


class ChatCache:
    """
    Класс для кэширования истории чата в SQLite базе данных.

    Обеспечивает:
    - Потокобезопасное хранение истории сообщений
    - Сохранение метаданных (модель, токены, время)
    - Форматированный вывод истории
    - Очистку истории
    """

    def __init__(self):
        """
        Инициализация системы кэширования.

        Создает:
        - Файл базы данных SQLite
        - Потокобезопасное хранилище соединений
        - Необходимые таблицы в базе данных
        """
        self.db_name = 'chat_cache.db'

        # Создание потокобезопасного хранилища соединений
        # Каждый поток будет иметь свое собственное соединение с базой
        self.local = threading.local()
        self.create_tables()

    def get_connection(self):
        """
        Получение соединения с базой данных для текущего потока.

        Returns:
            sqlite3.Connection: Объект соединения с базой данных

        Note:
            Каждый поток получает свое собственное соединение,
            что обеспечивает потокобезопасность работы с базой.
        """
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_name)
        return self.local.connection

    def create_tables(self):
        """
        Создание необходимых таблиц в базе данных.

        Создает таблицу messages со следующими полями:
        - id: уникальный идентификатор сообщения
        - model: идентификатор использованной модели
        - user_message: текст сообщения пользователя
        - ai_response: ответ AI модели
        - timestamp: время создания сообщения
        - tokens_used: количество использованных токенов
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                model TEXT,                          
                user_message TEXT,              
                ai_response TEXT,                  
                timestamp DATETIME,                  
                tokens_used INTEGER
            )                 
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model TEXT,
                message_length INTEGER,
                response_time FLOAT,
                tokens_used INTEGER
            )
            ''')

        conn.commit()
        conn.close()

    def save_message(self, model, user_message, ai_response, tokens_used):
        """
        Сохранение нового сообщения в базу данных.

        Args:
            model (str): Идентификатор использованной модели
            user_message (str): Текст сообщения пользователя
            ai_response (str): Ответ AI модели
            tokens_used (int): Количество использованных токенов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (model, user_message, ai_response, timestamp, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (model, user_message, ai_response, datetime.now(), tokens_used))
        conn.commit()

    def get_chat_history(self, limit=50):
        """
        Получение последних сообщений из истории чата.

        Args:
            limit (int): Максимальное количество возвращаемых сообщений

        Returns:
            list: Список кортежей с данными сообщений, отсортированных
                 по времени в обратном порядке (новые сначала)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def save_analytics(self, timestamp, model, message_length, response_time, tokens_used):
        """
        Сохранение данных аналитики в базу данных.

        Args:
            timestamp (datetime): Время создания записи
            model (str): Идентификатор использованной модели
            message_length (int): Длина сообщения
            response_time (float): Время ответа
            tokens_used (int): Количество использованных токенов
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO analytics_messages
            (timestamp, model, message_length, response_time, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, model, message_length, response_time, tokens_used))
        conn.commit()

    def get_analytics_history(self):
        """
        Получение всей истории аналитики.

        Returns:
            list: Список записей аналитики
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, model, message_length, response_time, tokens_used
            FROM analytics_messages
            ORDER BY timestamp ASC
        ''')
        return cursor.fetchall()

    def __del__(self):
        """
        Деструктор класса.

        Закрывает соединения с базой данных при уничтожении объекта,
        предотвращая утечки ресурсов.
        """

        if hasattr(self.local, 'connection'):
            self.local.connection.close()

    def clear_history(self):
        """
        Очистка всей истории сообщений.

        Удаляет все записи из таблицы messages,
        эффективно очищая всю историю чата.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        conn.commit()

    def get_formatted_history(self):
        """
        Получение отформатированной истории диалога.

        Returns:
            list: Список словарей с данными сообщений в формате:
                {
                    "id": int,              # ID сообщения
                    "model": str,           # Использованная модель
                    "user_message": str,    # Сообщение пользователя
                    "ai_response": str,     # Ответ AI
                    "timestamp": datetime,  # Время создания
                    "tokens_used": int      # Использовано токенов
                }
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                id,
                model,
                user_message,
                ai_response,
                timestamp,
                tokens_used
            FROM messages
            ORDER BY timestamp ASC
        ''')

        history = []
        for row in cursor.fetchall():
            history.append({
                "id": row[0],
                "model": row[1],
                "user_message": row[2],
                "ai_response": row[3],
                "timestamp": row[4],
                "tokens_used": row[5]
            })
        return history
