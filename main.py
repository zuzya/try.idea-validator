import operator
from typing import Annotated, List, Optional, TypedDict, Union, Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph, START
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from config import llm_generator, llm_critic, llm_router, GENERATOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT, RESEARCHER_SYSTEM_PROMPT, SIMULATION_SYSTEM_PROMPT, ANALYST_SYSTEM_PROMPT, MOCK_SIMULATION
import time
import json
import re
import pathlib

load_dotenv()

# --- 1. Data Structures (Pydantic Models) ---

class BusinessIdea(BaseModel):
    title: str = Field(description="Название стартапа (на русском)")
    description: str = Field(description="Суть продукта, ценностное предложение (на русском)")
    monetization_strategy: str = Field(description="Модель заработка: подписка, комиссия и т.д. (на русском)")
    target_audience: str = Field(description="Целевая аудитория в РФ (на русском)")

class CritiqueFeedback(BaseModel):
    is_approved: bool = Field(description="True если оценка >= 8")
    feedback: str = Field(description="Подробная критика, риски и советы (на русском языке)")
    score: int = Field(description="Оценка от 1 до 10", ge=1, le=10)

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

# --- 2. Graph State ---

class GraphState(TypedDict):
    initial_input: str
    current_idea: Optional[BusinessIdea]
    
    # --- Research Fields (Synthetic CustDev) ---
    interview_guide: Optional[InterviewGuide]  # Скрипт и гипотезы
    raw_interviews: List[InterviewResult]      # Результаты каждого "звонка"
    research_report: Optional[ResearchReport]  # Итоговый анализ
    # -------------------------------------------
    
    critique: Optional[CritiqueFeedback]
    iteration_count: int
    messages: List[BaseMessage]  # Optional, but good for history
    max_iterations: int  # Add configurable max iterations
    mode: Literal["full", "research_only"] # New field for mode selection
    
    # --- Configuration Flags ---
    enable_simulation: bool
    enable_critic: bool

# --- 3. Nodes & Logic ---

# Функция-"чистильщик", которая вытаскивает JSON из любого ответа модели
def extract_json_from_text(text: str):
    try:
        # 1. Пытаемся найти JSON внутри блога кода ```json ... ```
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 2. Пытаемся найти JSON внутри обычных скобок { ... }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
            
        # 3. Если ничего не нашли, возвращаем как есть (а вдруг там чистый JSON)
        return text
    except Exception:
        return text

