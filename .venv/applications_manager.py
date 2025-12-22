import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from telebot import types


class ApplicationsManager:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "student_studios_bot (1).db"

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def get_user_applications(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Проверим, есть ли таблица applications
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
            if not cursor.fetchone():
                print("Таблица applications не существует!")
                return []

            # Проверим структуру таблицы
            cursor.execute("PRAGMA table_info(applications)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Столбцы таблицы applications: {columns}")

            # Простой запрос для проверки
            cursor.execute("""
                SELECT application_id, studio_id, status, created_at
                FROM applications 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))

            rows = cursor.fetchall()
            print(f"Найдено заявок для пользователя {user_id}: {len(rows)}")

            applications = []

            for row in rows:
                studio_name = f"Студия #{row[1]}"
                # Попробуем получить название студии
                try:
                    cursor.execute("SELECT name FROM studios WHERE id = ?", (row[1],))
                    studio_result = cursor.fetchone()
                    if studio_result:
                        studio_name = studio_result[0]
                except:
                    pass

                applications.append({
                    'id': row[0],
                    'studio_id': row[1],
                    'status': row[2],
                    'created_at': row[3],
                    'studio_name': studio_name
                })

            return applications

        except Exception as e:
            print(f"Ошибка при получении заявок: {e}")
            return []
        finally:
            conn.close()

    def show_user_applications(self, chat_id: int, user_id: int):
        applications = self.get_user_applications(user_id)

        # Главное меню должно быть после сообщения, а не как кнопка над клавиатурой
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton('Каталог студий'))
        markup.row(types.KeyboardButton('Мои заявки'))

        if not applications:
            self.bot.send_message(
                chat_id,
                "У вас пока нет заявок",
                reply_markup=markup
            )
            return

        message = "📋 <b>Ваши заявки:</b>\n\n"

        for i, app in enumerate(applications, 1):
            try:
                created_date = datetime.strptime(app['created_at'], '%Y-%m-%d %H:%M:%S')
                date_str = created_date.strftime('%d.%m.%Y %H:%M')
            except:
                date_str = app['created_at']

            status_text = {
                'pending': '⏳ На рассмотрении',
                'approved': '✅ Принята',
                'rejected': '❌ Отклонена'
            }.get(app['status'], app['status'])

            message += f"<b>{i}. {app['studio_name']}</b>\n"
            message += f"   {status_text}\n"
            message += f"   📅 {date_str}\n\n"

        self.bot.send_message(
            chat_id,
            message,
            parse_mode='HTML',
            reply_markup=markup
        )

    def cleanup_old_applications(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            week_ago = datetime.now() - timedelta(days=7)
            week_ago_str = week_ago.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                DELETE FROM applications 
                WHERE status IN ('approved', 'rejected') AND updated_at < ?
            """, (week_ago_str,))

            conn.commit()
        except:
            conn.rollback()
        finally:
            conn.close()