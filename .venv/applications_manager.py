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

    def get_user_applications(self, telegram_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Находим user_id по telegram_id
            cursor.execute("SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,))
            user_result = cursor.fetchone()

            if not user_result:
                print(f"Пользователь с telegram_id {telegram_id} не найден!")
                return []

            user_id = user_result[0]

            # 2. Ищем заявки по user_id
            cursor.execute("""
                SELECT application_id, studio_id, status, created_at
                FROM applications 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))

            rows = cursor.fetchall()
            print(f"Найдено заявок для пользователя с telegram_id {telegram_id} (user_id={user_id}): {len(rows)}")

            applications = []

            for row in rows:
                studio_name = f"Студия #{row[1]}"
                try:
                    cursor.execute("SELECT name FROM studios WHERE studio_id = ?", (row[1],))
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
            import traceback
            traceback.print_exc()
            return []
        finally:
            conn.close()

    def show_user_applications(self, chat_id: int, user_id: int):
        applications = self.get_user_applications(user_id)

        if not applications:
            self.bot.send_message(
                chat_id,
                "У вас пока нет заявок",
                reply_markup=markup
            )
            return

        message = "<b>Ваши заявки:</b>\n\n"

        for i, app in enumerate(applications, 1):
            try:
                created_str = app['created_at']

                if ' ' in created_str:
                    date_part, time_part = created_str.split(' ')
                    time_without_seconds = ':'.join(time_part.split(':')[:2])
                    date_str = f"{date_part} {time_without_seconds}"
                else:
                    date_str = created_str

            except Exception as e:
                print(f"Ошибка форматирования даты {app['created_at']}: {e}")
                date_str = app['created_at']

            status_text = {
                'pending': '⏳ На рассмотрении',
                'approved': '✅ Принята',
                'rejected': '❌ Отклонена'
            }.get(app['status'], app['status'])

            message += f"<b>{i}. {app['studio_name']}</b>\n"
            message += f"Статус заявки:   {status_text}\n"
            message += f"Дата создания: {date_str}\n\n"

        self.bot.send_message(
            chat_id,
            message,
            parse_mode='HTML',
        )

    def cleanup_old_applications(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            week_ago = datetime.now() - timedelta(days=7)
            week_ago_str = week_ago.strftime('%Y-%m-%d %H:%M:')

            cursor.execute("""
                DELETE FROM applications 
                WHERE status IN ('approved', 'rejected') AND updated_at < ?
            """, (week_ago_str,))

            conn.commit()
        except:
            conn.rollback()
        finally:
            conn.close()