def generator_node(state: GraphState) -> GraphState:
    print(f"\n--- GENERATOR NODE (Iteration {state['iteration_count']}) ---")
    
    # ВАЖНО: Мы НЕ используем .with_structured_output, так как он нестабилен
    # Мы используем обычный invoke и парсим руками.
    
    # Формируем JSON-схему текстом, чтобы модель знала формат
    schema_instruction = """
    КРИТИЧЕСКИ ВАЖНО: Твой ответ должен быть СТРОГО валидным JSON объектом.
    НЕТ Markdown блоков ```json
    НЕТ вводных слов
    НЕТ вложенных объектов типа {"BusinessIdea": {...}}
    
    ТОЧНЫЙ ФОРМАТ (копируй структуру один-в-один, меняя только ЗНАЧЕНИЯ):
    {
      "title": "Название стартапа на русском",
      "description": "Описание продукта на русском",
      "monetization_strategy": "Модель заработка на русском",
      "target_audience": "Целевая аудитория на русском"
    }
    
    ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
    {
      "title": "Забота.РФ",
      "description": "Платформа для ухода за пожилыми людьми",
      "monetization_strategy": "Подписка 3000₽/мес + комиссия 15% за услуги",
      "target_audience": "Работающие взрослые дети (35-55 лет) в городах-миллионниках"
    }
    
    ЗАПРЕЩЕНО:
    - Использовать русские имена ключей (НазваниеПродукта, КраткоеОписание)
    - Создавать вложенные объекты
    - Добавлять ```json или другой markdown
    
    НАЧИНАЙ ОТВЕТ СРАЗУ С { и ЗАКАНЧИВАЙ }
    """
    
    if state["iteration_count"] == 0:
        print(">> Generating initial ZERO-TO-ONE concept...")
        user_content = f"""
        USER INPUT: '{state['initial_input']}'
        
        Task: Synthesize a Unicorn startup concept for the RUSSIAN MARKET (2025).
        """
    elif state.get("research_report") and not state.get("critique"):
        print(">> PIVOTING based on USER RESEARCH...")
        current_json = state["current_idea"].model_dump_json(indent=2)
        report_json = state["research_report"].model_dump_json(indent=2)
        
        user_content = f"""
        USER RESEARCH COMPLETED. UPDATE THE IDEA.
        
        PREVIOUS IDEA:
        {current_json}
        
        RESEARCH FINDINGS:
        {report_json}
        
        INSTRUCTIONS:
        1. Discard features that users rejected (see 'rejected_hypotheses').
        2. Double down on 'confirmed_hypotheses'.
        3. Implement the 'pivot_recommendation'.
        
        {schema_instruction}
        """
    elif state.get("critique"):
        print(">> PIVOTING based on Critique...")
        current_json = state["current_idea"].model_dump_json(indent=2)
        critique_json = state["critique"].model_dump_json(indent=2)
        
        user_content = f"""
        CRITIQUE RECEIVED. YOU MUST ITERATE OR PIVOT.
        
        PREVIOUS IDEA:
        {current_json}
        
        CRITIC FEEDBACK:
        {critique_json}
        
        INSTRUCTIONS:
        1. Address the fatal flaws.
        2. Focus on Russian local tech (VK, Telegram, SPB, Gosuslugi).
        
        {schema_instruction}
        """
    else:
        # Fallback - should not happen in normal flow, but prevents crashes
        print(">> WARNING: Unexpected state, generating fallback...")
        user_content = f"""
        USER INPUT: '{state['initial_input']}'
        
        Task: Refine the existing idea.
        {schema_instruction}
        """

    messages = [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    # --- RETRY & PARSE LOGIC ---
    new_idea = None
    last_error = None
    
    for attempt in range(3):
        try:
            print(f"   -> Invoking LLM (Attempt {attempt + 1})...")
            
            response = llm_generator.invoke(messages)
            raw_content = response.content
            
            # --- FIX: ОБРАБОТКА СПИСКА ---
            # Если Gemini вернул список блоков [{'type': 'text', 'text': '...'}]
            if isinstance(raw_content, list):
                print(f"   -> Detected list output, converting to string...")
                raw_content = "".join([
                    block.get("text", "") 
                    for block in raw_content 
                    if isinstance(block, dict) and "text" in block
                ])
            # -----------------------------
            
            # Чистим ответ
            cleaned_json_str = extract_json_from_text(raw_content)
            
            # Парсим в Python dict, а затем в Pydantic
            data_dict = json.loads(cleaned_json_str)
            new_idea = BusinessIdea(**data_dict)
            
            break # Успех!
            
        except Exception as e:
            print(f"   -> Parse Error on attempt {attempt + 1}: {e}")
            print(f"   -> Raw Output causing error: {raw_content[:500]}...") 
            last_error = e

    if new_idea is None:
        print("   -> CRITICAL ERROR: Failed to parse JSON from Generator.")
        # Чтобы не крашить весь процесс, вернем заглушку с ошибкой
        new_idea = BusinessIdea(
            title="Ошибка Генерации (Parsing)",
            description=f"Модель вернула некорректный JSON. Последняя ошибка: {str(last_error)}",
            monetization_strategy="N/A",
            target_audience="N/A"
        )

    print(f"   -> Generated: {new_idea.title}")

    # If we are iterating (critique exists), we should clear the previous research report and critique
    # to allow for a fresh research cycle if enabled.
    return {
        "current_idea": new_idea,
        "iteration_count": state["iteration_count"] + 1,
        "research_report": None, # Clear for next cycle
        "critique": None         # Clear for next cycle
    }

def critic_node(state: GraphState) -> GraphState:
    """
    Simulates and critiques the idea using ChatGPT 5.1 (Reasoning).
    """
    print("\n--- CRITIC NODE ---")
    
    # 1. Bind Structured Output
    structured_llm = llm_critic.with_structured_output(CritiqueFeedback)
    
    current_idea = state["current_idea"]
    
    # 2. Construct Data-Only User Message
    # The System Prompt already tells GPT-5.1 to "Simulate", so we just provide the data.
    user_content = f"""
    CANDIDATE STARTUP IDEA FOR EVALUATION:
    
    {current_idea.model_dump_json(indent=2)}
    
    Run your simulation and provide the verdict.
    """
    
    # 3. Invoke LLM with the Reasoning System Prompt
    messages = [
        SystemMessage(content=CRITIC_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    try:
        feedback = structured_llm.invoke(messages)
        
        # Validate the response
        if feedback is None:
            raise ValueError("LLM returned None. Check API key and model availability.")
        
        print(f"   -> Verdict: {feedback.is_approved} (Score: {feedback.score}/10)")
        print(f"   -> Key Feedback: {feedback.feedback[:100]}...") # Print preview
    except Exception as e:
        print(f"   -> ERROR in critic_node: {e}")
        # Return a default critique to prevent crash
        feedback = CritiqueFeedback(
            is_approved=False,
            feedback=f"Critique failed due to LLM error: {str(e)}",
            score=1
        )
        
    return {"critique": feedback}

def researcher_node(state: GraphState) -> GraphState:
    """
    Generates hypotheses and an interview guide using Gemini 3 Pro.
    Saves the guide to a local file.
    """
    print(f"\n--- RESEARCHER NODE ---")
    
    current_idea = state["current_idea"]
    
    # 1. Construct User Message
    schema_instruction = """
    КРИТИЧЕСКИ ВАЖНО ДЛЯ JSON:
    Используй английские имена полей: target_personas, questions, hypotheses_to_test
    
    ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
    {
      "target_personas": [
        {
          "name": "Татьяна Ивановна",
          "role": "Главный бухгалтер",
          "archetype": "Консерватор",
          "context": "Работает в 1С 15 лет, ненавидит обновления, зп 80к"
        },
        {
          "name": "Алексей",
          "role": "Продакт-менеджер",
          "archetype": "Новатор",
          "context": "Любит экспериментировать, работает в стартапе"
        },
        {
          "name": "Елена",
          "role": "Руководитель отдела",
          "archetype": "Хейтер",
          "context": "Не доверяет новым решениям, ищет подвох"
        }
      ],
      "questions": ["Вопрос 1", "Вопрос 2"],
      "hypotheses_to_test": [
        {"description": "Гипотеза 1", "type": "Problem"},
        {"description": "Гипотеза 2", "type": "Solution"},
        {"description": "Гипотеза 3", "type": "Monetization"}
      ]
    }
    
    ВАЖНО: type должен быть ТОЛЬКО "Problem", "Solution" или "Monetization" (НЕ "Willingness to Pay"!)
    target_personas должен содержать ТОЧНО 3 объекта с полями: role, archetype, context, name (все на русском)
    Не используй русские ключи в JSON
    """
    
    user_content = f"""
    ANALYZE THIS BUSINESS IDEA AND PREPARE USER RESEARCH:
    
    {current_idea.model_dump_json(indent=2)}
    
    Task: Create a 'Mom Test' interview guide to validate this idea in the Russian market.
    
    {schema_instruction}
    """
    
    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    # 2. Invoke LLM
    # We use the same manual parsing logic as generator_node for stability with Gemini
    interview_guide = None
    last_error = None
    
    for attempt in range(3):
        try:
            print(f"   -> Invoking Researcher (Attempt {attempt + 1})...")
            response = llm_generator.invoke(messages)
            raw_content = response.content
            
            if isinstance(raw_content, list):
                raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
                
            cleaned_json_str = extract_json_from_text(raw_content)
            data_dict = json.loads(cleaned_json_str)
            interview_guide = InterviewGuide(**data_dict)
            break
        except Exception as e:
            print(f"   -> Researcher Parse Error: {e}")
            last_error = e
            
    if interview_guide is None:
        print("   -> CRITICAL: Researcher failed to generate guide.")
        # Return empty/default to avoid crash
        return {"interview_guide": None, "iteration_count": state["iteration_count"]}

    print(f"   -> Generated Guide with {len(interview_guide.target_personas)} personas and {len(interview_guide.hypotheses_to_test)} hypotheses")

    # 3. File Persistence
    try:
        # Sanitize title for folder name
        safe_title = re.sub(r'[<>:"/\\|?*]', '', current_idea.title).strip().replace(' ', '_')
        # Limit length just in case
        safe_title = safe_title[:50]
        
        base_dir = pathlib.Path("experiments")
        experiment_dir = base_dir / safe_title
        experiment_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = experiment_dir / "interview_guide.md"
        
        # Format Markdown with new structure
        md_content = f"# Interview Guide: {current_idea.title}\n\n"
        
        md_content += "## Target Personas\n\n"
        for i, persona in enumerate(interview_guide.target_personas, 1):
            md_content += f"### Persona {i}: {persona.name}\n"
            md_content += f"- **Role:** {persona.role}\n"
            md_content += f"- **Archetype:** {persona.archetype}\n"
            md_content += f"- **Context:** {persona.context}\n\n"
        
        md_content += "## Hypotheses to Test\n"
        for h in interview_guide.hypotheses_to_test:
            md_content += f"- **[{h.type}]** {h.description}\n"
            
        md_content += "\n## Questions (The Mom Test)\n"
        for i, q in enumerate(interview_guide.questions, 1):
            md_content += f"{i}. {q}\n"
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"   -> Saved guide to: {file_path}")
        
    except Exception as e:
        print(f"   -> File Save Error: {e}")

    return {
        "interview_guide": interview_guide,
        "iteration_count": state["iteration_count"]
    }

def simulation_node(state: GraphState) -> GraphState:
    """
    Simulates 3 distinct user interviews based on the guide.
    """
    print(f"\n--- SIMULATION NODE ---")
    
    interview_guide = state.get("interview_guide")
    if not interview_guide:
        print("   -> CRITICAL: No interview guide found.")
        return state
        
    current_idea = state["current_idea"]
    
    # Get personas from interview guide (generated by researcher)
    personas = interview_guide.target_personas
    if not personas or len(personas) == 0:
        print("   -> CRITICAL: No personas in interview guide.")
        return state
    
    print(f"   -> Found {len(personas)} personas to interview")
    
    raw_interviews = []
    
    # Prepare File for Transcript
    try:
        safe_title = re.sub(r'[<>:"/\\|?*]', '', current_idea.title).strip().replace(' ', '_')[:50]
        base_dir = pathlib.Path("experiments")
        experiment_dir = base_dir / safe_title
        experiment_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = experiment_dir / "interviews_transcript.md"
        
        # Clear previous file
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(f"# User Interviews: {current_idea.title}\n\n")
            
    except Exception as e:
        print(f"   -> File Setup Error: {e}")
        transcript_path = None

    # Loop & Simulate
    for p in personas:
        print(f"   -> Simulating interview with {p.name}...")
        
        # MOCK MODE CHECK
        if MOCK_SIMULATION:
            print(f"   -> [MOCK MODE] Skipping real LLM call for {p.name}")
            result = InterviewResult(
                persona=UserPersona(name=p.name, role=p.role, background=f"{p.archetype}: {p.context}"),
                transcript_summary=f"Пользователь {p.name} говорит, что идея интересная, но дорого. Хочет Telegram-бот вместо приложения.",
                pain_level=7,
                willingness_to_pay=4
            )
            raw_interviews.append(result)
            
            # Still write to file
            if transcript_path:
                with open(transcript_path, "a", encoding="utf-8") as f:
                    f.write(f"## Interview with {result.persona.name}\n")
                    f.write(f"**Role:** {result.persona.role}\n")
                    f.write(f"**Pain Level:** {result.pain_level}/10\n")
                    f.write(f"**Willingness to Pay:** {result.willingness_to_pay}/10\n\n")
                    f.write(f"### Transcript Summary\n{result.transcript_summary}\n\n")
                    f.write("---\n\n")
            continue
        
        # REAL LLM MODE
        user_content = f"""
        ТЫ ИГРАЕШЬ РОЛЬ:
        Имя: {p.name}
        Профессия: {p.role}
        Психотип: {p.archetype}
        Контекст: {p.context}
        
        Твоя задача — пройти интервью по продукту.
        Будь {p.archetype}. Опирайся на свой контекст: {p.context}
        Отвечай честно. Если решение тебе не подходит — скажи об этом прямо.
        Не пытайся угодить интервьюеру.
        
        ВОПРОСЫ ИНТЕРВЬЮЕРА:
        {json.dumps(interview_guide.questions, ensure_ascii=False, indent=2)}
        
        Сгенерируй диалог и meta-analysis JSON.
        """
        
        messages = [
            SystemMessage(content=SIMULATION_SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ]
        
        # Invoke LLM (GPT-5.1 / Critic Model)
        try:
            response = llm_critic.invoke(messages)
            raw_content = response.content
            
            cleaned_json_str = extract_json_from_text(raw_content)
            data_dict = json.loads(cleaned_json_str)
            
            # Inject Name/Role into the result manually since LLM might generate random ones
            if "persona" not in data_dict:
                data_dict["persona"] = {}
            data_dict["persona"]["name"] = p.name
            data_dict["persona"]["role"] = p.role
            if "background" not in data_dict["persona"]:
                 data_dict["persona"]["background"] = f"{p.archetype}: {p.context}"

            result = InterviewResult(**data_dict)
            raw_interviews.append(result)
            
            # Append to Transcript File
            if transcript_path:
                with open(transcript_path, "a", encoding="utf-8") as f:
                    f.write(f"## Interview with {result.persona.name}\n")
                    f.write(f"**Role:** {result.persona.role}\n")
                    f.write(f"**Pain Level:** {result.pain_level}/10\n")
                    f.write(f"**Willingness to Pay:** {result.willingness_to_pay}\n\n")
                    f.write(f"### Transcript Summary\n{result.transcript_summary}\n\n")
                    # Note: We don't have the full raw dialogue text in the JSON model currently, 
                    # only the summary. The prompt asks for "Transcript" in the text generation 
                    # but the JSON schema only captures summary. 
                    # Ideally, we should capture the full text too, but for now we follow the schema.
                    f.write("---\n\n")
                    
        except Exception as e:
            print(f"   -> Simulation Error for {p['name']}: {e}")
            
    return {
        "raw_interviews": raw_interviews,
        "iteration_count": state["iteration_count"]
    }

def analyst_node(state: GraphState) -> GraphState:
    """
    Analyzes interview transcripts and generates a research report.
    """
    print(f"\n--- ANALYST NODE ---")
    
    raw_interviews = state.get("raw_interviews", [])
    if not raw_interviews:
        print("   -> CRITICAL: No interviews found.")
        return state
        
    current_idea = state["current_idea"]
    
    # 1. Aggregate Context
    transcripts_text = ""
    for i, interview in enumerate(raw_interviews, 1):
        transcripts_text += f"INTERVIEW {i} ({interview.persona.role}):\n"
        transcripts_text += f"Summary: {interview.transcript_summary}\n"
        transcripts_text += f"Pain Level: {interview.pain_level}/10\n"
        transcripts_text += f"Willingness to Pay: {interview.willingness_to_pay}/10\n\n"
        
    user_content = f"""
    ANALYZE THESE INTERVIEWS:
    
    {transcripts_text}
    
    Task: Validate hypotheses and recommend a pivot.
    
    КРИТИЧЕСКИ ВАЖНО: Твой ответ должен быть СТРОГО валидным JSON объектом.
    НЕТ Markdown блоков ```json
    НЕТ вводных слов
    
    ТОЧНЫЙ ФОРМАТ (копируй структуру один-в-один):
    {{
      "key_insights": ["Инсайт 1 простой строкой", "Инсайт 2 простой строкой"],
      "confirmed_hypotheses": ["Гипотеза 1", "Гипотеза 2"],
      "rejected_hypotheses": ["Гипотеза 3"],
      "pivot_recommendation": "Четкая рекомендация одной строкой"
    }}
    
    ЗАПРЕЩЕНО:
    - Использовать вложенные объекты типа {{"insight": "текст"}}
    - key_insights должен быть массивом СТРОК, не объектов
    - Все поля обязательны
    
    НАЧИНАЙ ОТВЕТ СРАЗУ С {{ и ЗАКАНЧИВАЙ }}
    """
    
    messages = [
        SystemMessage(content=ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    # 2. Invoke LLM (Gemini 3 Pro)
    research_report = None
    try:
        response = llm_generator.invoke(messages)
        raw_content = response.content
        
        if isinstance(raw_content, list):
            raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
            
        cleaned_json_str = extract_json_from_text(raw_content)
        data_dict = json.loads(cleaned_json_str)
        research_report = ResearchReport(**data_dict)
        
        print(f"   -> Pivot Recommendation: {research_report.pivot_recommendation[:100]}...")
        
        # 3. File Persistence
        safe_title = re.sub(r'[<>:"/\\|?*]', '', current_idea.title).strip().replace(' ', '_')[:50]
        base_dir = pathlib.Path("experiments")
        experiment_dir = base_dir / safe_title
        experiment_dir.mkdir(parents=True, exist_ok=True)
        report_path = experiment_dir / "research_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Research Report: {current_idea.title}\n\n")
            f.write("## ✅ Confirmed Hypotheses\n")
            for h in research_report.confirmed_hypotheses:
                f.write(f"- {h}\n")
            f.write("\n## ❌ Rejected Hypotheses\n")
            for h in research_report.rejected_hypotheses:
                f.write(f"- {h}\n")
            f.write("\n## 💡 Key Insights\n")
            for h in research_report.key_insights:
                f.write(f"- {h}\n")
            f.write(f"\n## 🔄 Pivot Recommendation\n{research_report.pivot_recommendation}\n")
            
        print(f"   -> Saved report to: {report_path}")
        
    except Exception as e:
        print(f"   -> Analyst Error: {e}")
        
    return {
        "research_report": research_report,
        "iteration_count": state["iteration_count"]
    }

# --- 4. Workflow (The Graph) ---

def route_after_generator(state: GraphState) -> str:
    """
    Determines where to go after Generator.
    Logic:
    1. If Simulation Enabled AND No Research Report -> Researcher
    2. If Critic Enabled -> Critic
    3. Else -> END
    """
    research_report = state.get("research_report")
    enable_simulation = state.get("enable_simulation", True) # Default True for backward compatibility
    enable_critic = state.get("enable_critic", True)         # Default True
    
    # If Simulation is enabled, we MUST do research first (unless already done for this cycle)
    # Note: generator_node clears research_report on new iteration, so this works for loops too.
    if enable_simulation and research_report is None:
        return "researcher"
        
    # If we have research (or sim disabled), check if we want critique
    if enable_critic:
        return "critic"
        
    # If neither (Generation Only), stop
    return "end"

def route_after_analyst(state: GraphState) -> str:
    """
    After analyst, always go back to generator to apply research insights.
    """
    return "generator"

def should_continue(state: GraphState) -> str:
    """
    Determines the next step in the graph.
    """
    critique = state.get("critique")
    iteration = state["iteration_count"]
    max_iterations = state.get("max_iterations", 5)  # Default 5 if not specified
    
    if critique and critique.is_approved:
        return "end"
    
    if iteration >= max_iterations:
        print(f"Max iterations reached ({max_iterations}).")
        return "end"
    
    return "continue"

# Build the graph
workflow = StateGraph(GraphState)

workflow.add_node("generator", generator_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("simulation", simulation_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("critic", critic_node)

workflow.add_edge(START, "generator")

# Conditional edge after generator
workflow.add_conditional_edges(
    "generator",
    route_after_generator,
    {
        "researcher": "researcher",
        "critic": "critic",
        "end": END
    }
)

workflow.add_edge("researcher", "simulation")
workflow.add_edge("simulation", "analyst")
workflow.add_edge("analyst", "generator") # Loop back for Pivot

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "continue": "generator",
        "end": END
    }
)

# Compile the Full Graph
app = workflow.compile()

# --- 5. Main Execution ---

if __name__ == "__main__":
    print("Starting Iterative Idea Validator...")
    
    initial_input = "Uber for walking cats"
    
    initial_state = GraphState(
        initial_input=initial_input,
        current_idea=None,
        critique=None,
        iteration_count=0,
        messages=[]
    )
    
    # Run the graph
    # stream() yields the state updates as they happen
    for output in app.stream(initial_state):
        pass # We are printing inside the nodes for this demo
        
    print("\n--- FINAL STATE ---")
    # Since stream yields updates, we might want to capture the final result differently 
    # or just rely on the prints for this skeleton. 
    # To get the final state object, we can use invoke() instead of stream() if we want the return value.
    
    final_state = app.invoke(initial_state)
    
    if final_state.get("current_idea"):
        print(f"Final Idea Title: {final_state['current_idea'].title}")
        print(f"Final Idea Description: {final_state['current_idea'].description}")
    
    if final_state.get("critique"):
        print(f"Final Score: {final_state['critique'].score}")
        print(f"Approved: {final_state['critique'].is_approved}")
