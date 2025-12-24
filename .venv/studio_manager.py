import telebot
from telebot import types
import logging
from typing import Dict, Any, List
from database import get_pending_applications, get_application_details, update_application_status, get_student_by_user_id

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

<<<<<<< HEAD
=======
class StudioManager:
    """Класс для управления анкетами руководителем студии"""
    # user_states: состояние каждого руководителя(какие заявки просматривает, текущая позиция)
    def __init__(self, bot, db_path: str = "student_studios_bot (1).db"):
       
        self.bot = bot
        self.db_path = db_path
        
        # Состояния пользователей
        self.user_states = {}
        
        # Кэш заявок для быстрого доступа
        self.applications_cache = {}
    
    def get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с БД"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def start_reviewing_applications_with_id(self, user_id: int, studio_id: int) -> bool:
        """Начинает просмотр заявок для указанного пользователя и студии"""
        try:
            # Получаем новые заявки
            applications = self.get_new_applications(studio_id)

            if not applications:
                return False

            # Сохраняем состояние пользователя
            self.user_states[user_id] = {
                'studio_id': studio_id,
                'applications': applications,
                'current_index': 0,
                'status': 'reviewing'
            }

            return True

        except Exception as e:
            logger.error(f"Error starting review for user {user_id}, studio {studio_id}: {e}")
            return False

    def get_studio_id_for_head(self, user_id: int) -> Optional[int]:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                print(f"\n[DEBUG] Ищу студию для user_id: {user_id}")

                cursor.execute("""
                    SELECT studio_id 
                    FROM studios 
                    WHERE head_user_id = ?
                """, (user_id,))

                result = cursor.fetchone()
                print(f"[DEBUG] Результат запроса: {result}")

                if result:
                    print(f"[DEBUG] Найдена студия ID: {result[0]}")
                else:
                    print(f"[DEBUG] Студия не найдена для user_id: {user_id}")
                    # Покажем все студии для отладки
                    cursor.execute("SELECT studio_id, name, head_user_id FROM studios")
                    all_studios = cursor.fetchall()
                    print(f"[DEBUG] Все студии в базе: {all_studios}")

                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting studio for head {user_id}: {e}")
            return None
    
    def get_new_applications(self, studio_id: int) -> List[Tuple[int, str, str, str]]:
        #Получает ВСЕ новые заявки
        #Возвращает:Список кортежей (application_id, summary, full_name, created_at)
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c

