from typing import Dict, Any, Callable, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import re

class Question:
    """Класс для хранения вопроса"""
    def __init__(self, 
                 question_id: str,
                 text: str,
                 question_type: str = 'text',
                 is_required: bool = True,
                 autofill_field: Optional[str] = None,
                 validation_func: Optional[Callable] = None,
                 options: Optional[list] = None,
                 keyboard: Optional[list] = None):
        self.id = question_id
        self.text = text
        self.type = question_type  # text, phone, email, boolean, select, multi_select
        self.is_required = is_required
        self.autofill_field = autofill_field  # Поле для автозаполнения из БД
        self.validation_func = validation_func
        self.options = options or []
        self.keyboard = keyboard
    
    def validate(self, answer: str) -> tuple[bool, str]:
        """Валидация ответа"""
        answer = answer.strip()
        
        if self.is_required and not answer:
            return False, "Это обязательный вопрос"
        
        if self.validation_func:
            return self.validation_func(answer)
        
        # Базовая валидация по типу
        if self.type == 'phone':
            phone_digits = re.sub(r'[^\d]', '', answer)
            if len(phone_digits) < 10:
                return False, "Введите корректный номер телефона"
        
        elif self.type == 'email':
            if '@' not in answer or '.' not in answer:
                return False, "Введите корректный email"
        
        elif self.type == 'boolean':
            if answer.lower() not in ['да', 'нет']:
                return False, "Ответьте 'да' или 'нет'"
        
        elif self.type == 'select':
            if answer not in self.options:
                return False, f"Выберите вариант из списка: {', '.join(self.options)}"
        
        return True, ""


# ------ Общие вопросы------
def ask_full_name(update: Update, context: CallbackContext) -> None:
    """Вопрос: ФИО"""
    update.message.reply_text("1. 📝 Укажите ваше ФИО (полностью):")

def ask_group(update: Update, context: CallbackContext) -> None:
    """Вопрос: Группа"""
    update.message.reply_text("2. 🎓 Укажите номер вашей группу:")

def ask_phone(update: Update, context: CallbackContext) -> None:
    """Вопрос: Телефон"""
    update.message.reply_text("3. 📱 Укажите ваш номер телефона:")

def ask_email(update: Update, context: CallbackContext) -> None:
    """Вопрос: Email"""
    update.message.reply_text("4. 📧 Укажите ваш email адрес:")

def ask_experience(update: Update, context: CallbackContext) -> None:
    """Вопрос: Опыт в деятельности"""
    update.message.reply_text("5. 💼 Расскажите о вашем опыте в данной деятельности:")

def ask_motivation(update: Update, context: CallbackContext) -> None:
    """Вопрос: Мотивация"""
    update.message.reply_text("6. 🎯 Почему вы хотите вступить в эту студию?")

def ask_expectations(update: Update, context: CallbackContext) -> None:
    """Вопрос: Ожидания"""
    update.message.reply_text("7. 🌟 Какие у вас ожидания от участия в студии?")

