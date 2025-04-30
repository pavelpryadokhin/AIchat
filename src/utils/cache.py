import sqlite3
import json
from datetime import datetime
import threading
import random
import hashlib


class ChatCache:
    """
    Класс для кэширования истории чата в SQLite базе данных.

    Обеспечивает:
    - Потокобезопасное хранение истории сообщений
    - Сохранение метаданных (модель, токены, время)
    - Форматированный вывод истории
    - Очистку истории
    - Хранение и управление API ключами и PIN-кодами для аутентификации
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

        Создает таблицы:
        - messages: для хранения сообщений
        - analytics_messages: для хранения аналитики
        - api_keys: для хранения API ключей и PIN-кодов
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
            
        # Таблица для хранения API ключей и PIN-кодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_hash TEXT UNIQUE,
                pin_code TEXT,
                created_at DATETIME
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
        
    # --- Функции для аутентификации ---
    
    def _hash_api_key(self, api_key):
        """
        Хеширует API ключ для безопасного хранения.
        
        Args:
            api_key (str): API ключ для хеширования
            
        Returns:
            str: Хешированный API ключ
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def register_api_key(self, api_key):
        """
        Регистрирует новый API ключ и генерирует для него PIN-код.
        
        Args:
            api_key (str): API ключ для регистрации
            
        Returns:
            str: Сгенерированный 4-значный PIN-код
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Генерация 4-значного PIN-кода
        pin_code = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        
        # Хеширование API ключа для безопасности
        api_key_hash = self._hash_api_key(api_key)
        
        try:
            cursor.execute('''
                INSERT INTO api_keys (api_key_hash, pin_code, created_at)
                VALUES (?, ?, ?)
            ''', (api_key_hash, pin_code, datetime.now()))
            conn.commit()
            return pin_code
        except sqlite3.IntegrityError:
            # Если ключ уже существует, возвращаем существующий PIN
            cursor.execute('SELECT pin_code FROM api_keys WHERE api_key_hash = ?', (api_key_hash,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def verify_pin(self, pin_code):
        """
        Проверяет существование PIN-кода в базе.
        
        Args:
            pin_code (str): PIN-код для проверки
            
        Returns:
            bool: True если PIN-код существует, False иначе
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM api_keys WHERE pin_code = ?', (pin_code,))
        count = cursor.fetchone()[0]
        return count > 0
    
    def delete_api_key_by_pin(self, pin_code):
        """
        Удаляет API ключ по PIN-коду.
        
        Args:
            pin_code (str): PIN-код для удаления
            
        Returns:
            bool: True если ключ был удален, False иначе
        """
        if not self.verify_pin(pin_code):
            return False
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM api_keys WHERE pin_code = ?', (pin_code,))
        conn.commit()
        return cursor.rowcount > 0
    
    def is_api_key_registered(self, api_key):
        """
        Проверяет, зарегистрирован ли API ключ.
        
        Args:
            api_key (str): API ключ для проверки
            
        Returns:
            bool: True если ключ зарегистрирован, False иначе
        """
        api_key_hash = self._hash_api_key(api_key)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM api_keys WHERE api_key_hash = ?', (api_key_hash,))
        count = cursor.fetchone()[0]
        return count > 0
