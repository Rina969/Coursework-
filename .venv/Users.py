import telebot
from telebot import types
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from .сборщик_анкет import QuestionnaireBuilder
from .вопросы import get_question_obj

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")
DB_PATH = "student_studios_bot (1).db"

def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_active_studios() -> List[Tuple[int, str]]:
    """Загрузка списка активных студий"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT studio_id, name FROM studios WHERE is_active = 1 ORDER BY studio_id")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error loading studios: {e}")
        return []

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Каталог студий')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Мои заявки')
    btn3 = types.KeyboardButton('Подать заявку')
    markup.row(btn2, btn3)

    bot.send_message(message.chat.id,
                     f'<em>Привет, в этом боте ты можешь узнать про творческие студии'
                     f' ГУАП и стать частью активной студенческой жизни!</em>', parse_mode='html', reply_markup=markup)

# ВЕТКА КАТАЛОГ СТУДИЙ

@bot.message_handler(func=lambda message: message.text == 'Каталог студий')
def inline_button_catalog(message):
    studios = load_active_studios()
    
    if not studios:
        bot.send_message(message.chat.id, 'На данный момент активных студий нет.')
        return
    
    markup = types.InlineKeyboardMarkup()
    for studio_id, name in studios:
        btn = types.InlineKeyboardButton(name, callback_data=f'info:{studio_id}')
        markup.row(btn)

    bot.send_message(message.chat.id, 'Нажми на студию для просмотра:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('info:'))
def show_studio_info(call):
    """Показывает информацию о студии"""
    studio_id = int(call.data.split(':')[1])
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, description, contacts 
                FROM studios 
                WHERE studio_id = ?
            """, (studio_id,))
            result = cursor.fetchone()
            
            if result:
                name, description, contacts = result
                text = f"<b>{name}</b>\n\n{description or 'Описание скоро появится.'}\n\n<b>Контакты:</b> {contacts or '—'}"
                
                # Добавляем кнопку подачи заявки
                markup = types.InlineKeyboardMarkup()
                btn_apply = types.InlineKeyboardButton("📝 Подать заявку", callback_data=f'apply:{studio_id}')
                markup.row(btn_apply)
                
                bot.send_message(call.message.chat.id, text, parse_mode='html', reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, "Студия не найдена")
    except Exception as e:
        logger.error(f"Error showing studio info: {e}")
        bot.answer_callback_query(call.id, "Ошибка при загрузке информации")


