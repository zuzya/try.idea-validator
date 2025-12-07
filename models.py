from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# --- Core Models ---

class BusinessIdea(BaseModel):
    title: str = Field(description="Название стартапа (на русском)")
    description: str = Field(description="Суть продукта, ценностное предложение (на русском)")
    monetization_strategy: str = Field(description="Модель заработка: подписка, комиссия и т.д. (на русском)")
    target_audience: str = Field(description="Целевая аудитория в РФ (на русском)")

class CritiqueFeedback(BaseModel):
    is_approved: bool = Field(description="True если оценка >= 8")
    feedback: str = Field(description="Подробная критика, риски и советы (на русском языке)")
    feedback: str = Field(description="Подробная критика, риски и советы (на русском языке)")
    score: int = Field(description="Оценка от 1 до 10", ge=1, le=10)

# --- Simulation Mechanics Models (Turn-by-Turn) ---

class PersonaThought(BaseModel):
    mood: Literal["Interested", "Annoyed", "Confused", "Skeptical"]
    patience: int = Field(description="Остаток терпения от 0 до 100")
    inner_monologue: str = Field(description="Честные мысли. Анализ вопроса на предмет 'чуши'. Решение, врать или нет.")
    verbal_response: str = Field(description="То, что персона говорит вслух исследователю.")

class InterviewerThought(BaseModel):
    analysis: str = Field(description="Анализ последнего ответа: был ли он честным? Нужно ли копать глубже?")
    next_question: str = Field(description="Вопрос к респонденту.")
    status: Literal["CONTINUE", "WRAP_UP"] = Field(description="Завершать ли интервью.")

# --- Synthetic CustDev Models ---

class Hypothesis(BaseModel):
    description: str = Field(description="Формулировка гипотезы на русском")
    type: Literal["Problem", "Solution", "Monetization"] = Field(description="Тип гипотезы")

class TargetPersona(BaseModel):
    role: str = Field(description="Роль (например: 'Главный бухгалтер' или 'Мама в декрете')")
    archetype: str = Field(description="Психотип (например: 'Консерватор', 'Новатор', 'Хейтер')")
    context: str = Field(description="Контекст жизни/работы (например: 'Работает в 1С, ненавидит обновления, зп 80к')")
    name: str = Field(description="Русское имя (например: 'Татьяна Ивановна')")

class InterviewGuide(BaseModel):
    target_personas: List[TargetPersona] = Field(description="Список из 3-х конкретных людей для интервью")
    questions: List[str] = Field(description="Список вопросов в стиле 'The Mom Test'")
    hypotheses_to_test: List[Hypothesis] = Field(description="Гипотезы для проверки")

class UserPersona(BaseModel):
    name: str = Field(description="Имя респондента")
    role: str = Field(description="Социальная роль / Профессия (например: 'Скептичный главбух')")
    background: str = Field(description="Краткая биография и привычки (контекст РФ)")
    
class InterviewResult(BaseModel):
    persona: UserPersona
    transcript_summary: str = Field(description="Краткая выжимка диалога (самые важные инсайты)")
    pain_level: int = Field(description="Насколько болит проблема от 1 до 10", ge=1, le=10)
    willingness_to_pay: int = Field(description="Готовность платить от 1 до 10", ge=1, le=10)
    
class ResearchReport(BaseModel):
    key_insights: List[str] = Field(description="Главные инсайты после всех интервью")
    confirmed_hypotheses: List[str] = Field(description="Список подтвержденных гипотез")
    rejected_hypotheses: List[str] = Field(description="Список опровергнутых гипотез")
    pivot_recommendation: str = Field(description="Рекомендация для Продукта: что изменить в идее на основе данных (на русском)")

class RichPersona(BaseModel):
    name: str = Field(description="Реалистичное имя и фамилия")
    role: str = Field(description="Точная должность")
    age: int = Field(description="Возраст")
    company_context: str = Field(description="Где работает: стартап, энтерпрайз, фриланс")
    bio: str = Field(description="Краткая биография, профессиональный бэкграунд")
    psychotype: str = Field(description="Психотип: Скептик, Новатор, Консерватор и т.д.")
    key_frustrations: List[str] = Field(description="Список реальных рабочих болей")
    tech_stack: List[str] = Field(description="Конкретный софт, который использует (Jira, 1C, Excel)")
    hidden_constraints: str = Field(description="Скрытые мотивы: нет бюджета, боится увольнения, лень")
