import flet as ft
import os
import asyncio
import time
import json
from datetime import datetime
import sys
import dotenv
from api import OpenRouterClient
from ui import AppStyles, MessageBubble, ModelSelector, AuthScreen
from utils import ChatCache, AppLogger, Analytics, PerformanceMonitor


class ChatApp:
    """
    Основной класс приложения чата.
    Управляет всей логикой работы приложения, включая UI и взаимодействие с API.
    """

    def __init__(self):
        """
        Инициализация основных компонентов приложения:
        - API клиент для связи с языковой моделью
        - Система кэширования для сохранения истории
        - Система логирования для отслеживания работы
        - Система аналитики для сбора статистики
        - Система мониторинга для отслеживания производительности
        """
        self.logger = AppLogger()
        self.cache = ChatCache()
        self.analytics = None
        self.monitor = None
        self.api_client = None
        self.is_authenticated = False
        
        # Создание директории для экспорта истории чата
        self.exports_dir = "exports"
        os.makedirs(self.exports_dir, exist_ok=True)

    def initialize_app_components(self):
        """
        Инициализация компонентов приложения после успешной аутентификации.
        """
        self.api_client = OpenRouterClient()
        self.analytics = Analytics(self.cache)
        self.monitor = PerformanceMonitor()

        self.balance_text = ft.Text(
            "Баланс: Загрузка...",  # Начальный текст до загрузки реального баланса
            **AppStyles.BALANCE_TEXT  # Применение стилей из конфигурации
        )
        self.update_balance()

    def load_chat_history(self):
        """
        Загрузка истории чата из кэша и отображение её в интерфейсе.
        Сообщения добавляются в обратном порядке для правильной хронологии.
        """
        try:
            history = self.cache.get_chat_history()
            for msg in reversed(history):
                _, model, user_message, ai_response, timestamp, tokens = msg
                # Добавление пары сообщений (пользователь + AI) в интерфейс
                self.chat_history.controls.extend([
                    MessageBubble(  # Создание пузырька сообщения пользователя
                        message=user_message,
                        is_user=True
                    ),
                    MessageBubble(  # Создание пузырька ответа AI
                        message=ai_response,
                        is_user=False
                    )
                ])
        except Exception as e:
            self.logger.error(f"Ошибка загрузки истории чата: {e}")

    def update_balance(self):
        """
        Обновление отображения баланса API в интерфейсе.
        При успешном получении баланса показывает его зеленым цветом,
        при ошибке - красным с текстом 'н/д' (не доступен).
        """
        try:
            balance = self.api_client.get_balance()
            self.balance_text.value = f"Баланс: {balance}"
            self.balance_text.color = ft.Colors.GREEN_400  # Установка зеленого цвета для успешного получения
        except Exception as e:
            self.balance_text.value = "Баланс: н/д"
            self.balance_text.color = ft.Colors.RED_400  # Установка красного цвета для ошибки
            self.logger.error(f"Ошибка обновления баланса: {e}")
            
    def handle_api_key_submit(self, api_key, page):
        """
        Обработка отправки API ключа.
        
        Args:
            api_key (str): API ключ OpenRouter.ai
            page (ft.Page): Объект страницы для обновления UI
        
        Returns:
            bool: True если ключ валидный, False иначе
        """
        try:
            # Временно устанавливаем API ключ в .env для проверки
            os.environ["OPENROUTER_API_KEY"] = api_key
            
            # Создаем временный экземпляр OpenRouterClient для проверки баланса
            temp_client = OpenRouterClient()
            balance = temp_client.get_balance()
            
            # Если получили баланс, значит ключ валидный
            if balance and balance != "Ошибка":
                # Сохраняем ключ в .env файл
                env_path = ".env"
                dotenv_file = dotenv.find_dotenv(env_path)
                
                if dotenv_file:
                    dotenv.set_key(dotenv_file, "OPENROUTER_API_KEY", api_key)
                else:
                    with open(env_path, "w") as f:
                        f.write(f"OPENROUTER_API_KEY={api_key}\n")
                
                # Регистрируем ключ и получаем PIN-код
                pin_code = self.cache.register_api_key(api_key)
                
                # Показываем пользователю его PIN-код
                self.auth_screen.show_success(f"Ваш PIN-код: {pin_code}\nЗапомните его для входа!")
                return True
            else:
                self.auth_screen.show_error("Неверный API ключ или нулевой баланс")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка проверки API ключа: {e}")
            self.auth_screen.show_error(f"Ошибка: {str(e)}")
            return False
            
    def handle_pin_submit(self, pin_code, page):
        """
        Обработка отправки PIN-кода.
        
        Args:
            pin_code (str): PIN-код для проверки
            page (ft.Page): Объект страницы для обновления UI
        
        Returns:
            bool: True если PIN-код верный, False иначе
        """
        if self.cache.verify_pin(pin_code):
            return True
        else:
            self.auth_screen.show_error("Неверный PIN-код")
            return False
            
    def handle_auth_reset(self):
        """
        Обработка сброса аутентификации.
        """
        self.auth_screen.switch_mode(None)  # Переключаемся в режим ввода API ключа

    def main(self, page: ft.Page):
        """
        Основная функция инициализации интерфейса приложения.
        Создает все элементы UI и настраивает их взаимодействие.

        Args:
            page (ft.Page): Объект страницы Flet для размещения элементов интерфейса
        """
        for key, value in AppStyles.PAGE_SETTINGS.items():
            setattr(page, key, value)

        AppStyles.set_window_size(page)
        
        # Создаем экран аутентификации
        self.auth_screen = AuthScreen(
            on_submit_api_key=lambda api_key: self.handle_api_key_validation(api_key, page),
            on_submit_pin=lambda pin: self.handle_pin_validation(pin, page),
            on_reset=self.handle_auth_reset
        )
        
        # Сначала показываем экран аутентификации
        page.add(ft.Container(
            content=self.auth_screen,
            alignment=ft.alignment.center,
            expand=True
        ))
        
        # Функции для обработки аутентификации
        def initialize_main_app():
            """Инициализация основного приложения после успешной аутентификации"""
            self.initialize_app_components()
            page.controls.clear()
            self.setup_main_interface(page)
            page.update()
        
        def handle_api_key_validation(api_key, page):
            """Обработка валидации API ключа"""
            is_valid = self.handle_api_key_submit(api_key, page)
            if is_valid:
                # Не переходим сразу к приложению, чтобы пользователь увидел свой PIN
                self.is_authenticated = True
        
        def handle_pin_validation(pin, page):
            """Обработка валидации PIN-кода"""
            is_valid = self.handle_pin_submit(pin, page)
            if is_valid:
                initialize_main_app()
                self.is_authenticated = True
        
        # Привязываем функции к обработчикам аутентификации
        self.handle_api_key_validation = handle_api_key_validation
        self.handle_pin_validation = handle_pin_validation

    def setup_main_interface(self, page):
        """
        Настройка основного интерфейса приложения после аутентификации.
        
        Args:
            page (ft.Page): Объект страницы Flet
        """
        # Инициализация выпадающего списка для выбора модели AI
        models = self.api_client.available_models
        self.model_dropdown = ModelSelector(models)
        self.model_dropdown.value = models[0] if models else None

        async def send_message_click(e):
            """
            Асинхронная функция отправки сообщения.
            """
            if not self.message_input.value:
                return

            try:
                # Визуальная индикация процесса
                self.message_input.border_color = ft.Colors.BLUE_400
                page.update()

                # Сохранение данных сообщения
                start_time = time.time()
                user_message = self.message_input.value
                self.message_input.value = ""
                page.update()

                # Добавление сообщения пользователя
                self.chat_history.controls.append(
                    MessageBubble(message=user_message, is_user=True)
                )

                # Индикатор загрузки
                loading = ft.ProgressRing()
                self.chat_history.controls.append(loading)
                page.update()

                # Асинхронная отправка запроса
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.api_client.send_message(
                        user_message,
                        self.model_dropdown.value
                    )
                )

                # Удаление индикатора загрузки
                self.chat_history.controls.remove(loading)

                # Обработка ответа
                if "error" in response:
                    response_text = f"Ошибка: {response['error']}"
                    tokens_used = 0
                    self.logger.error(f"Ошибка API: {response['error']}")
                else:
                    response_text = response["choices"][0]["message"]["content"]
                    tokens_used = response.get("usage", {}).get("total_tokens", 0)

                # Сохранение в кэш
                self.cache.save_message(
                    model=self.model_dropdown.value,
                    user_message=user_message,
                    ai_response=response_text,
                    tokens_used=tokens_used
                )

                # Добавление ответа в чат
                self.chat_history.controls.append(
                    MessageBubble(message=response_text, is_user=False)
                )

                # Обновление аналитики
                response_time = time.time() - start_time
                self.analytics.track_message(
                    model=self.model_dropdown.value,
                    message_length=len(user_message),
                    response_time=response_time,
                    tokens_used=tokens_used
                )

                # Логирование метрик
                self.monitor.log_metrics(self.logger)
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения: {e}")
                self.message_input.border_color = ft.Colors.RED_500

                # Показ уведомления об ошибке
                snack = ft.SnackBar(
                    content=ft.Text(
                        str(e),
                        color=ft.Colors.RED_500,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.Colors.GREY_900,
                    duration=5000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()

        def show_error_snack(page, message: str):
            """Показ уведомления об ошибке"""
            snack = ft.SnackBar(  # Создание уведомления
                content=ft.Text(
                    message,
                    color=ft.Colors.RED_500
                ),
                bgcolor=ft.Colors.GREY_900,
                duration=5000,
            )
            page.overlay.append(snack)  # Добавление уведомления
            snack.open = True  # Открытие уведомления
            page.update()

        async def show_analytics(e):
            """Показ статистики использования"""
            stats = self.analytics.get_statistics()

            # Создание диалога статистики
            dialog = ft.AlertDialog(
                title=ft.Text("Аналитика"),
                content=ft.Column([
                    ft.Text(f"Всего сообщений: {stats['total_messages']}"),
                    ft.Text(f"Всего токенов: {stats['total_tokens']}"),
                    ft.Text(f"Среднее токенов/сообщение: {stats['tokens_per_message']:.2f}"),
                    ft.Text(f"Сообщений в минуту: {stats['messages_per_minute']:.2f}")
                ]),
                actions=[
                    ft.TextButton("Закрыть", on_click=lambda e: close_dialog(dialog)),
                ],
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        async def clear_history(e):
            """
            Очистка истории чата.
            """
            try:
                self.cache.clear_history()
                self.analytics.clear_data()
                self.chat_history.controls.clear()

            except Exception as e:
                self.logger.error(f"Ошибка очистки истории: {e}")
                show_error_snack(page, f"Ошибка очистки истории: {str(e)}")

        async def confirm_clear_history(e):
            """Подтверждение очистки истории"""

            def close_dlg(e):  # Функция закрытия диалога
                close_dialog(dialog)

            async def clear_confirmed(e):  # Функция подтверждения очистки
                await clear_history(e)
                close_dialog(dialog)

            # Создание диалога подтверждения
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Подтверждение удаления"),
                content=ft.Text("Вы уверены? Это действие нельзя отменить!"),
                actions=[
                    ft.TextButton("Отмена", on_click=close_dlg),
                    ft.TextButton("Очистить", on_click=clear_confirmed),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        async def save_dialog(e):
            """
            Сохранение истории диалога в JSON файл.
            """
            try:
                history = self.cache.get_chat_history()

                # Форматирование данных для сохранения
                dialog_data = []
                for msg in history:
                    dialog_data.append({
                        "timestamp": msg[4],
                        "model": msg[1],
                        "user_message": msg[2],
                        "ai_response": msg[3],
                        "tokens_used": msg[5]
                    })

                # Создание имени файла
                filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.exports_dir, filename)

                # Сохранение в JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialog_data, f, ensure_ascii=False, indent=2, default=str)

                # Создание диалога успешного сохранения
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Диалог сохранен"),
                    content=ft.Column([
                        ft.Text("Путь сохранения:"),
                        ft.Text(filepath, selectable=True, weight=ft.FontWeight.BOLD),
                    ]),
                    actions=[
                        ft.TextButton("OK", on_click=lambda e: close_dialog(dialog)),
                        ft.TextButton("Открыть папку",
                                      on_click=lambda e: os.startfile(self.exports_dir)
                                      ),
                    ],
                )

                page.overlay.append(dialog)
                dialog.open = True
                page.update()

            except Exception as e:
                self.logger.error(f"Ошибка сохранения: {e}")
                show_error_snack(page, f"Ошибка сохранения: {str(e)}")

        def close_dialog(dialog):
            """Закрытие диалогового окна"""
            dialog.open = False
            page.update()

            if dialog in page.overlay:
                page.overlay.remove(dialog)

        # Создание компонентов интерфейса
        self.message_input = ft.TextField(**AppStyles.MESSAGE_INPUT)  # Поле ввода
        self.chat_history = ft.ListView(**AppStyles.CHAT_HISTORY)  # История чата

        # Загрузка существующей истории
        self.load_chat_history()

        # Создание кнопок управления
        save_button = ft.ElevatedButton(
            on_click=save_dialog,  # Привязка функции сохранения
            **AppStyles.SAVE_BUTTON  # Применение стилей
        )

        clear_button = ft.ElevatedButton(
            on_click=confirm_clear_history,  # Привязка функции очистки
            **AppStyles.CLEAR_BUTTON  # Применение стилей
        )

        send_button = ft.ElevatedButton(
            on_click=send_message_click,  # Привязка функции отправки
            **AppStyles.SEND_BUTTON  # Применение стилей
        )

        analytics_button = ft.ElevatedButton(
            on_click=show_analytics,  # Привязка функции аналитики
            **AppStyles.ANALYTICS_BUTTON  # Применение стилей
        )

        # Создание layout компонентов

        # Создание ряда кнопок управления
        control_buttons = ft.Row(
            controls=[  # Размещение кнопок в ряд
                save_button,
                analytics_button,
                clear_button
            ],
            **AppStyles.CONTROL_BUTTONS_ROW  # Применение стилей к ряду
        )

        # Создание строки ввода с кнопкой отправки
        input_row = ft.Row(
            controls=[  # Размещение элементов ввода
                self.message_input,
                send_button
            ],
            **AppStyles.INPUT_ROW  # Применение стилей к строке ввода
        )

        # Создание колонки для элементов управления
        controls_column = ft.Column(
            controls=[  # Размещение элементов управления
                input_row,
                control_buttons
            ],
            **AppStyles.CONTROLS_COLUMN  # Применение стилей к колонке
        )

        # Создание контейнера для баланса
        balance_container = ft.Container(
            content=self.balance_text,  # Размещение текста баланса
            **AppStyles.BALANCE_CONTAINER  # Применение стилей к контейнеру
        )

        # Создание колонки выбора модели
        model_selection = ft.Column(
            controls=[  # Размещение элементов выбора модели
                self.model_dropdown.search_field,
                self.model_dropdown,
                balance_container
            ],
            **AppStyles.MODEL_SELECTION_COLUMN  # Применение стилей к колонке
        )

        # Создание основной колонки приложения
        self.main_column = ft.Column(
            controls=[  # Размещение основных элементов
                model_selection,
                self.chat_history,
                controls_column
            ],
            **AppStyles.MAIN_COLUMN  # Применение стилей к главной колонке
        )

        # Добавление основной колонки на страницу
        page.add(self.main_column)

        # Запуск монитора
        self.monitor.get_metrics()

        # Логирование запуска
        self.logger.info("Приложение запущено")

def main():
    """Точка входа в приложение"""
    app = ChatApp()                              # Создание экземпляра приложения
    ft.app(target=app.main)                      # Запуск приложения

if __name__ == "__main__":
    main()