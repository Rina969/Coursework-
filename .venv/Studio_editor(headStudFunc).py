class StudioEditor:
    """
    Класс для управления процессом редактирования студии.

    Вместо сложного FSM используем простой словарь для хранения состояний.
    Каждый пользователь имеет свой набор данных.
    """

    def __init__(self):
        """
        Инициализация редактора студии.

        Создаем словарь для хранения состояния пользователей:
        - Ключ: user_id (ID пользователя в Telegram)
        - Значение: словарь с данными и этапом редактирования
        """
        self.user_sessions = {}
        # Пример структуры данных для одного пользователя:
        # {
        #     'step': 'waiting_for_name',  # Текущий этап
        #     'data': {                    # Собранные данные
        #         'name': 'Название студии',
        #         'image': b'...',        # Бинарные данные изображения
        #         'description': 'Описание'
        #     }
        # }

    def start_editing(self, user_id):
        """
        Начинает процесс редактирования для пользователя.

        Args:
            user_id (int): ID пользователя в Telegram

        Returns:
            str: Сообщение для отправки пользователю
        """
        # Сбрасываем предыдущую сессию, если была
        self.user_sessions[user_id] = {
            'step': 'waiting_for_name',  # Первый шаг - ждем название
            'data': {}  # Пока данных нет
        }

        return "🎬 <b>Редактирование студии</b>\n\nШаг 1 из 3\n📝 <b>Введите новое название студии:</b>"

    def handle_message(self, user_id, message_text):
        """
        Обрабатывает текстовое сообщение от пользователя.

        Args:
            user_id (int): ID пользователя
            message_text (str): Текст сообщения

        Returns:
            tuple: (сообщение для пользователя, этап завершен?)
        """
        # Проверяем, есть ли активная сессия у пользователя
        if user_id not in self.user_sessions:
            return "❌ Сначала начните редактирование студии!", False

        session = self.user_sessions[user_id]
        current_step = session['step']

        # Обрабатываем в зависимости от текущего этапа
        if current_step == 'waiting_for_name':
            # Этап 1: Получаем название студии
            if len(message_text.strip()) < 2:
                return "❌ Название слишком короткое! Введите название длиннее 2 символов.", False

            # Сохраняем название
            session['data']['name'] = message_text.strip()
            session['step'] = 'waiting_for_image'  # Переходим к следующему этапу

            return ("✅ <b>Название сохранено!</b>\n\n"
                    "Шаг 2 из 3\n"
                    "🖼️ <b>Отправьте новое промо-изображение:</b>\n\n"
                    "<i>Просто отправьте фото в чат ⤵️</i>", False)

        elif current_step == 'waiting_for_description':
            # Этап 3: Получаем описание студии
            session['data']['description'] = message_text.strip()

            # Завершаем процесс редактирования
            result = self._finish_editing(user_id)
            return result, True  # True означает, что процесс завершен

        else:
            # Если этап не предусматривает текстовый ввод
            return "⏳ Пожалуйста, отправьте изображение или завершите текущий этап.", False

    def handle_image(self, user_id, image_bytes):
        """
        Обрабатывает изображение от пользователя.

        Args:
            user_id (int): ID пользователя
            image_bytes (bytes): Бинарные данные изображения

        Returns:
            tuple: (сообщение для пользователя, этап завершен?)
        """
        # Проверяем, есть ли активная сессия
        if user_id not in self.user_sessions:
            return "❌ Сначала начните редактирование студии!", False

        session = self.user_sessions[user_id]

        # Проверяем, что мы на этапе ожидания изображения
        if session['step'] != 'waiting_for_image':
            return "❌ Сейчас не время отправлять изображение!", False

        # Сохраняем изображение
        session['data']['image'] = image_bytes
        session['step'] = 'waiting_for_description'  # Переходим к описанию

        return ("✅ <b>Изображение сохранено!</b>\n\n"
                "Шаг 3 из 3\n"
                "📝 <b>Введите новое описание студии:</b>", False)

    def _finish_editing(self, user_id):
        """
        Завершает процесс редактирования.

        Args:
            user_id (int): ID пользователя

        Returns:
            str: Итоговое сообщение с собранными данными
        """
        if user_id not in self.user_sessions:
            return "❌ Нет активной сессии редактирования!"

        session = self.user_sessions[user_id]
        data = session['data']

        # Формируем итоговое сообщение
        result_message = (
            "✅ <b>Редактирование завершено!</b>\n\n"
            f"<b>Название:</b> {data.get('name', 'Не указано')}\n"
            f"<b>Описание:</b> {data.get('description', 'Не указано')}\n"
            f"<b>Изображение:</b> {'Загружено' if 'image' in data else 'Не загружено'}\n\n"
            "<i>Данные готовы для сохранения в базу данных.</i>"
        )

        # Здесь будет код для сохранения в БД (позже добавим)
        # save_to_database(data)

        # Очищаем сессию пользователя
        del self.user_sessions[user_id]

        return result_message

    def cancel_editing(self, user_id):
        """
        Отменяет процесс редактирования.

        Args:
            user_id (int): ID пользователя

        Returns:
            str: Сообщение об отмене
        """
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        return "❌ Редактирование отменено."

    def get_user_step(self, user_id):
        """
        Получает текущий этап пользователя.

        Args:
            user_id (int): ID пользователя

        Returns:
            str or None: Текущий этап или None если сессии нет
        """
        if user_id in self.user_sessions:
            return self.user_sessions[user_id]['step']
        return None


# Создаем глобальный экземпляр редактора
studio_editor = StudioEditor()