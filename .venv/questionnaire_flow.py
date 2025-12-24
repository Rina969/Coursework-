import telebot
from telebot import types
from typing import Dict, Any
import logging
<<<<<<< HEAD
from datetime import datetime

from users_collector import QuestionnaireBuilder
=======

from users_collector import QuestionnaireBuilder  # Этот импорт должен быть
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
from questions import get_question_obj
from database import save_application_to_db

logger = logging.getLogger(__name__)


class QuestionnaireFlow:
    """Управление процессом заполнения анкеты"""

    def __init__(self, bot):
        self.bot = bot
        self.user_states = {}

    def start_questionnaire(self, call, studio_id: int):
        """Начало анкеты для выбранной студии"""
        user_id = call.from_user.id

        studio_config = QuestionnaireBuilder.get_questionnaire_for_studio(studio_id)
        if not studio_config:
            self.bot.answer_callback_query(call.id, "Анкета для этой студии не настроена")
            return False

        self.user_states[user_id] = {
            'state': 'questionnaire',
            'studio_id': studio_id,
            'studio_name': studio_config.get('name', 'Студия'),
            'current_question_index': 0,
            'answers': {},
            'questionnaire': studio_config
        }

        # Получаем данные пользователя для автозаполнения
        user_data = self._get_user_data(user_id)
        self.user_states[user_id]['user_data'] = user_data

        if QuestionnaireBuilder.can_autofill(studio_id, user_data):
            self._offer_autofill(call, studio_id, user_data)
        else:
            self._start_manual_filling(call, studio_id)
        return True

    def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получает данные пользователя из БД"""
        from database import get_user_by_telegram_id
        user = get_user_by_telegram_id(user_id)
<<<<<<< HEAD
=======

        if user:
            logger.info(f"Найдены данные пользователя {user_id}: {user}")
        else:
            logger.info(f"Данные пользователя {user_id} не найдены в БД")

>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
        return user if user else {}

    def _offer_autofill(self, call, studio_id: int, user_data: Dict[str, Any]):
        """Предлагает автозаполнение"""
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)
        autofill_info = []

<<<<<<< HEAD
        for field in autofill_fields:
            value = user_data.get(field, '')
            if value:
=======
        # Логируем для отладки
        logger.info(f"Поля для автозаполнения: {autofill_fields}")
        logger.info(f"Данные пользователя: {user_data}")

        for field in autofill_fields:
            value = user_data.get(field, '')
            logger.info(f"Поле {field}: значение '{value}', тип {type(value)}")
            if value and str(value).strip():
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
                field_name = {
                    'full_name': 'ФИО',
                    'student_group': 'Группа',
                    'phone_number': 'Телефон',
                    'email': 'Email'
                }.get(field, field)
                autofill_info.append(f"{field_name}: {value}")

        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        message = f"*Анкета для студии: {studio_name}*\n\n"

        if autofill_info:
            message += "Найдены ваши данные из предыдущих анкет:\n"
            for info in autofill_info:
                message += f"• {info}\n"
            message += "\nХотите использовать их для автозаполнения?"
        else:
<<<<<<< HEAD
            message += "Хотите использовать основную информацию для автозаполнения?"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Использовать мои данные", callback_data='use_autofill'),
            types.InlineKeyboardButton("Заполнить вручную", callback_data='manual_fill')
        )
=======
            message += "К сожалению, данных для автозаполнения не найдено.\nХотите заполнить анкету вручную?"

        markup = types.InlineKeyboardMarkup()
        if autofill_info:
            markup.row(
                types.InlineKeyboardButton("Использовать мои данные", callback_data='use_autofill'),
                types.InlineKeyboardButton("Заполнить вручную", callback_data='manual_fill')
            )
        else:
            markup.row(
                types.InlineKeyboardButton("Заполнить вручную", callback_data='manual_fill')
            )
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c

        self.bot.edit_message_text(
            message,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )

    def _start_manual_filling(self, call, studio_id: int):
        """Начинает ручное заполнение анкеты"""
        user_id = call.from_user.id
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)

        self.user_states[user_id]['state'] = 'answering'

        self.bot.edit_message_text(
            f"Начинаем заполнение анкеты для студии *{studio_name}*.\n\n"
            f"Пожалуйста, ответьте на несколько вопросов:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )

        self._ask_next_question(call.message.chat.id, user_id)

    def _ask_next_question(self, chat_id: int, user_id: int):
        """Задает следующий вопрос"""
        if user_id not in self.user_states:
            return

        state = self.user_states[user_id]
<<<<<<< HEAD
        studio_id = state['studio_id']
        question_ids = QuestionnaireBuilder.get_question_sequence(studio_id)
        current_index = state.get('current_question_index', 0)

=======
        question_ids = state['questionnaire'].get('questions', [])
        current_index = state.get('current_question_index', 0)

        # Пропускаем уже заполненные вопросы
        while current_index < len(question_ids):
            qid = question_ids[current_index]
            # Если вопрос уже заполнен (например, через автозаполнение), пропускаем его
            if qid in state['answers']:
                logger.info(f"Вопрос {qid} уже заполнен, пропускаем")
                current_index += 1
                state['current_question_index'] = current_index
            else:
                break

>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
        # Проверяем, не заполнили ли мы все вопросы
        if current_index >= len(question_ids):
            self._show_summary(chat_id, user_id)
            return

        # Получаем текущий вопрос
        qid = question_ids[current_index]
        q_obj = get_question_obj(qid)

        if not q_obj:
            # Пропускаем несуществующий вопрос
            state['current_question_index'] += 1
            self._ask_next_question(chat_id, user_id)
            return

        # Сохраняем текущий вопрос
        state['current_question_id'] = qid

<<<<<<< HEAD
        # Отправляем вопрос
        if q_obj.type == 'select' and q_obj.options:
            # Для вопросов с выбором создаем клавиатуру
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for option in q_obj.options:
                markup.add(types.KeyboardButton(option))
            self.bot.send_message(chat_id, q_obj.text, reply_markup=markup)
=======
        logger.info(f"Задаем вопрос {qid}, тип: {q_obj.type}")

        # Проверяем, может быть вопрос уже заполнен автозаполнением?
        if qid in state['answers']:
            logger.info(f"Вопрос {qid} уже имеет ответ: {state['answers'][qid]}")
            state['current_question_index'] += 1
            self._ask_next_question(chat_id, user_id)
            return

        # Отправляем вопрос с нужным типом клавиатуры
        if q_obj.type == 'select' and q_obj.options:
            # Для вопросов с выбором создаем INLINE клавиатуру
            markup = types.InlineKeyboardMarkup(row_width=1)
            for option in q_obj.options:
                markup.add(types.InlineKeyboardButton(
                    option,
                    callback_data=f"select_answer:{qid}:{option}"
                ))

            self.bot.send_message(
                chat_id,
                q_obj.text,
                reply_markup=markup
            )

        elif q_obj.type == 'boolean':
            # Для boolean вопросов используем reply-клавиатуру
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Да", "Нет")

            self.bot.send_message(
                chat_id,
                q_obj.text,
                reply_markup=markup
            )

>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
        else:
            # Для обычных вопросов без клавиатуры
            self.bot.send_message(chat_id, q_obj.text)

    def process_answer(self, message):
<<<<<<< HEAD
        """Обработка ответа на вопрос"""
=======
        """Обработка текстового ответа на вопрос"""
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
        user_id = message.from_user.id

        if user_id not in self.user_states:
            return

        state = self.user_states[user_id]
        if state.get('state') != 'answering':
            return

        current_qid = state.get('current_question_id')
        answer_text = message.text.strip()

        if not current_qid:
            return

        # Получаем объект вопроса для валидации
        q_obj = get_question_obj(current_qid)

<<<<<<< HEAD
=======
        # Проверяем тип вопроса - если это select, то обрабатывается через callback
        if q_obj and q_obj.type == 'select':
            return  # Пропускаем, select обрабатывается через callback

>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
        if q_obj:
            is_valid, error_msg = q_obj.validate(answer_text)
            if not is_valid:
                self.bot.send_message(message.chat.id, f"❌ {error_msg}\n\nПопробуйте еще раз:")
                return

        # Сохраняем ответ
        state['answers'][current_qid] = answer_text

        # Увеличиваем индекс и задаем следующий вопрос
        state['current_question_index'] += 1

<<<<<<< HEAD
        # Убираем клавиатуру для следующего вопроса
        remove_markup = types.ReplyKeyboardRemove()
        self.bot.send_message(message.chat.id, "Отлично! Следующий вопрос:", reply_markup=remove_markup)

        self._ask_next_question(message.chat.id, user_id)
=======
        # Отправляем подтверждение для вопросов с reply-клавиатурой
        if q_obj and q_obj.type == 'boolean':
            # Сначала отправляем подтверждение с текстом
            self.bot.send_message(
                message.chat.id,
                f"✅ Ответ принят: {answer_text}",
                reply_markup=types.ReplyKeyboardRemove()
            )

        self._ask_next_question(message.chat.id, user_id)

    def process_select_answer(self, call):
        """Обработка выбора из inline-клавиатуры для select вопросов"""
        user_id = call.from_user.id

        if user_id not in self.user_states:
            self.bot.answer_callback_query(call.id, "Сессия устарела")
            return

        state = self.user_states[user_id]
        if state.get('state') != 'answering':
            self.bot.answer_callback_query(call.id, "Неверное состояние")
            return

        # Разбираем callback_data: "select_answer:question_id:selected_option"
        parts = call.data.split(':')
        if len(parts) != 3:
            self.bot.answer_callback_query(call.id, "Ошибка данных")
            return

        qid = parts[1]
        selected_option = parts[2]

        # Проверяем, что это текущий вопрос
        current_qid = state.get('current_question_id')
        if qid != current_qid:
            self.bot.answer_callback_query(call.id, "Неверный вопрос")
            return

        # Сохраняем ответ
        state['answers'][qid] = selected_option

        # Увеличиваем индекс вопроса
        state['current_question_index'] += 1

        # Удаляем inline-клавиатуру и показываем выбранный вариант
        self.bot.edit_message_text(
            f"❓ {get_question_obj(qid).text if get_question_obj(qid) else 'Вопрос'}\n"
            f"✅ Вы выбрали: {selected_option}",
            call.message.chat.id,
            call.message.message_id
        )

        # Задаем следующий вопрос
        self._ask_next_question(call.message.chat.id, user_id)

    def _show_summary(self, chat_id: int, user_id: int):
        """Показывает сводку по заполненной анкете"""
        if user_id not in self.user_states:
            return

        state = self.user_states[user_id]
        studio_id = state['studio_id']
        answers = state['answers']

        # Генерируем сводку
        summary = "📋 *Сводка вашей заявки*\n\n"

        for qid, answer in answers.items():
            q_obj = get_question_obj(qid)
            question_text = q_obj.text if q_obj else qid
            summary += f"*{question_text}*\n"
            summary += f"{answer}\n\n"

        # Отправляем сводку пользователю
        self.bot.send_message(
            chat_id,
            summary,
            parse_mode='Markdown'
        )

        # Подтверждение отправки
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ Отправить заявку", callback_data='confirm_application'),
            types.InlineKeyboardButton("✏️ Заполнить заново", callback_data='restart_questionnaire')
        )

        self.bot.send_message(
            chat_id,
            "Проверьте информацию выше. Все верно?",
            reply_markup=markup
        )

        state['state'] = 'reviewing'

    def _confirm_application(self, call):
        """Подтверждение и сохранение заявки"""
        user_id = call.from_user.id

        if user_id not in self.user_states:
            self.bot.answer_callback_query(call.id, "Сессия устарела")
            return

        state = self.user_states[user_id]

        # Сохраняем заявку в БД
        application_id = save_application_to_db(
            telegram_id=user_id,
            studio_id=state['studio_id'],
            answers=state['answers'],
            user_first_name=call.from_user.first_name,
            user_last_name=call.from_user.last_name
        )

        if application_id:
            # Удаляем состояние пользователя
            if user_id in self.user_states:
                del self.user_states[user_id]

            # Сообщаем об успехе
            self.bot.edit_message_text(
                "✅ *Ваша заявка успешно отправлена!*\n\n"
                f"Номер заявки: #{application_id}\n"
                "С вами свяжутся в ближайшее время.",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )

            # Показываем главное меню
            self._show_main_menu(call.message.chat.id, call.from_user)
        else:
            self.bot.edit_message_text(
                "❌ Произошла ошибка при сохранении заявки. Попробуйте позже.",
                call.message.chat.id,
                call.message.message_id
            )

    def _restart_questionnaire(self, call):
        """Перезапуск заполнения анкеты"""
        user_id = call.from_user.id
        if user_id in self.user_states:
            state = self.user_states[user_id]
            studio_id = state['studio_id']

            # Начинаем заново
            self.start_questionnaire(call, studio_id)

    def _show_main_menu(self, chat_id: int, user):
        """Показывает главное меню"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Каталог студий')
        markup.row(btn1)
        btn2 = types.KeyboardButton('Мои заявки')
        btn3 = types.KeyboardButton('Подать заявку')
        markup.row(btn2, btn3)

        self.bot.send_message(
            chat_id,
            '<em>Главное меню</em>',
            parse_mode='html',
            reply_markup=markup
        )
>>>>>>> 2c58de2511d2324c74225b79a43c74abe47df76c
