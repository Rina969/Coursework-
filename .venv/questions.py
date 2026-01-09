from typing import Dict, Any, Callable, Optional
import re


class Question:
    """Класс для хранения вопроса"""

    def __init__(self,
                 question_id: str,
                 text: str,  # Полный текст вопроса должен передаваться
                 question_type: str = 'text',
                 is_required: bool = True,
                 autofill_field: Optional[str] = None,
                 validation_func: Optional[Callable] = None,
                 options: Optional[list] = None):
        self.id = question_id
        self.text = text  # Используйте переданный текст
        self.type = question_type  # text, phone, email, boolean, select
        self.is_required = is_required
        self.autofill_field = autofill_field
        self.validation_func = validation_func
        self.options = options or []

    def validate(self, answer: str) -> tuple[bool, str]:
        """Валидация ответа"""
        answer = answer.strip()

        if self.is_required and not answer:
            return False, "Это обязательный вопрос"

        if self.validation_func:
            return self.validation_func(answer)

        # Базовая валидация по типу
        if self.type == 'phone_number':
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


# ========== СЛОВАРЬ ВСЕХ ВОПРОСОВ ==========
# ИСПРАВЛЕНО: Теперь сразу создаем объекты Question с полным текстом
ALL_QUESTIONS = {
    'full_name': Question(
        'full_name',
        'Укажите ваше ФИО (полностью):',
        autofill_field='full_name'
    ),

    'group': Question(
        'group',
        'Укажите номер вашей группу:',
        autofill_field='student_group'
    ),

    'phone_number': Question(
        'phone_number',
        'Укажите ваш номер телефона:',
        'phone_number',
        autofill_field='phone_number'
    ),

    'email': Question(
        'email',
        'Укажите ваш email адрес:',
        'email',
        autofill_field='email'
    ),

    'experience': Question(
        'experience',
        'Расскажите о вашем опыте в данной деятельности:'
    ),

    'motivation': Question(
        'motivation',
        'Почему вы хотите вступить в эту студию?'
    ),

    'expectations': Question(
        'expectations',
        'Какие у вас ожидания от участия в студии?'
    ),

    'activeness': Question(
        'activeness',
        'Готовы ли вы участвовать в мероприятиях студии? (да/нет)',
        'boolean'
    ),

    'media': Question(
        'media',
        'Какое направление вам интересно?\nВарианты: Фотостуди, Видеостудия, Студия дизайна, Журналистика и СММ',
        'select',
        options=['Фотостуди', 'Видеостудия', 'Студия дизайна', 'Журналистика и СММ']
    ),

    'music_instrument': Question(
        'music_instrument',
        'На каком инструменте вы играете (если играете)?'
    ),

    'singing_experience': Question(
        'singing_experience',
        'Есть ли у вас опыт пения? Если да, опишите его:'
    ),

    'improvisation': Question(
        'improvisation',
        'Как вы относитесь к импровизации?'
    ),

    'tech_skills': Question(
        'tech_skills',
        'Какими техническими навыками вы владеете?'
    ),

    'organizational_exp': Question(
        'organizational_exp',
        'Был ли у вас опыт организации мероприятий? Опишите:'
    ),

    'quote': Question(
        'quote',
        'Девиз по жизни или цитата, которая вас вдохновляет:'
    ),

    'project_ideas': Question(
        'project_ideas',
        'Есть ли у вас идеи для проектов в студии?'
    ),

    'leadership': Question(
        'leadership',
        'Есть ли у вас лидерский опыт?'
    ),

    'why_choose_us': Question(
        'why_choose_us',
        'Почему вы выбрали именно нашу студию?'
    ),

    'feedback_source': Question(
        'feedback_source',
        'Откуда вы узнали о нашей студии?'
    ),

    'public_speaking': Question(
        'public_speaking',
        'Как вы относитесь к публичным выступлениям?'
    ),
}


def get_question_handler(question_id: str) -> str:
    """Возвращает текст вопроса по ID"""
    q_obj = ALL_QUESTIONS.get(question_id)
    return q_obj.text if q_obj else ""


def get_question_obj(question_id: str) -> Optional[Question]:
    """Возвращает объект вопроса по ID"""
    return ALL_QUESTIONS.get(question_id)
