import logging
import os
from datetime import datetime


class AppLogger:
    """
    Класс для логирования работы приложения.

    Обеспечивает:
    - Сохранение логов в файлы с датой в имени
    - Вывод логов в консоль
    - Различные уровни логирования (debug, info, warning, error)
    - Форматирование сообщений с временными метками
    """

    def __init__(self):
        """
        Инициализация системы логирования.

        Настраивает:
        - Директорию для хранения логов
        - Форматирование сообщений
        - Обработчики для файла и консоли
        - Уровни логирования
        """
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.logs_dir, f"chat_app_{current_date}.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger = logging.getLogger('ChatApp')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """
        Логирование информационного сообщения.

        Используется для записи важной информации о работе приложения:
        - Успешные операции
        - Статус выполнения
        - Информация о состоянии

        Args:
            message (str): Текст информационного сообщения
        """
        self.logger.info(message)

    def error(self, message: str, exc_info=None):
        """
        Логирование ошибки.

        Используется для записи информации об ошибках:
        - Исключения
        - Сбои в работе
        - Критические ошибки

        Args:
            message (str): Текст сообщения об ошибке
            exc_info: Информация об исключении (по умолчанию None)
                     Если передано True, автоматически добавляет стек вызовов
        """
        self.logger.error(message, exc_info=exc_info)

    def debug(self, message: str):
        """
        Логирование отладочной информации.

        Используется для записи подробной информации для отладки:
        - Значения переменных
        - Промежуточные результаты
        - Детали выполнения

        Args:
            message (str): Текст отладочного сообщения
        """
        self.logger.debug(message)

    def warning(self, message: str):
        """
        Логирование предупреждения.

        Используется для записи предупреждений:
        - Потенциальные проблемы
        - Нежелательные ситуации
        - Предупреждения о состоянии

        Args:
            message (str): Текст предупреждения
        """
        self.logger.warning(message)
