import telebot
from telebot import types
import logging

from auth import get_user_role
from database import load_active_studios
from questionnaire_flow import QuestionnaireFlow
from catalog import show_studio_catalog, show_studio_info
from users_collector import QuestionnaireBuilder
from questions import get_question_obj



# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot("8575877961:AAHgw2xCBZagYmj1s-LwlA-dhAcgXALxVzE")

# Инициализация компонентов
questionnaire_flow = QuestionnaireFlow(bot)

# Инициализация модуля администратора
from Admin import initialize as init_admin

init_admin(bot)


@bot.message_handler(commands=['start'])
def start(message):
    """Главный обработчик команды /start"""
    username = message.from_user.username
    role = get_user_role(username)

    if role == 'admin':
        from Admin import admin_start
        admin_start(message)
        return
    elif role == 'head':
        from head_of_studio import handle_head_start
        handle_head_start(message)
        return

    # Для обычных пользователей
    user_start(message)


def user_start(message):
    """Старт для обычного пользователя"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Каталог студий')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Мои заявки')
    btn3 = types.KeyboardButton('Подать заявку')
    markup.row(btn2, btn3)

    bot.send_message(
        message.chat.id,
        '<em>Привет, в этом боте ты можешь узнать про творческие студии'
        ' ГУАП и стать частью активной студенческой жизни!</em>',
        parse_mode='html',
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == 'Каталог студий')
def handle_catalog(message):
    """Показ каталога студий"""
    show_studio_catalog(bot, message.chat.id)


@bot.message_handler(func=lambda message: message.text == 'Подать заявку')
def handle_apply_from_menu(message):
    """Подать заявку из меню"""
    show_studio_catalog(bot, message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('info:'))
def handle_studio_info(call):
    """Показ информации о студии"""
    show_studio_info(bot, call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('apply:'))
def handle_apply(call):
    """Начало заполнения анкеты"""
    studio_id = int(call.data.split(':')[1])
    questionnaire_flow.start_questionnaire(call, studio_id)


@bot.callback_query_handler(func=lambda call: call.data in ['use_autofill', 'manual_fill'])
def handle_autofill_choice(call):
    """Обработка выбора автозаполнения"""
    user_id = call.from_user.id

    if user_id not in questionnaire_flow.user_states:
        bot.answer_callback_query(call.id, "Сессия устарела")
        return

    state = questionnaire_flow.user_states[user_id]
    studio_id = state['studio_id']

    if call.data == 'use_autofill':
        user_data = state['user_data']
        logger.info(f"Данные пользователя для автозаполнения: {user_data}")

        # Получаем все вопросы для этой студии
        questions = QuestionnaireBuilder.get_question_objects(studio_id)

        for q in questions:
            if q.autofill_field and q.autofill_field in user_data:
                value = user_data[q.autofill_field]
                if value and str(value).strip():
                    # Сохраняем значение в ответы
                    state['answers'][q.id] = str(value)
                    logger.info(f"Автозаполнение: {q.id} = {value}")

        bot.edit_message_text(
            "✅ Данные автозаполнены.\nПродолжаем с оставшимися вопросами...",
            call.message.chat.id,
            call.message.message_id
        )

    # Начинаем опрос
    state['state'] = 'answering'
    questionnaire_flow._ask_next_question(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer:'))
def handle_select_answer(call):
    """Обработка выбора из инлайн-клавиатуры"""
    if questionnaire_flow.user_states.get(call.from_user.id, {}).get('state') == 'answering':
        questionnaire_flow._handle_select_answer(call)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_text_messages(message):
    """Обработка всех текстовых сообщений"""
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, находится ли пользователь в процессе заполнения анкеты
    if user_id in questionnaire_flow.user_states and questionnaire_flow.user_states[user_id].get(
            'state') == 'answering':
        questionnaire_flow.process_answer(message)
        return

    role = get_user_role(username)

    if role == "admin":
        from Admin import handle_admin_message
        handle_admin_message(message)
        return

    # Обработка других команд
    if message.text == 'Мои заявки':
        bot.send_message(message.chat.id, "Функция 'Мои заявки' в разработке")
    else:
        bot.send_message(message.chat.id, "Используйте кнопки меню или команду /start")


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_application')
def handle_confirm_application(call):
    """Обработка подтверждения заявки"""
    if call.from_user.id in questionnaire_flow.user_states:
        questionnaire_flow._confirm_application(call)


@bot.callback_query_handler(func=lambda call: call.data == 'restart_questionnaire')
def handle_restart_questionnaire(call):
    """Обработка перезаполнения анкеты"""
    user_id = call.from_user.id
    if user_id in questionnaire_flow.user_states:
        state = questionnaire_flow.user_states[user_id]
        studio_id = state['studio_id']

        # Начинаем заново
        questionnaire_flow.start_questionnaire(call, studio_id)

# В самом конце файла, перед запуском бота, добавьте:

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_answer:'))
def handle_select_answer(call):
    """Обработка выбора из inline-клавиатуры для select вопросов"""
    questionnaire_flow.process_select_answer(call)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_application')
def handle_confirm_application(call):
    """Обработка подтверждения заявки"""
    questionnaire_flow._confirm_application(call)

@bot.callback_query_handler(func=lambda call: call.data == 'restart_questionnaire')
def handle_restart_questionnaire(call):
    """Обработка перезаполнения анкеты"""
    questionnaire_flow._restart_questionnaire(call)


# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)