def ask_activeness(update: Update, context: CallbackContext) -> None:
    """Вопрос: Участие в мероприятиях"""
    keyboard = [
        [InlineKeyboardButton("Да", callback_data="activeness_yes"),
         InlineKeyboardButton("Нет", callback_data="activeness_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "8. 📢 Готовы ли вы участвовать в мероприятиях студии?",
        reply_markup=reply_markup
    )

# ------ дополнительные опросы ------

def ask_dance_style(update: Update, context: CallbackContext) -> None:
    """Вопрос: Стиль танца"""
    keyboard = [
        [InlineKeyboardButton("Хип-хоп", callback_data="dance_hiphop")],
        [InlineKeyboardButton("Бальные танцы", callback_data="dance_ballroom")],
        [InlineKeyboardButton("Современные", callback_data="dance_modern")],
        [InlineKeyboardButton("Народные", callback_data="dance_folk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "9. 💃 Какой танцевальный стиль вам интересен?",
        reply_markup=reply_markup
    )

def ask_music_instrument(update: Update, context: CallbackContext) -> None:
    """Вопрос: Музыкальный инструмент"""
    update.message.reply_text("10. 🎵 На каком инструменте вы играете (если играете)?")

def ask_singing_experience(update: Update, context: CallbackContext) -> None:
    """Вопрос: Опыт пения"""
    update.message.reply_text("11. 🎤 Есть ли у вас опыт пения? Если да, опишите его:")

def ask_theater_role(update: Update, context: CallbackContext) -> None:
    """Вопрос: Предпочитаемые роли в театре"""
    keyboard = [
        [InlineKeyboardButton("Драматические", callback_data="role_drama")],
        [InlineKeyboardButton("Комические", callback_data="role_comedy")],
        [InlineKeyboardButton("Характерные", callback_data="role_character")],
        [InlineKeyboardButton("Не знаю", callback_data="role_unknown")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "12. 🎭 Какие роли вам интересны в театре?",
        reply_markup=reply_markup
    )

def ask_tech_skills(update: Update, context: CallbackContext) -> None:
    """Вопрос: Технические навыки"""
    update.message.reply_text("13. 💻 Какими техническими навыками вы владеете?")

def ask_organizational_exp(update: Update, context: CallbackContext) -> None:
    """Вопрос: Организационный опыт"""
    update.message.reply_text("14. 📋 Был ли у вас опыт организации мероприятий? Опишите:")

def ask_leadership(update: Update, context: CallbackContext) -> None:
    """Вопрос: Лидерские качества"""
    keyboard = [
        [InlineKeyboardButton("Да, есть опыт", callback_data="leadership_yes")],
        [InlineKeyboardButton("Хочу развивать", callback_data="leadership_develop")],
        [InlineKeyboardButton("Пока нет", callback_data="leadership_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "15. 👨‍💼 Есть ли у вас лидерский опыт?",
        reply_markup=reply_markup
    )

def ask_project_ideas(update: Update, context: CallbackContext) -> None:
    """Вопрос: Идеи для проектов"""
    update.message.reply_text("16. 💡 Есть ли у вас идеи для проектов в студии?")

def ask_time_commitment(update: Update, context: CallbackContext) -> None:
    """Вопрос: Временные возможности"""
    update.message.reply_text("17. ⏰ Сколько часов в неделю вы готовы уделять студии?")

def ask_why_choose_us(update: Update, context: CallbackContext) -> None:
    """Вопрос: Почему выбрали нас"""
    update.message.reply_text("18. ❓ Почему вы выбрали именно нашу студию?")

def ask_feedback_source(update: Update, context: CallbackContext) -> None:
    """Вопрос: Откуда узнали о студии"""
    keyboard = [
        [InlineKeyboardButton("От друзей", callback_data="source_friends")],
        [InlineKeyboardButton("Соцсети", callback_data="source_social")],
        [InlineKeyboardButton("Сайт вуза", callback_data="source_website")],
        [InlineKeyboardButton("Объявление", callback_data="source_poster")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "19. 📢 Откуда вы узнали о нашей студии?",
        reply_markup=reply_markup
    )

def ask_special_needs(update: Update, context: CallbackContext) -> None:
    """Вопрос: Особые потребности"""
    update.message.reply_text("20. ♿ Есть ли у вас особые потребности, которые мы должны учитывать?")


# ========== СЛОВАРЬ ВСЕХ ВОПРОСОВ ==========
ALL_QUESTIONS = {
    # ID вопроса: (функция-обработчик, объект Question)
    'full_name': (ask_full_name, Question('full_name', 'ФИО', autofill_field='full_name')),
    'group': (ask_group, Question('group', 'Группа', autofill_field='student_group')),
    'phone': (ask_phone, Question('phone', 'Телефон', 'phone', autofill_field='phone')),
    'email': (ask_email, Question('email', 'Email', 'email', autofill_field='email')),
    'experience': (ask_experience, Question('experience', 'Опыт в деятельности')),
    'motivation': (ask_motivation, Question('motivation', 'Мотивация вступления')),
    'expectations': (ask_expectations, Question('expectations', 'Ожидания от студии')),
    'activeness': (ask_activeness, Question('activeness', 'Участие в мероприятиях', 'boolean')),
    'dance_style': (ask_dance_style, Question('dance_style', 'Танцевальный стиль', 'select',
                                            options=['Хип-хоп', 'Бальные танцы', 'Современные', 'Народные'])),
    'music_instrument': (ask_music_instrument, Question('music_instrument', 'Музыкальный инструмент')),
    'singing_experience': (ask_singing_experience, Question('singing_experience', 'Опыт пения')),
    'theater_role': (ask_theater_role, Question('theater_role', 'Театральные роли', 'select',
                                               options=['Драматические', 'Комические', 'Характерные', 'Не знаю'])),
    'tech_skills': (ask_tech_skills, Question('tech_skills', 'Технические навыки')),
    'organizational_exp': (ask_organizational_exp, Question('organizational_exp', 'Организационный опыт')),
    'leadership': (ask_leadership, Question('leadership', 'Лидерский опыт', 'select',
                                          options=['Да, есть опыт', 'Хочу развивать', 'Пока нет'])),
    'project_ideas': (ask_project_ideas, Question('project_ideas', 'Идеи для проектов')),
    'time_commitment': (ask_time_commitment, Question('time_commitment', 'Временные возможности')),
    'why_choose_us': (ask_why_choose_us, Question('why_choose_us', 'Почему выбрали нас')),
    'feedback_source': (ask_feedback_source, Question('feedback_source', 'Источник информации', 'select',
                                                    options=['От друзей', 'Соцсети', 'Сайт вуза', 'Объявление'])),
    'special_needs': (ask_special_needs, Question('special_needs', 'Особые потребности', is_required=False))
}

def get_question_handler(question_id: str):
    """Возвращает обработчик вопроса по ID"""
    return ALL_QUESTIONS.get(question_id, (None, None))[0]

def get_question_obj(question_id: str) -> Optional[Question]:
    """Возвращает объект вопроса по ID"""
    result = ALL_QUESTIONS.get(question_id)
    return result[1] if result else None
