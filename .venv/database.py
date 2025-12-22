import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_connection(db_path: str = "student_studios_bot (1).db") -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect(db_path, check_same_thread=False)


def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получает данные пользователя по Telegram ID"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT full_name, student_group, phone_number, email
                           FROM users
                           WHERE telegram_id = ?
                           """, (telegram_id,))
            result = cursor.fetchone()

            if result:
                return {
                    'full_name': result[0] or '',
                    'student_group': result[1] or '',
                    'phone_number': result[2] or '',
                    'email': result[3] or ''
                }
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
    return None


def save_application_to_db(telegram_id: int, studio_id: int, answers: dict,
                           user_first_name: str = None, user_last_name: str = None) -> Optional[int]:
    """Сохраняет заявку в БД"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Получаем или создаем пользователя
            cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
            user_result = cursor.fetchone()

            if user_result:
                user_id = user_result[0]
            else:
                # Получаем ФИО из ответов или Telegram
                full_name = answers.get('full_name')
                if not full_name:
                    full_name = f"{user_first_name or ''} {user_last_name or ''}".strip()
                    if not full_name:
                        full_name = "Не указано"

                cursor.execute("""
                               INSERT INTO users (telegram_id, full_name, created_at)
                               VALUES (?, ?, ?)
                               """, (telegram_id, full_name, datetime.now()))
                user_id = cursor.lastrowid

            # Генерируем сводку
            from users_collector import QuestionnaireBuilder
            summary = QuestionnaireBuilder.generate_summary(studio_id, answers)

            # Сохраняем заявку
            cursor.execute("""
                           INSERT INTO applications (user_id, studio_id, summary, status, created_at)
                           VALUES (?, ?, ?, ?, ?)
                           """, (user_id, studio_id, summary, 'pending', datetime.now()))

            application_id = cursor.lastrowid

            # Сохраняем ответы на вопросы
            for question_id, answer in answers.items():
                from questions import get_question_obj
                q_obj = get_question_obj(question_id)
                question_text = q_obj.text if q_obj else question_id

                cursor.execute("""
                               INSERT INTO application_answers
                                   (application_id, question_id, question_text, answer_text)
                               VALUES (?, ?, ?, ?)
                               """, (application_id, question_id, question_text, answer))

            conn.commit()
            return application_id

    except Exception as e:
        logger.error(f"Error saving application: {e}")
        return None


def load_active_studios():
    """Загрузка списка активных студий"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT studio_id, name FROM studios WHERE is_active = 1 ORDER BY studio_id")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error loading studios: {e}")
        return []




