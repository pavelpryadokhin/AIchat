import requests
import os
from dotenv import load_dotenv
from utils import AppLogger

load_dotenv()


class OpenRouterClient:
    """
    Клиент для взаимодействия с OpenRouter API.
    """

    def __init__(self):
        """
        Инициализация клиента OpenRouter.

        Настраивает:
        - Систему логирования
        - API ключ и базовый URL из переменных окружения
        - Заголовки для HTTP запросов
        - Список доступных моделей

        Raises:
            ValueError: Если API ключ не найден в переменных окружения
        """
        self.logger = AppLogger()

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("BASE_URL")

        if not self.api_key:
            self.logger.error("OpenRouter API key not found in .env")
            raise ValueError("OpenRouter API key not found in .env")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        self.logger.info("OpenRouterClient initialized successfully")
        self.available_models = self.get_models()

    def get_models(self):
        """
        Получение списка доступных языковых моделей.

        Returns:
            list: Список словарей с информацией о моделях:
                 [{"id": "model-id", "name": "Model Name"}, ...]

        Note:
            При ошибке запроса возвращает список базовых моделей по умолчанию
        """
        self.logger.debug("Fetching available models")

        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            models_data = response.json()
            self.logger.info(f"Retrieved {len(models_data["data"])} models")

            return [
                {
                    "id": model["id"],
                    "name": model["name"]
                }
                for model in models_data["data"]
            ]
        except Exception as e:
            # Список моделей по умолчанию при ошибке API
            models_default = [
                {"id": "deepseek-coder", "name": "DeepSeek"},
                {"id": "claude-3-sonnet", "name": "Claude 3.5 Sonnet"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
            ]
            self.logger.info(f"Retrieved {len(models_default)} models with Error: {e}")
            return models_default

    def send_message(self, message: str, model: str):
        """
        Отправка сообщения выбранной языковой модели.

        Args:
            message (str): Текст сообщения для отправки
            model (str): Идентификатор выбранной модели

        Returns:
            dict: Ответ от API, содержащий либо ответ модели, либо информацию об ошибке
        """
        self.logger.debug(f"Sending message to model: {model}")
        data = {
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }

        try:
            self.logger.debug("Making API request")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            self.logger.info("Successfully received response from API")
            return response.json()

        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": str(e)}

    def get_balance(self):
        """
        Получение текущего баланса аккаунта.

        Returns:
            str: Строка с балансом в формате '$X.XX' или 'Ошибка' при неудаче
        """
        try:
            response = requests.get(
                f"{self.base_url}/credits",
                headers=self.headers
            )
            data = response.json()
            if data:
                data = data.get('data')
                return f"${(data.get('total_credits', 0) - data.get('total_usage', 0)):.2f}"
            return "Ошибка"
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return "Ошибка"