class StudioManager:
    def __init__(self, bot):
        self.bot = bot
        self.user_states = {}  # {telegram_id: state_dict}


    def start_reviewing_applications(self, telegram_id: int, studio_id: int, chat_id: int) -> bool:
        """Начинает просмотр заявок руководителем"""
        try:
            # Получаем ожидающие заявки
            applications = get_pending_applications(studio_id)

            if not applications:
                logger.info(f"Нет новых заявок для студии {studio_id}")
                return False

            # Сохраняем состояние пользователя
            self.user_states[telegram_id] = {
                'studio_id': studio_id,
                'applications': applications,
                'current_index': 0,
                'chat_id': chat_id,
                'status': 'reviewing'
            }

            # Информационное сообщение
            self.bot.send_message(
                chat_id,
                f"<b>Начинаем просмотр заявок</b>\n\n"
                f"<b>Всего заявок:</b> {len(applications)}\n\n"
                f"<i>Заявки показываются по одной. Используйте кнопки для действий:</i>\n",
                parse_mode='HTML'
            )

            self.show_next_application(chat_id, telegram_id)
            return True

        except Exception as e:
            logger.error(f"Ошибка начала просмотра для руководителя {telegram_id}: {e}")
            return False


    def show_next_application(self, chat_id: int, telegram_id: int):
        """Показывает следующую заявку в очереди"""
        if telegram_id not in self.user_states:
            return

        state = self.user_states[telegram_id]
        applications = state['applications']
        current_index = state['current_index']

        if current_index >= len(applications):
            # Все заявки обработаны
            self.bot.send_message(
                chat_id,
                "🎉 <b>Все заявки рассмотрены!</b>\n\n"
                "Новых заявок в очереди нет.",
                parse_mode='HTML'
            )

            # Очищаем состояние
            del self.user_states[telegram_id]
            return

        # Получаем текущую заявку
        app_data = applications[current_index]
        app_id = app_data['application_id']

        # Получаем детальную информацию
        details = get_application_details(app_id)

        if not details:
            # Если ошибка, пропускаем эту заявку
            self.bot.send_message(
                chat_id,
                f"⚠️ Ошибка загрузки заявки #{app_id}. Пропускаем...",
                parse_mode='HTML'
            )
            state['current_index'] += 1
            self.show_next_application(chat_id, telegram_id)
            return

        # Сохраняем ID текущей заявки
        state['current_application_id'] = app_id

        # Форматируем сообщение
        message_text = self.format_application_message(details, current_index + 1, len(applications))

        # Создаем inline-клавиатуру
        markup = types.InlineKeyboardMarkup(row_width=2)

        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f"accept:{app_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{app_id}")
        )

        markup.add(
            types.InlineKeyboardButton("📞 Связаться", callback_data=f"contact:{app_id}"),
            types.InlineKeyboardButton("Прекратить", callback_data="stop_review")
        )

        # Отправляем сообщение
        self.bot.send_message(
            chat_id,
            message_text,
            parse_mode='HTML',
            reply_markup=markup
        )

    def format_application_message(self, app_data: Dict[str, Any], current_num: int, total: int) -> str:
        """Форматирует сообщение с информацией о заявке"""
        message = f"<b>Заявка #{app_data['application_id']}</b>\n\n"
        message += f"<b>Студент:</b> {app_data['full_name']}\n"

        if app_data.get('student_group'):
            message += f"<b>Группа:</b> {app_data['student_group']}\n"

        if app_data.get('username'):
            message += f"<b>Telegram:</b> @{app_data['username']}\n"

        if app_data.get('phone_number'):
            message += f"<b>Телефон:</b> {app_data['phone_number']}\n"

        if app_data.get('email'):
            message += f"<b>Email:</b> {app_data['email']}\n"

        message += f"\n<b>Сводка:</b>\n{app_data.get('summary', 'Нет сводки')}\n"

        if app_data.get('answers'):
            message += f"\n<b>Ответы на вопросы:</b>\n"
            for i, (question, answer) in enumerate(app_data['answers'].items(), 1):
                message += f"\n<b>{i}. {question}</b>\n{answer}\n"

        message += f"\n<i>Прогресс: {current_num} из {total}</i>"

        return message

    def handle_application_action(self, call):
        """Обрабатывает действия руководителя с заявками"""
        telegram_id = call.from_user.id

        if telegram_id not in self.user_states:
            self.bot.answer_callback_query(call.id, "Сессия устарела. Начните просмотр заново.")
            return

        action_data = call.data
        state = self.user_states[telegram_id]

        if action_data == "stop_review":
            # Прекращаем просмотр
            self.bot.answer_callback_query(call.id, "Просмотр прекращен")

            # Удаляем последнее сообщение с заявкой
            try:
                self.bot.delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass

            # Очищаем состояние
            del self.user_states[telegram_id]

            # Возвращаемся в главное меню
            self.return_to_main_menu(call.message.chat.id)
            return

        # Извлекаем ID заявки и действие
        parts = action_data.split(":")
        if len(parts) != 2:
            self.bot.answer_callback_query(call.id, "Ошибка обработки")
            return

        action, app_id_str = parts
        app_id = int(app_id_str)

        # Проверяем, что это текущая заявка
        if state.get('current_application_id') != app_id:
            self.bot.answer_callback_query(call.id, "Заявка уже обработана")
            return

        # Удаляем текущее сообщение
        try:
            self.bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        # Обрабатываем действие
        if action == "accept":
            self.accept_application(call, app_id, telegram_id)
        elif action == "reject":
            self.reject_application(call, app_id, telegram_id)
        elif action == "contact":
            self.contact_student(call, app_id, telegram_id)

    def accept_application(self, call, application_id: int, telegram_id: int):
        """Принять заявку"""
        try:
            # Получаем данные заявки
            app_data = get_application_details(application_id)
            if not app_data:
                self.bot.answer_callback_query(call.id, "❌ Ошибка при принятии")
                return

            # Обновляем статус
            success = update_application_status(application_id, 'accepted')

            if success:
                # Отправляем уведомление студенту
                self.send_notification_to_student(
                    app_data['student_telegram_id'],
                    app_data['full_name'],
                    app_data['studio_name'],
                    'accepted'
                )

                self.bot.answer_callback_query(call.id, "✅ Заявка принята")

                # Удаляем заявку из состояния и показываем следующую
                self.remove_processed_application(telegram_id, application_id)
                state = self.user_states[telegram_id]
                self.show_next_application(state['chat_id'], telegram_id)
            else:
                self.bot.answer_callback_query(call.id, "❌ Ошибка при принятии")

        except Exception as e:
            logger.error(f"Ошибка принятия заявки {application_id}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при принятии")

    def reject_application(self, call, application_id: int, telegram_id: int):
        """Отклонить заявку"""
        try:

            app_data = get_application_details(application_id)
            if not app_data:
                self.bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")
                return

            success = update_application_status(application_id, 'rejected')

            if success:
                self.send_notification_to_student(
                    app_data['student_telegram_id'],
                    app_data['full_name'],
                    app_data['studio_name'],
                    'rejected'
                )

                self.bot.answer_callback_query(call.id, "❌ Заявка отклонена")

                # Удаляем заявку из состояния и показываем следующую
                self.remove_processed_application(telegram_id, application_id)
                state = self.user_states[telegram_id]
                self.show_next_application(state['chat_id'], telegram_id)
            else:
                self.bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")

        except Exception as e:
            logger.error(f"Ошибка отклонения заявки {application_id}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")

    def contact_student(self, call, application_id: int, telegram_id: int):
        """Показать контакты студента и переместить заявку в конец"""
        try:
            # Получаем данные заявки
            app_data = get_application_details(application_id)
            if not app_data:
                self.bot.answer_callback_query(call.id, "❌ Ошибка")
                return

            # Формируем контактную информацию
            contact_info = f"<b>Контакты студента:</b>\n\n"
            contact_info += f"<b>Имя:</b> {app_data['full_name']}\n"

            if app_data.get('username'):
                contact_info += f"<b>Telegram:</b> @{app_data['username']}\n"

            if app_data.get('phone_number'):
                contact_info += f"<b>Телефон:</b> {app_data['phone_number']}\n"

            if app_data.get('email'):
                contact_info += f"<b>Email:</b> {app_data['email']}\n"

            if app_data.get('student_group'):
                contact_info += f"<b>Группа:</b> {app_data['student_group']}\n"


            # Перемещаем заявку в конец очереди
            self.move_application_to_end(telegram_id, application_id)
            state = self.user_states[telegram_id]
            self.show_next_application(state['chat_id'], telegram_id)

        except Exception as e:
            logger.error(f"Ошибка получения контактов для заявки {application_id}: {e}")
            self.bot.answer_callback_query(call.id, "❌ Ошибка")

    def send_notification_to_student(self, student_telegram_id: str, student_name: str, studio_name: str, action: str):
        """Отправляет уведомление студенту"""
        try:
            if not student_telegram_id:
                return

            if action == 'accepted':
                message = (
                    f"🎉 <b>Поздравляем, {student_name}!</b>\n\n"
                    f"Ваша заявка в студию <b>'{studio_name}'</b> одобрена!\n\n"
                    f"Руководитель свяжется с вами для дальнейших инструкций."
                )
            elif action == 'rejected':
                message = (
                    f"<b>Уважаемый(ая) {student_name}!</b>\n\n"
                    f"К сожалению, ваша заявка в студию <b>'{studio_name}'</b> отклонена.\n\n"
                    f"Не расстраивайтесь! Вы можете подать заявку в другие студии."
                )
            else:
                return

            self.bot.send_message(
                student_telegram_id,
                message,
                parse_mode='HTML'
            )

            logger.info(f"✅ Уведомление отправлено студенту {student_telegram_id}")

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления студенту: {e}")


    def remove_processed_application(self, telegram_id: int, application_id: int):
        """Удаляет обработанную заявку из состояния пользователя"""
        if telegram_id not in self.user_states:
            return

        state = self.user_states[telegram_id]
        applications = state['applications']

        new_applications = [
            app for app in applications
            if app['application_id'] != application_id
        ]

        state['applications'] = new_applications

        if state['current_index'] >= len(new_applications):
            state['current_index'] = 0

    def move_application_to_end(self, telegram_id: int, application_id: int):
        """Перемещает заявку в конец очереди"""
        if telegram_id not in self.user_states:
            return

        state = self.user_states[telegram_id]
        applications = state['applications']

        # Находим заявку
        target_app = None
        other_apps = []

        for app in applications:
            if app['application_id'] == application_id:
                target_app = app
            else:
                other_apps.append(app)

        if target_app:
            state['applications'] = other_apps + [target_app]
            # Переходим к следующей заявке
            state['current_index'] = 0

    def return_to_main_menu(self, chat_id: int):
        """Возвращает в главное меню руководителя"""
        from head_of_studio import HeadOfStudio
        from telebot import types

        # Создаем меню руководителя
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

        btn_new_applications = types.KeyboardButton('Новые заявки')
        btn_statistics = types.KeyboardButton('Статистика')
        btn_edit_studio = types.KeyboardButton('Изменить информацию о студии')
        btn_refresh = types.KeyboardButton('Обновить')

        markup.row(btn_new_applications, btn_statistics)
        markup.row(btn_edit_studio)
        markup.row(btn_refresh)

        self.bot.send_message(
            chat_id,
            parse_mode='HTML',
            reply_markup=markup
        )





