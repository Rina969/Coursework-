from typing import Dict, List, Any, Optional, Callable
from questions import get_question_handler, get_question_obj, ALL_QUESTIONS

class QuestionnaireBuilder:
    """Сборщик анкет для разных студий"""
    
    STUDIO_QUESTIONNAIRES = {
        # ID студии: [список ID вопросов из ALL_QUESTIONS]
        1: { 'name': 'Танцевальная студия',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'project_ideas',    # 5. Стиль танца
                'experience',     # 6. Опыт
                'motivation',     # 7. Мотивация
                'activeness',     # 8. Участие в мероприятиях
            ]
        },
        6: {'name': 'КВН',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'experience',
                'quot',
                'public_speakin',
            ]
        },
        2: {'name': 'Театральная студия',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',   # 5. Театральные роли
                'experience',     # 6. Опыт
                'motivation',     # 7. Мотивация
                'improvisation',
                'feedback_source',
            ]
        },
        4: {'name': 'МУЗГУАП',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'music_instrument', # 5. Музыкальный инструмент
                'singing_experience', # 6. Опыт пения
                'public_speakin',
                'activeness',
            ]
        },
        5: {'name': 'Медиацентр',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'media',
                'experience',
                'project_ideas',
                'time_commitment',
            ]
        },
        3: {'name': 'Студия технического обеспечения мероприятий',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'tech_skills',    # 5. Технические навыки
                'organizational_exp',
                'leadership',
                'feedback_source',
            ]
        },
        7: {'name': 'Студия организации мероприятий',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'organizational_exp',
                'motivation',
                'activeness',
                'tech_skills',
            ]
        },
        8: {'name': 'Студия ведущих',
            'questions': [
                'full_name',      # 1. ФИО
                'group',          # 2. Группа
                'phone_number',          # 3. Телефон
                'email',          # 4. Email
                'experience', # 6. Идеи для проектов
                'public_speakin',
                'quot',
                'improvisation',
            ]
        },
    }
    
    @classmethod
    def get_questionnaire_for_studio(cls, studio_id: int) -> Optional[Dict[str, Any]]:
        """Получает конфигурацию анкеты для студии"""
        return cls.STUDIO_QUESTIONNAIRES.get(studio_id)
    
    @classmethod
    def get_studio_name(cls, studio_id: int) -> str:
        """Получает название студии"""
        config = cls.get_questionnaire_for_studio(studio_id)
        return config.get('name', 'Неизвестная студия') if config else 'Неизвестная студия'
    
    @classmethod
    def get_question_sequence(cls, studio_id: int) -> List[str]:
        """Получает последовательность вопросов для студии"""
        config = cls.get_questionnaire_for_studio(studio_id)
        return config.get('questions', []) if config else []
    
    @classmethod
    def build_questionnaire_handlers(cls, studio_id: int) -> List[Callable]:
        """Собирает список обработчиков вопросов для студии"""
        question_ids = cls.get_question_sequence(studio_id)
        handlers = []
        
        for qid in question_ids:
            handler = get_question_handler(qid)
            if handler:
                handlers.append(handler)
        
        return handlers
    
    @classmethod
    def get_question_objects(cls, studio_id: int) -> List[Any]:
        """Получает объекты вопросов для студии"""
        question_ids = cls.get_question_sequence(studio_id)
        questions = []
        
        for qid in question_ids:
            q_obj = get_question_obj(qid)
            if q_obj:
                questions.append(q_obj)
        
        return questions
    
    @classmethod
    def get_autofill_fields(cls, studio_id: int) -> List[str]:
        """Получает список полей для автозаполнения"""
        questions = cls.get_question_objects(studio_id)
        autofill_fields = []
        
        for q in questions:
            if q.autofill_field:
                autofill_fields.append(q.autofill_field)
        
        # Убираем дубликаты
        return list(set(autofill_fields))

    #У нас каждый раз новая анкета, зачем автозаполнение??
    @classmethod
    def can_autofill(cls, studio_id: int, user_data: Dict[str, Any]) -> bool:
        """Проверяет, можно ли автозаполнить анкету"""
        autofill_fields = cls.get_autofill_fields(studio_id)
        
        if not autofill_fields:
            return False
        
        # Проверяем, сколько полей можно автозаполнить
        fillable_count = 0
        for field in autofill_fields:
            value = user_data.get(field, '')
            if value and str(value).strip():
                fillable_count += 1
        
        return fillable_count == len(autofill_fields)
    
    @classmethod
    def generate_summary(cls, studio_id: int, answers: Dict[str, str]) -> str:
        """Генерирует сводку по ответам"""
        questions = cls.get_question_objects(studio_id)
        studio_name = cls.get_studio_name(studio_id)
        
        lines = [f"📋 *Анкета для студии: {studio_name}*\n"]
        
        for i, q in enumerate(questions, 1):
            answer = answers.get(q.id, "❌ Не заполнено")
            lines.append(f"\n{i}. *{q.text}*\n{answer}")
        
        return "\n".join(lines)
    
    @classmethod
    def validate_answers(cls, studio_id: int, answers: Dict[str, str]) -> tuple[bool, Dict[str, str]]:
        """Валидирует все ответы анкеты"""
        questions = cls.get_question_objects(studio_id)
        errors = {}
        
        for q in questions:
            answer = answers.get(q.id, '').strip()
            
            if q.is_required and not answer:
                errors[q.id] = "Обязательный вопрос не заполнен"
                continue
            
            is_valid, error_msg = q.validate(answer)
            if not is_valid:
                errors[q.id] = error_msg
        
        return len(errors) == 0, errors











