import telebot
from telebot import types
from typing import Dict, Any
import logging
from datetime import datetime

from users_collector import QuestionnaireBuilder
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
        return user if user else {}

    def _offer_autofill(self, call, studio_id: int, user_data: Dict[str, Any]):
        """Предлагает автозаполнение"""
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)
        autofill_info = []

        for field in autofill_fields:
            value = user_data.get(field, '')
            if value:
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
            message += "Хотите использовать основную информацию для автозаполнения?"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Использовать мои данные", callback_data='use_autofill'),
            types.InlineKeyboardButton("Заполнить вручную", callback_data='manual_fill')
        )

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
        studio_id = state['studio_id']
        question_ids = QuestionnaireBuilder.get_question_sequence(studio_id)
        current_index = state.get('current_question_index', 0)

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

        # Отправляем вопрос
        if q_obj.type == 'select' and q_obj.options:
            # Для вопросов с выбором создаем клавиатуру
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for option in q_obj.options:
                markup.add(types.KeyboardButton(option))
            self.bot.send_message(chat_id, q_obj.text, reply_markup=markup)
        else:
            # Для обычных вопросов без клавиатуры
            self.bot.send_message(chat_id, q_obj.text)

    def process_answer(self, message):
        """Обработка ответа на вопрос"""
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

        if q_obj:
            is_valid, error_msg = q_obj.validate(answer_text)
            if not is_valid:
                self.bot.send_message(message.chat.id, f"❌ {error_msg}\n\nПопробуйте еще раз:")
                return

        # Сохраняем ответ
        state['answers'][current_qid] = answer_text

        # Увеличиваем индекс и задаем следующий вопрос
        state['current_question_index'] += 1

        # Убираем клавиатуру для следующего вопроса
        remove_markup = types.ReplyKeyboardRemove()
        self.bot.send_message(message.chat.id, "Отлично! Следующий вопрос:", reply_markup=remove_markup)

        self._ask_next_question(message.chat.id, user_id)