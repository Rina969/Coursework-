import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_connection(db_path: str = "student_studios_bot (1).db") -> sqlite3.Connection:
    """Возвращает соединение с БД"""
    return sqlite3.connect(db_path, check_same_thread=False)

def get_user_role(username: str) -> str:
    """Получение роли пользователя из базы данных"""
    if not username:
        return 'student'

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username = ?", (f"@{username}",))
            result = cursor.fetchone()
            return result[0] if result else 'student'
    except Exception as e:
        logger.error(f"Database error getting role: {e}")
        return 'student'

def get_studio_id_for_head(user_id: int) -> Optional[int]:
    """Получает ID студии, за которой закреплен руководитель"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT studio_id FROM studios WHERE head_user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting studio for head {user_id}: {e}")
        return None