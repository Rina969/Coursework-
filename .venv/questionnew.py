from typing import Dict, Any, Callable, Optional
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
                 options: Optional[list] = None):
        self.id = question_id
        self.text = text
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
ALL_QUESTIONS = {
    'full_name': ("Укажите ваше ФИО (полностью):",
                  Question('full_name', 'ФИО', autofill_field='full_name')),

    'group': ("Укажите номер вашей группу:",
              Question('group', 'Группа', autofill_field='student_group')),

    'phone_number': ("Укажите ваш номер телефона:",
                     Question('phone_number', 'Телефон', 'phone_number', autofill_field='phone_number')),

    'email': ("Укажите ваш email адрес:",
              Question('email', 'Email', 'email', autofill_field='email')),

    'experience': ("Расскажите о вашем опыте в данной деятельности:",
                   Question('experience', 'Опыт в деятельности')),

    'motivation': ("Почему вы хотите вступить в эту студию?",
                   Question('motivation', 'Мотивация вступления')),

    'activeness': ("Готовы ли вы участвовать в мероприятиях студии? (да/нет)",
                   Question('activeness', 'Участие в мероприятиях', 'boolean')),

    'media': ("Какое направление вам интересно?\nВарианты: Фотостудия, Видеостудия, Студия дизайна, Журналистика и СММ",
              Question('media', 'Направление медиацентра', 'select',
                       options=['Фотостудия', 'Видеостудия', 'Студия дизайна', 'Журналистика и СММ'])),

    'music_instrument': ("На каком инструменте вы играете (если играете)?",
                         Question('music_instrument', 'Музыкальный инструмент')),

    'singing_experience': ("Есть ли у вас опыт пения? Если да, опишите его:",
                           Question('singing_experience', 'Опыт пения')),

    'improvisation': ("Как вы относитесь к импровизации?",
                      Question('improvisation', 'Импровизация')),

    'tech_skills': ("Какими техническими навыками вы владеете?",
                    Question('tech_skills', 'Технические навыки')),

    'organizational_exp': ("Был ли у вас опыт организации мероприятий? Опишите:",
                           Question('organizational_exp', 'Организационный опыт')),

    'quote': ("Девиз по жизни или цитата, которая вас вдохновляет:",
              Question('quote', 'Цитата')),

    'project_ideas': ("Есть ли у вас идеи для проектов в студии?",
                      Question('project_ideas', 'Идеи для проектов')),

    'leadership': ("Есть ли у вас лидерский опыт?",
                   Question('leadership', 'Лидерские качества')),

    'public_speaking': ("Как вы относитесь к публичным выступлениям?",
                        Question('public_speaking', 'Публичные выступления')),

    'feedback_source': ("Откуда вы узнали о нашей студии?",
                        Question('feedback_source', 'Источник информации')),
}


def get_question_handler(question_id: str) -> str:
    """Возвращает текст вопроса по ID"""
    result = ALL_QUESTIONS.get(question_id)
    return result[0] if result else ""


def get_question_obj(question_id: str) -> Optional[Question]:
    """Возвращает объект вопроса по ID"""
    result = ALL_QUESTIONS.get(question_id)
    return result[1] if result else None