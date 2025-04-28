import time
from datetime import datetime

class Analytics:
    """
    Класс для сбора и анализа данных об использовании приложения.

    Отслеживает различные метрики использования чата:
    - Статистику по моделям
    - Время ответа
    - Использование токенов
    - Длину сообщений
    - Общую длительность сессии
    """

    def __init__(self, cache):
        """
        Инициализация системы аналитики.

        Args:
            cache (ChatCache): Экземпляр класса для работы с базой данных

        Создает необходимые структуры данных для хранения:
        - Времени начала сессии
        - Статистики использования моделей
        - Детальных данных о каждом сообщении
        """
        self.cache = cache
        self.start_time = time.time()
        self.model_usage = {}
        self.session_data = []


        self._load_historical_data()

    def _load_historical_data(self):
        """
        Загрузка исторических данных из базы данных.
        Обновляет статистику использования моделей и сессионные данные.
        """
        history = self.cache.get_analytics_history()

        for record in history:
            timestamp, model, message_length, response_time, tokens_used = record

            if model not in self.model_usage:
                self.model_usage[model] = {
                    'count': 0,
                    'tokens': 0
                }
            self.model_usage[model]['count'] += 1
            self.model_usage[model]['tokens'] += tokens_used

            self.session_data.append({
                'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f'),
                'model': model,
                'message_length': message_length,
                'response_time': response_time,
                'tokens_used': tokens_used
            })

    def track_message(self, model: str, message_length: int, response_time: float, tokens_used: int):
        """
        Отслеживание метрик отдельного сообщения.

        Сохраняет подробную информацию о каждом сообщении и обновляет
        общую статистику использования моделей.

        Args:
            model (str): Идентификатор использованной модели
            message_length (int): Длина сообщения в символах
            response_time (float): Время ответа в секундах
            tokens_used (int): Количество использованных токенов
        """
        timestamp = datetime.now()

        self.cache.save_analytics(timestamp, model, message_length, response_time, tokens_used)

        if model not in self.model_usage:
            self.model_usage[model] = {
                'count': 0,
                'tokens': 0
            }
        self.model_usage[model]['count'] += 1
        self.model_usage[model]['tokens'] += tokens_used

        self.session_data.append({
            'timestamp': timestamp,
            'model': model,
            'message_length': message_length,
            'response_time': response_time,
            'tokens_used': tokens_used
        })

    def get_statistics(self) -> dict:
        """
        Получение общей статистики использования.

        Вычисляет и возвращает агрегированные метрики на основе
        собранных данных о сообщениях и использовании моделей.

        Returns:
            dict: Словарь с различными метриками:
                - total_messages: общее количество сообщений
                - total_tokens: общее количество использованных токенов
                - session_duration: длительность сессии в секундах
                - messages_per_minute: среднее количество сообщений в минуту
                - tokens_per_message: среднее количество токенов на сообщение
                - model_usage: статистика использования каждой модели
        """
        total_time = time.time() - self.start_time
        total_tokens = sum(model['tokens'] for model in self.model_usage.values())
        total_messages = sum(model['count'] for model in self.model_usage.values())
        return {
            'total_messages': total_messages,
            'total_tokens': total_tokens,
            'session_duration': total_time,

            # Расчет среднего количества сообщений в минуту
            # Если сессия только началась (total_time близко к 0),
            # возвращаем 0 чтобы избежать деления на очень маленькое число
            'messages_per_minute': (total_messages * 60) / total_time if total_time > 0 else 0,

            # Расчет среднего количества токенов на сообщение
            # Если сообщений нет, возвращаем 0 чтобы избежать деления на ноль
            'tokens_per_message': total_tokens / total_messages if total_messages > 0 else 0,

            # Полная статистика использования моделей
            'model_usage': self.model_usage
        }

    def export_data(self) -> list:
        """
        Экспорт всех собранных данных сессии.

        Returns:
            list: Список словарей с подробной информацией о каждом сообщении
                 включая временные метки, использованные модели и метрики.
        """
        return self.session_data

    def clear_data(self):
        """
        Очистка всех накопленных данных аналитики.

        Сбрасывает все счетчики и метрики, начиная новую сессию:
        - Очищает статистику использования моделей
        - Очищает историю сообщений
        - Сбрасывает время начала сессии
        """
        self.model_usage.clear()
        self.session_data.clear()