class QuestionnaireHandler:
    """Обработчик анкет с автозаполнением"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def start_questionnaire(self, update: Update, context: CallbackContext) -> int:
        """Начало анкеты для выбранной студии"""
        query = update.callback_query
        query.answer()
        
        # Получаем ID студии из cтадии выбора студии
        studio_id = int(query.data.split('_')[-1])
        
        # Сохраняем данные в контексте
        context.user_data['studio_id'] = studio_id
        context.user_data['questionnaire'] = QuestionnaireBuilder.get_questionnaire_for_studio(studio_id)
        context.user_data['current_question_index'] = 0
        context.user_data['answers'] = {}
        
        # Получаем данные пользователя для автозаполнения
        user_id = update.effective_user.id
        user_data = self.get_user_data(user_id)
        context.user_data['user_data'] = user_data
        
        # Проверяем возможность автозаполнения
        if QuestionnaireBuilder.can_autofill(studio_id, user_data):
            return self.offer_autofill(update, context, studio_id, user_data)
        else:
            return self.start_manual_filling(update, context, studio_id)
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Получает данные пользователя из БД для автозаполнения"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT full_name, student_group, phone, email 
                FROM users 
                WHERE telegram_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'full_name': result[0] or '',
                    'student_group': result[1] or '',
                    'phone': result[2] or '',
                    'email': result[3] or ''
                }
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
        
        return {}
    
    def offer_autofill(self, update: Update, context: CallbackContext, 
                      studio_id: int, user_data: Dict[str, Any]) -> int:
        """Предлагает автозаполнение"""
        query = update.callback_query
        
        # Получаем поля для автозаполнения
        autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)
        autofill_info = []
        
        for field in autofill_fields:
            value = user_data.get(field, '')
            if value:
                field_name = {
                    'full_name': 'ФИО',
                    'student_group': 'Группа',
                    'phone': 'Телефон',
                    'email': 'Email'
                }.get(field, field)
                autofill_info.append(f"{field_name}: {value}")
        
        message = (
            f"Хотите использовать основную информацию из предыдущих анкет для автозаполнения?"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Использовать мои данные", callback_data='use_autofill'),
                InlineKeyboardButton("✏️ Заполнить вручную", callback_data='manual_fill')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        return 1  # Состояние ожидания выбора
    
    def handle_autofill_choice(self, update: Update, context: CallbackContext) -> int:
        """Обработка выбора автозаполнения"""
        query = update.callback_query
        query.answer()
        
        studio_id = context.user_data['studio_id']
        user_data = context.user_data['user_data']
        answers = context.user_data['answers']
        
        if query.data == 'use_autofill':
            # Автозаполняем данные
            autofill_fields = QuestionnaireBuilder.get_autofill_fields(studio_id)
            
            for field in autofill_fields:
                value = user_data.get(field)
                if value:
                    # Находим ID вопроса, соответствующего этому полю
                    questions = QuestionnaireBuilder.get_question_objects(studio_id)
                    for q in questions:
                        if q.autofill_field == field:
                            answers[q.id] = value
                            break
            
            query.edit_message_text(
                "✅ Данные автозаполнены.\n"
                "Продолжаем с оставшимися вопросами..."
            )
        
        # Начинаем опрос с первого незаполненного вопроса
        return self.ask_next_question(update, context)
    
    def start_manual_filling(self, update: Update, context: CallbackContext, 
                            studio_id: int) -> int:
        """Начинает ручное заполнение анкеты"""
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                f"Начинаем заполнение анкеты для студии *{studio_name}*.\n\n"
                "Пожалуйста, ответьте на несколько вопросов:",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(
                f"Начинаем заполнение анкеты для студии *{studio_name}*.\n\n"
                "Пожалуйста, ответьте на несколько вопросов:",
                parse_mode='Markdown'
            )
        
        return self.ask_next_question(update, context)
    
    def ask_next_question(self, update: Update, context: CallbackContext) -> int:
        """Задает следующий вопрос"""
        studio_id = context.user_data['studio_id']
        question_ids = QuestionnaireBuilder.get_question_sequence(studio_id)
        current_index = context.user_data['current_question_index']
        answers = context.user_data['answers']
        
        # Пропускаем уже заполненные вопросы (при автозаполнении)
        while current_index < len(question_ids):
            qid = question_ids[current_index]
            if qid not in answers:
                break
            current_index += 1
        
        # Проверяем, не заполнили ли мы все вопросы
        if current_index >= len(question_ids):
            return self.show_summary(update, context)
        
        # Сохраняем текущий индекс
        context.user_data['current_question_index'] = current_index
        context.user_data['current_question_id'] = qid
        
        # Получаем и вызываем обработчик вопроса
        handler = QuestionnaireBuilder.build_questionnaire_handlers(studio_id)[current_index]
        
        if update.callback_query:
            # Если это callback, отправляем новое сообщение
            update.callback_query.message.reply_text("Следующий вопрос:")
            handler(update, context)
        else:
            handler(update, context)
        
        # Возвращаем состояние для обработки ответа
        return current_index + 100  # Уникальное состояние для каждого вопроса
    
    def process_answer(self, update: Update, context: CallbackContext) -> int:
        """Обработка ответа на вопрос"""
        current_qid = context.user_data.get('current_question_id')
        answer_text = update.message.text.strip()
        
        # Для вопросов с inline-кнопками
        if update.callback_query:
            answer_text = update.callback_query.data
            if answer_text.startswith('activeness_'):
                answer_text = 'Да' if answer_text.endswith('yes') else 'Нет'
        
        # Получаем объект вопроса для валидации
        q_obj = get_question_obj(current_qid)
        
        if q_obj:
            is_valid, error_msg = q_obj.validate(answer_text)
            if not is_valid:
                update.message.reply_text(f"❌ {error_msg}\n\nПопробуйте еще раз:")
                return context.user_data['current_question_index'] + 100
        
        # Сохраняем ответ
        context.user_data['answers'][current_qid] = answer_text
        
        # Переходим к следующему вопросу
        context.user_data['current_question_index'] += 1
        
        return self.ask_next_question(update, context)
    
    def show_summary(self, update: Update, context: CallbackContext) -> int:
        """Показывает сводку по ответам"""
        studio_id = context.user_data['studio_id']
        answers = context.user_data['answers']
        
        # Валидируем ответы
        is_valid, errors = QuestionnaireBuilder.validate_answers(studio_id, answers)
        
        if not is_valid:
            error_text = "❌ *Ошибки в заполнении:*\n\n"
            for qid, error in errors.items():
                q_obj = get_question_obj(qid)
                error_text += f"• {q_obj.text}: {error}\n"
            
            error_text += "\nПожалуйста, заполните анкету заново."
            
            update.message.reply_text(error_text, parse_mode='Markdown')
            context.user_data['current_question_index'] = 0
            context.user_data['answers'] = {}
            return self.ask_next_question(update, context)
        


        # Генерируем сводку
        summary = QuestionnaireBuilder.generate_summary(studio_id, answers)
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить и отправить", 
                                   callback_data='confirm_application'),
                InlineKeyboardButton("✏️ Заполнить заново", 
                                   callback_data='restart_questionnaire')
            ],
            [
                InlineKeyboardButton("🚫 Отменить и вернуться в каталог", 
                                   callback_data='cancel_to_catalog')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                f"{summary}\n\n"
                f"*Всё верно? Подтвердите отправку заявки или внесите изменения.*",
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(
                f"{summary}\n\n"
                f"*Всё верно? Подтвердите отправку заявки или внесите изменения.*",
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        
        return 'CONFIRMATION_STATE'
    
    def handle_confirmation_action(self, update: Update, context: CallbackContext) -> int:
        """Обработка действий на этапе подтверждения"""
        query = update.callback_query
        query.answer()
        
        action = query.data
        
        if action == 'confirm_application':
            return self.confirm_application(update, context)
        
        elif action == 'restart_questionnaire':
            return self.restart_questionnaire(update, context)
        
        elif action == 'cancel_to_catalog':
            return self.cancel_to_catalog(update, context)
        
        return 'CONFIRMATION_STATE'
    
    def confirm_application(self, update: Update, context: CallbackContext) -> int:
        """Подтверждение и сохранение анкеты в БД"""
        query = update.callback_query
        
        studio_id = context.user_data['studio_id']
        user_id = update.effective_user.id
        answers = context.user_data['answers']
        user_data = context.user_data.get('user_data', {})
        
        # Сохраняем анкету в БД
        success, application_id = self.save_application_to_db(
            user_id=user_id,
            studio_id=studio_id,
            answers=answers,
            user_data=user_data
        )
        
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        
        if success:
            # Создаем клавиатуру с кнопкой "Главное меню"
            keyboard = [
                [InlineKeyboardButton("🏠 Главное меню", callback_data='go_to_main_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            success_message = (
                f"✅ Ваша заявка в студию *{studio_name}* отправлена.\n"
            )
            
            query.edit_message_text(
                success_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Очищаем данные анкеты, но сохраняем studio_id для возможного повторного заполнения
            context.user_data.pop('answers', None)
            context.user_data.pop('current_question_index', None)
            context.user_data.pop('current_question_id', None)
            
            return 'AFTER_CONFIRMATION'
            
        else:
            # В случае ошибки
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", 
                                    callback_data='retry_save_application')],
                [InlineKeyboardButton("🚫 Отменить", callback_data='cancel_to_catalog')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            error_message = (
                f"Не удалось сохранить заявку в студию *{studio_name}*.\n"
            )
            
            query.edit_message_text(
                error_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return 'CONFIRMATION_STATE'
    
    def restart_questionnaire(self, update: Update, context: CallbackContext) -> int:
        """Перезапуск заполнения анкеты"""
        query = update.callback_query
        
        studio_id = context.user_data['studio_id']
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        
        # Полностью сбрасываем данные анкеты
        context.user_data['answers'] = {}
        context.user_data['current_question_index'] = 0
        context.user_data.pop('current_question_id', None)
        
        return self.start_manual_filling(update, context, studio_id)

    def cancel_to_catalog(self, update: Update, context: CallbackContext) -> int:
        """Отмена анкеты и возврат в каталог студий"""
         query = update.callback_query
        
        studio_id = context.user_data['studio_id']
        studio_name = QuestionnaireBuilder.get_studio_name(studio_id)
        
        # Полностью сбрасываем данные анкеты
        context.user_data['answers'] = {}
        context.user_data['current_question_index'] = 0
        context.user_data.pop('current_question_id', None)
        
        return self.inline_button_catalog(message)


