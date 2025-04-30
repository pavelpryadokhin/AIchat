import flet as ft
from ui.styles import AppStyles
import asyncio

class MessageBubble(ft.Container):
    """
    Args:
        message (str): Текст сообщения для отображения
        is_user (bool): Флаг, указывающий, является ли это сообщением пользователя
    """
    def __init__(self, message: str, is_user: bool):
        super().__init__()

        # Настройка отступов внутри пузырька
        self.padding = 10

        # Настройка скругления углов пузырька
        self.border_radius = 10

        # Установка цвета фона в зависимости от отправителя:
        # - Синий для сообщений пользователя
        # - Серый для сообщений AI
        self.bgcolor = ft.Colors.BLUE_700 if is_user else ft.Colors.GREY_700

        # Установка выравнивания пузырька:
        # - Справа для сообщений пользователя
        # - Слева для сообщений AI
        self.alignment = ft.alignment.center_right if is_user else ft.alignment.center_left

        # Настройка внешних отступов для создания эффекта диалога:
        # - Отступ слева для сообщений пользователя
        # - Отступ справа для сообщений AI
        # - Небольшие отступы сверху и снизу для разделения сообщений
        self.margin = ft.margin.only(
            left=50 if is_user else 0,      # Отступ слева
            right=0 if is_user else 50,      # Отступ справа
            top=5,                           # Отступ сверху
            bottom=5                         # Отступ снизу
        )

        # Создание содержимого пузырька
        self.content = ft.Column(
            controls=[
                # Текст сообщения с настройками отображения
                ft.Text(
                    value=message,                    # Текст сообщения
                    color=ft.Colors.WHITE,            # Белый цвет текста
                    size=16,                         # Размер шрифта
                    selectable=True,                 # Возможность выделения текста
                    weight=ft.FontWeight.W_400       # Нормальная толщина шрифта
                )
            ],
            tight=True  # Плотное расположение элементов в колонке
        )


class ModelSelector(ft.Dropdown):
    """
    Выпадающий список для выбора AI модели с функцией поиска.

    Наследуется от ft.Dropdown для создания кастомного выпадающего списка
    с дополнительным полем поиска для фильтрации моделей.

    Args:
        models (list): Список доступных моделей в формате:
                      [{"id": "model-id", "name": "Model Name"}, ...]
    """
    def __init__(self, models: list):
        super().__init__()

        # Применение стилей из конфигурации к компоненту
        for key, value in AppStyles.MODEL_DROPDOWN.items():
            setattr(self, key, value)

        # Настройка внешнего вида выпадающего списка
        self.label = None                    # Убираем текстовую метку
        self.hint_text = "Выбор модели"      # Текст-подсказка

        # Создание списка опций из предоставленных моделей
        self.options = [
            ft.dropdown.Option(
                key=model['id'],             # ID модели как ключ
                text=model['name']           # Название модели как отображаемый текст
            ) for model in models
        ]

        # Сохранение полного списка опций для фильтрации
        self.all_options = self.options.copy()

        # Установка начального значения (первая модель из списка)
        self.value = models[0]['id'] if models else None

        # Создание поля поиска для фильтрации моделей
        self.search_field = ft.TextField(
            on_change=self.filter_options,        # Функция обработки изменений
            hint_text="Поиск модели",            # Текст-подсказка в поле поиска
            **AppStyles.MODEL_SEARCH_FIELD       # Применение стилей из конфигурации
        )

    def filter_options(self, e):
        """
        Фильтрация списка моделей на основе введенного текста поиска.

        Args:
            e: Событие изменения текста в поле поиска
        """
        # Получение текста поиска в нижнем регистре
        search_text = self.search_field.value.lower() if self.search_field.value else ""

        # Если поле поиска пустое - показываем все модели
        if not search_text:
            self.options = self.all_options
        else:
            # Фильтрация моделей по тексту поиска
            # Ищем совпадения в названии или ID модели
            self.options = [
                opt for opt in self.all_options
                if search_text in opt.text.lower() or search_text in opt.key.lower()
            ]

        # Обновление интерфейса для отображения отфильтрованного списка
        e.page.update()


