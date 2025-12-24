import telebot
from telebot import types
from typing import List, Tuple
import logging
from database import load_active_studios

logger = logging.getLogger(__name__)


def show_studio_catalog(bot, chat_id: int):
    """Показывает каталог студий"""
    studios = load_active_studios()

    if not studios:
        bot.send_message(chat_id, 'На данный момент активных студий нет.')
        return

    markup = types.InlineKeyboardMarkup()
    for studio_id, name in studios:
        btn = types.InlineKeyboardButton(name, callback_data=f'info:{studio_id}')
        markup.row(btn)

    bot.send_message(chat_id, 'Нажми на студию для просмотра:', reply_markup=markup)


def show_studio_info(bot, call):
    """Показывает информацию о студии"""
    studio_id = int(call.data.split(':')[1])

    try:
        from database import get_connection
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
                text = f"<b>{name}</b>\n\n{description or 'Описание скоро появится.'}"

                if contacts:
                    text += f"\n\n<b>Контакты:</b>\n{contacts}"

                markup = types.InlineKeyboardMarkup()
                btn_apply = types.InlineKeyboardButton("📝 Подать заявку", callback_data=f'apply:{studio_id}')
                markup.row(btn_apply)

                bot.edit_message_text(
                    text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='html',
                    reply_markup=markup
                )
            else:
                bot.answer_callback_query(call.id, "Студия не найдена")
    except Exception as e:
        logger.error(f"Error showing studio info: {e}")
        bot.answer_callback_query(call.id, "Ошибка при загрузке информации")