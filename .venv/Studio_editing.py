import sqlite3
from typing import Dict, Any
import logging
from telebot import types

logger = logging.getLogger(__name__)

def handle_edit_field_selection(message, bot, user_edit_states, create_edit_menu_markup):
    """Обработка выбора поля для редактирования"""
    user_id = message.from_user.id

    if user_id not in user_edit_states:
        bot.send_message(message.chat.id, "❌ Сессия редактирования не активна")
        return

    edit_state = user_edit_states[user_id]

    # Определяем какое поле редактируем
    field_map = {
        'Изменить название': ('name', 'введите новое название студии'),
        'Изменить описание': ('description', 'введите новое описание студии'),
        'Изменить контакты': ('contacts', 'введите новые контакты (телефон, email, соцсети)')
    }

    field_name, prompt = field_map[message.text]
    edit_state['awaiting_input'] = field_name

    # Сохраняем текущий текст для возможной отмены
    if field_name not in edit_state['changes']:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {field_name} FROM studios WHERE id = ?",
                       (edit_state['studio_id'],))
        result = cursor.fetchone()
        conn.close()
        if result:
            current_value = result[0]
            edit_state['changes'][f'old_{field_name}'] = current_value

    bot.send_message(
        message.chat.id,
        f"✏️ <b>Редактирование {field_name}</b>\n\n"
        f"Пожалуйста, {prompt}:\n\n"
        "<i>Для отмены ввода отправьте 'отмена'</i>",
        parse_mode='HTML'
    )


def handle_field_input(message, bot, user_edit_states, create_edit_menu_markup):
    """Обработка ввода нового значения для поля"""
    user_id = message.from_user.id

    if user_id not in user_edit_states:
        return

    edit_state = user_edit_states[user_id]
    field_name = edit_state.get('awaiting_input')

    if not field_name:
        return

    # Проверяем отмену
    if message.text.lower() == 'отмена':
        if f'old_{field_name}' in edit_state['changes']:
            # Восстанавливаем старое значение
            old_value = edit_state['changes'][f'old_{field_name}']
            edit_state['changes'][field_name] = old_value
            del edit_state['changes'][f'old_{field_name}']

        edit_state['awaiting_input'] = None

        bot.send_message(
            message.chat.id,
            "⏪ <b>Ввод отменен</b>",
            parse_mode='HTML',
            reply_markup=create_edit_menu_markup()
        )
        return

    # Сохраняем новое значение
    edit_state['changes'][field_name] = message.text
    edit_state['awaiting_input'] = None

    # Подтверждаем ввод
    confirmation_text = {
        'name': 'Название',
        'description': 'Описание',
        'contacts': 'Контакты'
    }

    bot.send_message(
        message.chat.id,
        f"✅ <b>{confirmation_text.get(field_name, 'Поле')} обновлено</b>\n\n"
        f"Новое значение сохранено в черновике.\n\n"
        f"<i>Продолжайте редактирование или нажмите 'Сохранить все изменения'</i>",
        parse_mode='HTML',
        reply_markup=create_edit_menu_markup()
    )

    # Показываем предпросмотр
    show_preview(message.chat.id, user_id, bot, user_edit_states)


def show_preview(chat_id: int, user_id: int, bot, user_edit_states):
    """Показывает предпросмотр изменений"""
    if user_id not in user_edit_states:
        return

    edit_state = user_edit_states[user_id]
    studio_id = edit_state['studio_id']

    # Получаем текущие данные
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, contacts FROM studios WHERE id = ?", (studio_id,))
    current_data = cursor.fetchone()
    conn.close()

    if not current_data:
        return

    current_name, current_description, current_contacts = current_data

    # Применяем изменения из черновика
    preview_name = edit_state['changes'].get('name', current_name)
    preview_description = edit_state['changes'].get('description', current_description)
    preview_contacts = edit_state['changes'].get('contacts', current_contacts)

    message = (
        "<b>Предпросмотр изменений:</b>\n\n"
        f"<b>Название:</b> {preview_name if preview_name else '❌ Не указано'}\n"
        f"<b>Описание:</b>\n{preview_description if preview_description else '❌ Не указано'}\n"
        f"<b>Контакты:</b>\n{preview_contacts if preview_contacts else '❌ Не указаны'}\n\n"
        f"<i>Изменено полей: {len([k for k in edit_state['changes'].keys() if not k.startswith('old_')])}</i>"
    )

    bot.send_message(chat_id, message, parse_mode='HTML')


def handle_save_all_changes(message, bot, user_edit_states, create_main_menu_markup):
    """Сохранение всех изменений в БД"""
    user_id = message.from_user.id

    if user_id not in user_edit_states:
        bot.send_message(message.chat.id, "❌ Нет изменений для сохранения")
        return

    edit_state = user_edit_states[user_id]

    # Фильтруем только настоящие изменения (не старые значения)
    real_changes = {k: v for k, v in edit_state['changes'].items() if not k.startswith('old_')}

    if not real_changes:
        bot.send_message(message.chat.id, "❌ Нет изменений для сохранения")
        return

    # Сохраняем изменения в БД
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Формируем SQL запрос
        set_clauses = []
        params = []

        for field, value in real_changes.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        params.append(edit_state['studio_id'])

        update_query = f"""
            UPDATE studios 
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """

        cursor.execute(update_query, params)
        conn.commit()

        # Логируем изменения
        logger.info(f"Студия {edit_state['studio_id']} обновлена пользователем {user_id}")

        bot.send_message(
            message.chat.id,
            "✅ <b>Все изменения сохранены!</b>",
            parse_mode='HTML',
            reply_markup=create_main_menu_markup(user_id)
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка при сохранении изменений студии: {e}")
        bot.send_message(
            message.chat.id,
            f"❌ <b>Ошибка при сохранении:</b>\n{str(e)}",
            parse_mode='HTML'
        )
    finally:
        conn.close()

    # Очищаем состояние редактирования
    del user_edit_states[user_id]


def handle_edit_cancel(message, bot, user_edit_states, create_main_menu_markup):
    """Отмена редактирования"""
    user_id = message.from_user.id

    if user_id in user_edit_states:
        del user_edit_states[user_id]

    bot.send_message(
        message.chat.id,
        "❌ <b>Редактирование отменено</b>",
        parse_mode='HTML',
        reply_markup=create_main_menu_markup(user_id)
    )