# import telebot
# from telebot import types
# import sqlite3
# from typing import Dict, Any, Optional, List, Tuple
# import logging
# from datetime import datetime
#
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)
#
# class StudioManager:
#     """Класс для управления анкетами руководителем студии"""
#     # user_states: состояние каждого руководителя(какие заявки просматривает, текущая позиция)
#     def __init__(self, bot, db_path: str = "student_studios_bot (1).db"):
#
#         self.bot = bot
#         self.db_path = db_path
#
#         # Состояния пользователей
#         self.user_states = {}
#
#         # Кэш заявок для быстрого доступа
#         self.applications_cache = {}
#
#     def get_connection(self) -> sqlite3.Connection:
#         """Возвращает соединение с БД"""
#         return sqlite3.connect(self.db_path, check_same_thread=False)
#
#     def start_reviewing_applications_with_id(self, user_id: int, studio_id: int) -> bool:
#         """Начинает просмотр заявок для указанного пользователя и студии"""
#         try:
#             # Получаем новые заявки
#             applications = self.get_new_applications(studio_id)
#
#             if not applications:
#                 return False
#
#             # Сохраняем состояние пользователя
#             self.user_states[user_id] = {
#                 'studio_id': studio_id,
#                 'applications': applications,
#                 'current_index': 0,
#                 'status': 'reviewing'
#             }
#
#             return True
#
#         except Exception as e:
#             logger.error(f"Error starting review for user {user_id}, studio {studio_id}: {e}")
#             return False
#
#     def get_studio_id_for_head(self, user_id: int) -> Optional[int]:
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#                 print(f"\n[DEBUG] Ищу студию для user_id: {user_id}")
#
#                 cursor.execute("""
#                     SELECT studio_id
#                     FROM studios
#                     WHERE head_user_id = ?
#                 """, (user_id,))
#
#                 result = cursor.fetchone()
#                 print(f"[DEBUG] Результат запроса: {result}")
#
#                 if result:
#                     print(f"[DEBUG] Найдена студия ID: {result[0]}")
#                 else:
#                     print(f"[DEBUG] Студия не найдена для user_id: {user_id}")
#                     # Покажем все студии для отладки
#                     cursor.execute("SELECT studio_id, name, head_user_id FROM studios")
#                     all_studios = cursor.fetchall()
#                     print(f"[DEBUG] Все студии в базе: {all_studios}")
#
#                 return result[0] if result else None
#         except Exception as e:
#             logger.error(f"Error getting studio for head {user_id}: {e}")
#             return None
#
#     def get_new_applications(self, studio_id: int) -> List[Tuple[int, str, str, str]]:
#         #Получает ВСЕ новые заявки
#         #Возвращает:Список кортежей (application_id, summary, full_name, created_at)
#
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#                 cursor.execute("""
#                     SELECT
#                         a.application_id,
#                         a.summary,
#                         u.full_name,
#                         a.created_at,
#                         u.username,
#                         u.phone_number,
#                         u.email
#                     FROM applications a
#                     JOIN users u ON a.user_id = u.user_id
#                     WHERE a.studio_id = ?
#                     AND a.status = 'pending'
#                     ORDER BY a.created_at ASC
#                 """, (studio_id,))
#
#                 return cursor.fetchall()
#         except Exception as e:
#             logger.error(f"Error getting applications for studio {studio_id}: {e}")
#             return []
#
#     def get_application_details(self, application_id: int) -> Optional[Dict[str, Any]]:
#         #Получает детальную информацию о заявке по ее айди
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 # Получаем основную информацию о заявке
#                 cursor.execute("""
#                     SELECT
#                         a.application_id, a.summary, a.status, a.created_at,
#                         u.user_id, u.telegram_id, u.full_name, u.student_group,
#                         u.phone_number, u.email, u.username,
#                         s.name as studio_name
#                     FROM applications a
#                     JOIN users u ON a.user_id = u.user_id
#                     JOIN studios s ON a.studio_id = s.studio_id
#                     WHERE a.application_id = ?
#                 """, (application_id,))
#
#                 result = cursor.fetchone()
#                 if not result:
#                     return None
#
#                 # Получаем ответы на вопросы
#                 cursor.execute("""
#                     SELECT question_text, answer_text
#                     FROM application_answers
#                     WHERE application_id = ?
#                     ORDER BY answer_id
#                 """, (application_id,))
#
#                 answers = cursor.fetchall()
#
#                 # Формируем словарь с данными
#                 app_data = {
#                     'application_id': result[0],
#                     'summary': result[1],
#                     'status': result[2],
#                     'created_at': result[3],
#                     'user_id': result[4],
#                     'user_telegram_id': result[5],
#                     'full_name': result[6],
#                     'student_group': result[7],
#                     'phone_number': result[8],
#                     'email': result[9],
#                     'username': result[10],
#                     'studio_name': result[11],
#                     'answers': dict(answers) if answers else {}
#                 }
#
#                 # Сохраняем в кэш
#                 self.applications_cache[application_id] = app_data
#                 return app_data
#
#         except Exception as e:
#             logger.error(f"Error getting application details {application_id}: {e}")
#             return None
#
#     def format_application_message(self, app_data: Dict[str, Any]) -> str:
#         """Форматирует сообщение с информацией о заявке"""
#         if not app_data:
#             return "❌ Ошибка загрузки заявки"
#
#         message = f"<b>Заявка #{app_data['application_id']}</b>\n"
#         message += f"<b>Студент:</b> {app_data['full_name']}\n"
#         message += f"<b>Группа:</b> {app_data['student_group'] or 'Не указана'}\n"
#
#         if app_data.get('username'):
#             message += f"<b>Telegram:</b> @{app_data['username']}\n"
#
#         if app_data.get('phone_number'):
#             message += f"<b>Телефон:</b> {app_data['phone_number']}\n"
#
#         if app_data.get('email'):
#             message += f"<b>Email:</b> {app_data['email']}\n\n"
#         else:
#             message += "\n"
#
#         # Добавляем ответы на вопросы
#         if app_data.get('answers'):
#             message += "<b>Ответы на вопросы:</b>\n"
#             for i, (question, answer) in enumerate(app_data['answers'].items(), 1):
#                 message += f"{i}. <b>{question}</b>\n{answer}\n\n"
#         elif app_data.get('summary'):
#             message += "<b>Сводка анкеты:</b>\n"
#             # Преобразуем Markdown в HTML для лучшего отображения
#             summary = app_data['summary'].replace('*', '').replace('_', '')
#             message += f"{summary}\n\n"
#
#         # Показываем прогресс
#         if 'user_id' in self.user_states:
#             user_id = None
#             for uid, state in self.user_states.items():
#                 if state.get('current_application_id') == app_data['application_id']:
#                     user_id = uid
#                     break
#
#             if user_id:
#                 state = self.user_states[user_id]
#                 current_idx = state.get('current_index', 0) + 1
#                 total = len(state.get('applications', []))
#                 message += f"<i>Прогресс: {current_idx} из {total}</i>"
#
#         return message
#
#     def start_reviewing_applications(self, message):
#         """Начинает просмотр заявок руководителем"""
#         user_id = message.from_user.id
#
#         # Получаем студию руководителя
#         studio_id = self.get_studio_id_for_head(user_id)
#         if not studio_id:
#             self.bot.send_message(
#                 message.chat.id,
#                 "❌ Вы не закреплены ни за одной студией.",
#                 parse_mode='HTML'
#             )
#             return
#
#         # Получаем новые заявки
#         applications = self.get_new_applications(studio_id)
#
#         if not applications:
#             self.bot.send_message(
#                 message.chat.id,
#                 "Нет новых заявок для рассмотрения.",
#                 parse_mode='HTML'
#             )
#             return
#
#         # Получаем название студии для сообщения
#         studio_name = self.get_studio_name(studio_id)
#
#         # Показываем информацию о количестве заявок
#         self.bot.send_message(
#             message.chat.id,
#             f"<b>{studio_name}</b>\n"
#             f"Найдено заявок: <b>{len(applications)}</b>\n\n",
#             parse_mode='HTML'
#         )
#
#         # Сохраняем состояние пользователя
#         self.user_states[user_id] = {
#             'studio_id': studio_id,
#             'applications': applications,
#             'current_index': 0,
#             'status': 'reviewing'
#         }
#
#         # Показываем первую заявку
#         self.show_next_application(message.chat.id, user_id)
#
#     def show_next_application(self, chat_id: int, user_id: int):
#         """Показывает следующую заявку в очереди"""
#         if user_id not in self.user_states:
#             return
#
#         state = self.user_states[user_id]
#         applications = state['applications']
#         current_index = state['current_index']
#
#         if current_index >= len(applications):
#             # Все заявки обработаны
#             self.bot.send_message(
#                 chat_id,
#                 "<b>Все заявки рассмотрены!</b>\n\n"
#                 "Новых заявок в очереди нет.",
#                 parse_mode='HTML'
#             )
#
#             # Очищаем состояние
#             del self.user_states[user_id]
#             return
#
#         # Получаем текущую заявку
#         app_id, summary, full_name, created_at, username, phone, email = applications[current_index]
#
#         # Получаем данные заявки
#         app_data = self.get_application_details(app_id)
#
#         if not app_data:
#             # Если не удалось загрузить, пропускаем эту заявку
#             self.bot.send_message(
#                 chat_id,
#                 f"⚠️ Ошибка загрузки заявки #{app_id}.",
#                 parse_mode='HTML'
#             )
#
#             # Увеличиваем индекс и показываем следующую
#             state['current_index'] += 1
#             self.show_next_application(chat_id, user_id)
#             return
#
#         # Сохраняем ID текущей заявки
#         state['current_application_id'] = app_id
#
#         # Форматируем сообщение
#         message_text = self.format_application_message(app_data)
#
#         markup = types.InlineKeyboardMarkup()
#
#         markup.row(
#             types.InlineKeyboardButton("✅ Принять", callback_data=f"accept:{app_id}"),
#             types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{app_id}")
#         )
#
#         markup.row(
#             types.InlineKeyboardButton("⏭ Пропустить", callback_data=f"skip:{app_id}")
#         )
#
#         markup.row(
#             types.InlineKeyboardButton("⏹ Прекратить просмотр", callback_data="stop_review")
#         )
#
#         # Отправляем сообщение
#         self.bot.send_message(
#             chat_id,
#             message_text,
#             parse_mode='HTML',
#             reply_markup=markup
#         )
#
#     def handle_application_action(self, call):
#
#         user_id = call.from_user.id
#
#         if user_id not in self.user_states:
#             self.bot.answer_callback_query(call.id, "Сессия устарела")
#             return
#
#         action_data = call.data
#         state = self.user_states[user_id]
#
#         if action_data == "stop_review":
#             # Прекращаем просмотр
#             self.bot.answer_callback_query(call.id, "Просмотр прекращен")
#
#             # Показываем сообщение о прекращении
#             self.bot.edit_message_text(
#                 "<b>Просмотр заявок прекращен</b>\n\n"
#                 "Вы можете возобновить в любой момент.",
#                 call.message.chat.id,
#                 call.message.message_id,
#                 parse_mode='HTML'
#             )
#
#             # Очищаем состояние
#             del self.user_states[user_id]
#             return
#
#
#         # Извлекаем ID заявки и действие
#         parts = action_data.split(":")
#         if len(parts) != 2:
#             self.bot.answer_callback_query(call.id, "Ошибка")
#             return
#
#         action, app_id_str = parts
#         app_id = int(app_id_str)
#
#         # Проверяем, что это текущая заявка
#         if state.get('current_application_id') != app_id:
#             self.bot.answer_callback_query(call.id, "Заявка уже обработана")
#             return
#
#         # Обрабатываем действие
#         if action == "accept":
#             self.accept_application(call, app_id)
#         elif action == "reject":
#             self.reject_application(call, app_id)
#         elif action == "skip":
#             self.skip_application(call, app_id)
#
#     def accept_application(self, call, application_id: int):
#         """Принять заявку """
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 # Обновляем статус заявки
#                 cursor.execute("""
#                     UPDATE applications
#                     SET status = 'accepted',
#                         processed_at = ?
#                     WHERE application_id = ?
#                 """, (datetime.now(), application_id))
#
#                 conn.commit()
#
#                 # Получаем данные студента для уведомления
#                 cursor.execute("""
#                     SELECT u.telegram_id, s.name, u.full_name
#                     FROM applications a
#                     JOIN users u ON a.user_id = u.user_id
#                     JOIN studios s ON a.studio_id = s.studio_id
#                     WHERE a.application_id = ?
#                 """, (application_id,))
#
#                 result = cursor.fetchone()
#                 if result:
#                     student_telegram_id, studio_name, student_name = result
#                     # Отправляем уведомление студенту
#                     try:
#                         self.bot.send_message(
#                             student_telegram_id,
#                             f"🎉 <b>Поздравляем, {student_name}!</b>\n\n"
#                             f"Ваша заявка в студию <b>'{studio_name}'</b> одобрена!\n\n",
#                             parse_mode='HTML'
#                         )
#                     except Exception as e:
#                         logger.error(f"Error notifying student {student_telegram_id}: {e}")
#
#                 self.bot.answer_callback_query(call.id, "✅ Заявка принята")
#
#                 # Удаляем заявку из состояния пользователя
#                 self.remove_application_from_state(call.from_user.id, application_id)
#
#                 # Удаляем сообщение с заявкой
#                 self.bot.delete_message(call.message.chat.id, call.message.message_id)
#
#                 # Показываем следующую заявку (если есть)
#                 self.show_next_application(call.message.chat.id, call.from_user.id)
#
#         except Exception as e:
#             logger.error(f"Error accepting application {application_id}: {e}")
#             self.bot.answer_callback_query(call.id, "❌ Ошибка при принятии")
#
#     def reject_application(self, call, application_id: int):
#         """ Отклонить заявку"""
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 # Обновляем статус заявки
#                 cursor.execute("""
#                     UPDATE applications
#                     SET status = 'rejected',
#                         processed_at = ?
#                     WHERE application_id = ?
#                 """, (datetime.now(), application_id))
#
#                 conn.commit()
#
#                 # Получаем данные студента для уведомления
#                 cursor.execute("""
#                     SELECT u.telegram_id, s.name, u.full_name
#                     FROM applications a
#                     JOIN users u ON a.user_id = u.user_id
#                     JOIN studios s ON a.studio_id = s.studio_id
#                     WHERE a.application_id = ?
#                 """, (application_id,))
#
#                 result = cursor.fetchone()
#                 if result:
#                     student_telegram_id, studio_name, student_name = result
#                     try:
#                         self.bot.send_message(
#                             student_telegram_id,
#                             f"<b>Уважаемый(ая) {student_name}!</b>\n\n"
#                             f"К сожалению, ваша заявка в студию <b>'{studio_name}'</b> не может быть принята.\n\n"
#                             f"Не расстраивайтесь! Вы можете подать заявку в другие студии "
#                             f"или попробовать снова в следующем семестре.",
#                             parse_mode='HTML'
#                         )
#                     except Exception as e:
#                         logger.error(f"Error notifying student {student_telegram_id}: {e}")
#
#                 self.bot.answer_callback_query(call.id, "❌ Заявка отклонена")
#
#                 # Удаляем заявку из состояния пользователя
#                 self.remove_application_from_state(call.from_user.id, application_id)
#
#                 # Удаляем сообщение с заявкой
#                 self.bot.delete_message(call.message.chat.id, call.message.message_id)
#
#                 # Показываем следующую заявку
#                 self.show_next_application(call.message.chat.id, call.from_user.id)
#
#         except Exception as e:
#             logger.error(f"Error rejecting application {application_id}: {e}")
#             self.bot.answer_callback_query(call.id, "❌ Ошибка при отклонении")
#
#
#     def skip_application(self, call, application_id: int):
#         """Пропустить заявку (оставить в очереди)"""
#         # Перемещаем заявку в конец очереди
#         self.move_application_to_end(call.from_user.id, application_id)
#
#         self.bot.answer_callback_query(call.id, "Заявка перемещена в конец очереди")
#
#         # Удаляем текущее сообщение и показываем следующую заявку
#         self.bot.delete_message(call.message.chat.id, call.message.message_id)
#         self.show_next_application(call.message.chat.id, call.from_user.id)
#
#     def remove_application_from_state(self, user_id: int, application_id: int):
#         """Удаляет заявку из состояния пользователя"""
#         if user_id not in self.user_states:
#             return
#
#         state = self.user_states[user_id]
#         applications = state['applications']
#
#         # Удаляем заявку из списка
#         new_applications = [
#             app for app in applications
#             if app[0] != application_id
#         ]
#
#         # Обновляем список заявок
#         state['applications'] = new_applications
#
#         # Если текущая заявка была удалена, корректируем индекс
#         if state.get('current_index') >= len(new_applications):
#             state['current_index'] = max(0, len(new_applications) - 1)
#
#     def move_application_to_end(self, user_id: int, application_id: int):
#         """Перемещает заявку в конец очереди """
#         if user_id not in self.user_states:
#             return
#
#         state = self.user_states[user_id]
#         applications = state['applications']
#
#         # Находим заявку
#         target_application = None
#         new_applications = []
#
#         for app in applications:
#             if app[0] == application_id:
#                 target_application = app
#             else:
#                 new_applications.append(app)
#
#         # Если нашли заявку, добавляем ее в конец
#         if target_application:
#             new_applications.append(target_application)
#
#             # Обновляем список заявок
#             state['applications'] = new_applications
#
#             # Корректируем текущий индекс
#             # Текущая заявка будет удалена из сообщения,
#             # поэтому показываем следующую по порядку
#             # Индекс не меняем, так как список сдвинулся
#             if state.get('current_index') >= len(new_applications):
#                 state['current_index'] = len(new_applications) - 1
#
#     def get_studio_name(self, studio_id: int) -> str:
#         """Получает название студии по ID"""
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#                 cursor.execute(
#                     "SELECT name FROM studios WHERE studio_id = ?",
#                     (studio_id,)
#                 )
#                 result = cursor.fetchone()
#                 return result[0] if result else "Неизвестная студия"
#         except Exception as e:
#             logger.error(f"Error getting studio name: {e}")
#             return "Неизвестная студия"
#
#     def get_statistics(self, studio_id: int) -> Dict[str, Any]:
#         """Получает отчет по заявкам студии"""
#         try:
#             with self.get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 cursor.execute("""
#                     SELECT
#                         COUNT(*) as total,
#                         SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
#                         SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
#                         SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
#                     FROM applications
#                     WHERE studio_id = ?
#                 """, (studio_id,))
#
#                 stats = cursor.fetchone()
#
#                 # Статистика по дням (последние 7 дней)
#                 cursor.execute("""
#                     SELECT
#                         DATE(created_at) as date,
#                         COUNT(*) as count
#                     FROM applications
#                     WHERE studio_id = ?
#                     AND created_at >= DATE('now', '-7 days')
#                     GROUP BY DATE(created_at)
#                     ORDER BY date DESC
#                 """, (studio_id,))
#
#                 daily_stats = cursor.fetchall()
#
#
#
#         except Exception as e:
#             logger.error(f"Error getting statistics for studio {studio_id}: {e}")
#             return {}
#
#     def format_statistics_message(self, stats: Dict[str, Any], studio_name: str) -> str:
#         """Форматирует сообщение с отчетом"""
#         if not stats:
#             return "❌ Не удалось получить отчет"
#
#         message = f"<b>отчет по заявкам студии '{studio_name}'</b>\n\n"
#
#         message += f"<b>Общая статистика:</b>\n"
#         message += f"📋 Всего заявок: {stats.get('total', 0)}\n"
#         message += f"⏳ Ожидают рассмотрения: {stats.get('pending', 0)}\n"
#         message += f"✅ Принято: {stats.get('accepted', 0)}\n"
#         message += f"❌ Отклонено: {stats.get('rejected', 0)}\n\n"
#
#         if stats.get('daily'):
#             message += "<b>За последние 7 дней:</b>\n"
#             for date, count in stats['daily'][:7]:
#                 message += f"{date}: {count} заявок\n"
#             message += "\n"
#
#         return message