class AuthScreen(ft.UserControl):
    """
    Экран аутентификации с поддержкой ввода API ключа и PIN-кода.
    
    Предоставляет интерфейс для:
    - Ввода API ключа OpenRouter при первом использовании
    - Ввода PIN-кода для последующих входов
    - Возможности сброса API ключа
    """
    
    def __init__(self, on_submit_api_key, on_submit_pin, on_reset):
        """
        Инициализация экрана аутентификации.
        
        Args:
            on_submit_api_key: Функция обратного вызова при отправке API ключа
            on_submit_pin: Функция обратного вызова при отправке PIN-кода
            on_reset: Функция обратного вызова при сбросе ключа
        """
        super().__init__()
        self.on_submit_api_key = on_submit_api_key
        self.on_submit_pin = on_submit_pin
        self.on_reset = on_reset
        
        # Состояние экрана: 'pin' или 'api_key'
        self.mode = 'pin'  # По умолчанию показываем ввод PIN
        
        # Поле для ввода с применением стилей из AppStyles
        self.input_field = ft.TextField(
            label="Введите PIN-код",
            hint_text="4-значный PIN",
            password=True,  # Обязательно включено для маскировки ввода
            bgcolor=ft.Colors.GREY_800,
            border_color=ft.Colors.GREY_700,
            focused_border_color=ft.Colors.BLUE_400,
            color=ft.Colors.WHITE,
            cursor_color=ft.Colors.WHITE,
            border_radius=8,
            text_size=18,
            width=300,
            height=70,
            text_align=ft.TextAlign.CENTER,
            on_submit=self.handle_submit,  # Обработчик нажатия Enter
            autofocus=True  # Автоматически ставим фокус на поле ввода при открытии
        )
        
        # Кнопка отправки
        self.submit_button = ft.ElevatedButton(
            text="Войти",
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
                padding=15,
            ),
            width=300,
            height=50,
            on_click=self.handle_submit
        )
        
        # Кнопка переключения режима
        self.mode_switch_button = ft.TextButton(
            text="Использовать API ключ",
            style=ft.ButtonStyle(
                color=ft.Colors.BLUE_400
            ),
            on_click=self.switch_mode
        )
        
        # Сообщение об ошибке
        self.error_message = ft.Text(
            color=ft.Colors.RED_500,
            size=14,
            visible=False
        )
        
        # Информационное сообщение (для отображения PIN)
        self.info_message = ft.Text(
            color=ft.Colors.GREEN_400,
            size=16,
            text_align=ft.TextAlign.CENTER,
            visible=False
        )
    
    def build(self):
        """
        Создание интерфейса экрана аутентификации.
        
        Returns:
            ft.Container: Контейнер с элементами интерфейса
        """
        # Заголовок
        title = ft.Text(
            "AI Chat",
            size=32,
            color=ft.Colors.BLUE_700,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Подзаголовок
        subtitle = ft.Text(
            "Авторизация",
            size=22,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500,
        )
        
        # Основной контейнер с оформлением в стиле основного приложения
        return ft.Container(
            content=ft.Column(
                controls=[
                    title,
                    subtitle,
                    ft.Container(height=30),  # Отступ
                    self.input_field,
                    self.error_message,
                    self.info_message,
                    ft.Container(height=10),  # Отступ
                    self.submit_button,
                    self.mode_switch_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.center,
            padding=30,
            border_radius=10,
            bgcolor=ft.Colors.GREY_900,  # Темный фон как в основном приложении
            width=400,
            height=500,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK,
                offset=ft.Offset(0, 5),
            )
        )
    
    def switch_mode(self, e):
        """
        Переключение между режимами ввода API ключа и PIN-кода.
        
        Args:
            e: Событие клика
        """
        if self.mode == 'pin':
            self.mode = 'api_key'
            self.input_field.label = "Введите API ключ OpenRouter"
            self.input_field.hint_text = "Ваш API ключ"
            self.input_field.password = True
            self.mode_switch_button.text = "Использовать PIN-код"
            self.submit_button.text = "Подтвердить"
        else:
            self.mode = 'pin'
            self.input_field.label = "Введите PIN-код"
            self.input_field.hint_text = "4-значный PIN"
            self.input_field.password = True
            self.mode_switch_button.text = "Использовать API ключ"
            self.submit_button.text = "Войти"
        
        # После переключения режима ставим фокус на поле ввода
        self.input_field.focus()
        
        # Сброс сообщений
        self.error_message.visible = False
        self.info_message.visible = False
        self.input_field.value = ""
        self.update()
    
    def handle_submit(self, e):
        """
        Обработка отправки формы.
        
        Args:
            e: Событие клика или нажатия Enter
        """
        if not self.input_field.value:
            self.show_error("Поле не может быть пустым")
            return
        
        if self.mode == 'pin':
            # Проверка PIN-кода
            self.on_submit_pin(self.input_field.value)
        else:
            # Отправка API ключа
            self.on_submit_api_key(self.input_field.value)
    
    def show_error(self, message):
        """
        Отображение сообщения об ошибке.
        
        Args:
            message: Текст сообщения об ошибке
        """
        self.error_message.value = message
        self.error_message.visible = True
        self.info_message.visible = False
        self.update()
    
    def show_success(self, message):
        """
        Отображение информационного сообщения.
        
        Args:
            message: Текст информационного сообщения
        """
        self.info_message.value = message
        self.info_message.visible = True
        self.error_message.visible = False
        self.update()
    
    def reset_form(self):
        """
        Сброс формы.
        """
        self.input_field.value = ""
        self.error_message.visible = False
        self.info_message.visible = False
        self.input_field.focus()  # Возвращаем фокус на поле ввода
        self.update()