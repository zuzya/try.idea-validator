import json
import re
import pathlib
from langchain_core.messages import HumanMessage, SystemMessage
from config import (
    llm_generator, llm_critic, llm_fast,
    GENERATOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT, 
    RESEARCHER_SYSTEM_PROMPT, INTERVIEWER_SYSTEM_PROMPT, PERSONA_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT, MOCK_SIMULATION, RECRUITER_ENRICHMENT_PROMPT
)
from models import (
    BusinessIdea, CritiqueFeedback, InterviewGuide, 
    InterviewResult, UserPersona, ResearchReport, RichPersona, TargetPersona,
    PersonaThought, InterviewerThought
)
from google_recruiter import GoogleRecruiter
from google.api_core import retry
import google.generativeai as genai
from state import GraphState
from utils import extract_json_from_text, save_artifact

def generator_node(state: GraphState) -> GraphState:
    print(f"\n--- GENERATOR NODE (Iteration {state['iteration_count']}) ---")
    
    # DEBUG
    rr = state.get("research_report")
    cr = state.get("critique")
    print(f"   -> DEBUG State: Has Research? {rr is not None} | Has Critique? {cr is not None}")
    if rr: print(f"      -> Research: {rr.pivot_recommendation[:50]}...")
    
    current_idea = state.get("current_idea")
    
    user_content = ""
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

    # Select LLM based on mode
    llm = llm_fast if state.get("use_fast_model") else llm_generator
    if state.get("use_fast_model"):
        print("   -> [DEBUG] Using FAST Model (GPT-4o-mini)")

    # --- RETRY & PARSE LOGIC ---
    new_idea = None
    last_error = None
    
    for attempt in range(3):
        try:
            print(f"   -> Invoking LLM (Attempt {attempt + 1})...")
            
            response = llm.invoke(messages)
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

    # --- SAVE ARTIFACT: LEAN CANVAS ---
    lean_canvas_content = f"# Lean Canvas: {new_idea.title}\n\n"
    lean_canvas_content += f"## Problem\nTBD\n\n" # We could expand this if the model returned more
    lean_canvas_content += f"## Solution\n{new_idea.description}\n\n"
    lean_canvas_content += f"## Target Audience\n{new_idea.target_audience}\n\n"
    lean_canvas_content += f"## Monetization\n{new_idea.monetization_strategy}\n\n"
    
    save_artifact(new_idea.title, "lean_canvas.md", lean_canvas_content)
    # ----------------------------------

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
    
    # Select LLM
    llm = llm_fast if state.get("use_fast_model") else llm_critic
    if state.get("use_fast_model"):
        print("   -> [DEBUG] Using FAST Model (GPT-4o-mini) for Critique")
        # Note: structured output might behave differently on Flash, but we try
        structured_llm = llm.with_structured_output(CritiqueFeedback)
    
    try:
        feedback = structured_llm.invoke(messages)
        
        # Validate the response
        if feedback is None:
            raise ValueError("LLM returned None. Check API key and model availability.")
        
        print(f"   -> Verdict: {feedback.is_approved} (Score: {feedback.score}/10)")
        print(f"   -> Key Feedback: {feedback.feedback[:100]}...") # Print preview
        
        # --- SAVE ARTIFACT: CRITIQUE ---
        critique_content = f"# Critique: {current_idea.title}\n\n"
        critique_content += f"## Verdict: {'APPROVED' if feedback.is_approved else 'REJECTED'}\n"
        critique_content += f"**Score:** {feedback.score}/10\n\n"
        critique_content += f"## Feedback\n{feedback.feedback}\n"
        
        save_artifact(current_idea.title, "critique.md", critique_content)
        # -------------------------------
        
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
    
    # Select LLM
    llm = llm_fast if state.get("use_fast_model") else llm_generator
    if state.get("use_fast_model"):
        print("   -> [DEBUG] Using FAST Model (GPT-4o-mini) for Research")

    # 2. Invoke LLM
    # We use the same manual parsing logic as generator_node for stability with Gemini
    interview_guide = None
    last_error = None
    
    for attempt in range(3):
        try:
            print(f"   -> Invoking Researcher (Attempt {attempt + 1})...")
            response = llm.invoke(messages)
            raw_content = response.content
            
            if isinstance(raw_content, list):
                raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
                
            cleaned_json_str = extract_json_from_text(raw_content)
            data_dict = json.loads(cleaned_json_str)
            
            # --- ROBUSTNESS FIX: Auto-fill missing fields for weaker models ---
            if "target_personas" in data_dict:
                for p in data_dict["target_personas"]:
                    if "search_query_en" not in p or not p["search_query_en"]:
                        # Fallback: Construct query from role and context
                        role_en = p.get("role", "Professional") # Simple fallback
                        p["search_query_en"] = f"A {role_en} looking for solutions."
                        print(f"      -> [Patch] Auto-filled missing 'search_query_en' for {p.get('name', '?')}")
                    
                    if "name" not in p:
                        p["name"] = p.get("role", "Generic Persona")
                        
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
        
    save_artifact(current_idea.title, "interview_guide.md", md_content)

    return {
        "interview_guide": interview_guide,
        "iteration_count": state["iteration_count"]
    }

def recruiter_node(state: GraphState) -> GraphState:
    """
    Finds relevant personas using Google Vector Search (Role-based) and "enriches" them.
    """
    print(f"\n--- RECRUITER NODE (Enrichment Mode) ---")
    
    interview_guide = state.get("interview_guide")
    if not interview_guide:
        print("   -> WARNING: No interview guide found. Skipping recruiter.")
        return state
        
    target_personas_specs = interview_guide.target_personas
    rich_personas_list = []
    
    try:
        # 1. Initialize Recruiter
        recruiter = GoogleRecruiter()
        # Ensure we have a model for enrichment
        llm = llm_fast if state.get("use_fast_model") else llm_generator
        
        # Limit the number of personas to interview based on user config
        limit = state.get("num_personas", 3)
        print(f"   -> Limiting selection to first {limit} personas (requested by user).")
        
        # 2. Iterate Strategy
        for i, spec in enumerate(target_personas_specs[:limit], 1):
            print(f"   -> [{i}/{limit}] Hunting for: {spec.role} ({spec.archetype})")
            
            # A. Generate Query
            # We use the specific English search query provided by Researcher for better vector matching
            query = spec.search_query_en
            print(f"      -> Query: {query}")
            
            # B. Search
            found_text = ""
            try:
                # We search for top 3 and pick best match text or just concat top 2
                raw_chunks = recruiter.search_personas(query, limit=3)
                if raw_chunks:
                    found_text = "\n\n".join(raw_chunks)
                    print(f"      -> Found {len(raw_chunks)} candidates in DB.")
                else:
                    print(f"      -> No direct matches in DB. Will rely on synthetic enrichment.")
                    found_text = "No direct match in database. Generate realistic details based on requirements."
            except Exception as e:
                print(f"      -> Search Error: {e}")
                found_text = "Search unavailable."
                
            # C. Enrichment (LLM)
            # We feed the Spec + Found Text -> RichPersona
            
            # Prepare prompts
            enrich_msg = RECRUITER_ENRICHMENT_PROMPT.replace("{target_persona_json}", spec.model_dump_json())
            enrich_msg = enrich_msg.replace("{search_result_text}", found_text[:3000]) # truncated context
            
            messages = [
                SystemMessage(content="You are an expert HR Profiler."),
                HumanMessage(content=enrich_msg)
            ]
            
            try:
                print(f"      -> Enriching profile with LLM...")
                response = llm.invoke(messages)
                cleaned_json = extract_json_from_text(response.content)
                data_dict = json.loads(cleaned_json)
                
                # Check for list vs dict
                if isinstance(data_dict, list):
                   data_dict = data_dict[0] # Take first if array returned
                
                rich_p = RichPersona(**data_dict)
                rich_personas_list.append(rich_p)
                
                print(f"      -> Created RichPersona: {rich_p.name} | {rich_p.company_context}")
                
            except Exception as e:
                print(f"      -> Enrichment Error for {spec.role}: {e}")
                # Fallback: Create semi-synthetic from Spec
                # Note: We miss age/bio etc. but enough to proceed?
                # Actually, better to skip or retry. Let's try to make a minimal one.
                pass

    except Exception as e:
        print(f"   -> Recruiter Critical Error: {e}")
        
    if not rich_personas_list:
        print("   -> Recruiter failed to generate any personas. Using Synthetic fallback downstream.")
        
    return {
        "selected_personas": [p.model_dump() for p in rich_personas_list], # Compatible with state key
        "iteration_count": state["iteration_count"]
    }

def simulation_node(payload: dict) -> dict:
    """
    Simulates ONE user interview. 
    Input payload: {"rich_persona": dict, "interview_guide": InterviewGuide, "current_idea": BusinessIdea, "use_fast_model": bool}
    """
    rich_p_dict = payload.get("rich_persona")
    interview_guide = payload.get("interview_guide")
    current_idea = payload.get("current_idea") # Optional, needed for context? Actually not used heavily inside loop.
    use_fast_model = payload.get("use_fast_model", False)

    if not rich_p_dict:
        print("   -> CRITICAL: No rich persona in payload.")
        return {}

    # Map RichPersona -> TargetPersona
    rich_p = RichPersona(**rich_p_dict)
    print(f"\n--- SIMULATING: {rich_p.name} ({rich_p.role}) ---")

    full_context = (
        f"Bio: {rich_p.bio}\n"
        f"Age: {rich_p.age}\n"
        f"Company: {rich_p.company_context}\n"
        f"Frustrations: {', '.join(rich_p.key_frustrations)}\n"
        f"Tech Stack: {', '.join(rich_p.tech_stack)}\n"
        f"Hidden Constraints: {rich_p.hidden_constraints}"
    )

    p = TargetPersona(
        name=rich_p.name,
        role=rich_p.role,
        archetype=rich_p.psychotype,
        context=full_context,
        search_query_en="N/A (Derived from RichPersona)"
    )

    # Prepare LLMs
    interviewer_llm = llm_fast if use_fast_model else llm_generator
    structured_interviewer = interviewer_llm.with_structured_output(InterviewerThought)
    
    persona_llm = llm_fast 
    structured_persona = persona_llm.with_structured_output(PersonaThought)

    conversation_log = ""
    raw_interviews = []
    
    # MOCK SIMULATION CHECK
    if MOCK_SIMULATION:
        print(f"   -> [MOCK MODE] Skipping real LLM call for {p.name}")
        conversation_log = "### Interview (MOCK)\nMock transcript content..."
        result = InterviewResult(
            persona=UserPersona(name=p.name, role=p.role, background=f"{p.archetype}: {p.context}"),
            transcript_summary=f"Пользователь {p.name} (Parallel Mock) говорит, что идея норм.",
            pain_level=7,
            willingness_to_pay=4
        )
        # Create Log Markup
        transcript_markdown = f"## Interview Summary: {p.name}\n"
        transcript_markdown += f"**Role:** {p.role}\n**Pain:** 7/10\n**WTP:** 4/10\n\n### Transcript\n{conversation_log}\n---\n\n"
        
        return {
            "raw_interviews": [result],
            "interview_transcripts": [transcript_markdown]
        }

    # --- TURN-BY-TURN LOOP ---
    history = []
    
    conversation_log += f"### Interview with {p.name}\n"
    conversation_log += f"**Role**: {p.role} | **Archetype**: {p.archetype}\n"
    conversation_log += f"**Context**: {p.context[:200]}...\n\n"
    
    MAX_TURNS = 10
    patience = 100
    next_question = interview_guide.questions[0]
    
    for turn in range(MAX_TURNS):
        # 1. PERSONA AGENT
        persona_prompt = f"""
        CURRENT SITUATION:
        Interviewer (AI) asked: "{next_question}"
        
        YOUR PATIENCE: {patience}/100
        
        DIALOGUE HISTORY:
        {[h['content'] for h in history[-3:]]} 
        """
        
        persona_messages = [
            SystemMessage(content=PERSONA_SYSTEM_PROMPT.format(persona_context=p.context)),
            HumanMessage(content=persona_prompt)
        ]
        
        try:
            persona_thought = structured_persona.invoke(persona_messages)
        except Exception as e:
            print(f"      -> [Persona Error] {e}")
            persona_thought = PersonaThought(mood="Confused", patience=patience-10, inner_monologue="Error", verbal_response="Could you repeat that?")
        
        # Update state
        patience = persona_thought.patience
        history.append({"role": "interviewer", "content": next_question})
        history.append({"role": "respondent", "content": persona_thought.verbal_response})
        
        # Log
        conversation_log += f"**Interviewer**: {next_question}\n"

        personas_response_text = persona_thought.verbal_response
        conversation_log += f"\n**{p.name}:** {personas_response_text} *(Mood: {persona_thought.mood})*\n> Inner: {persona_thought.inner_monologue}\n"

        print(f"      [{turn+1}/{MAX_TURNS}] {p.name}: {persona_thought.verbal_response[:50]}...")
        
        if persona_thought.patience < 10:
            conversation_log += "\n*(Respondent ended the interview due to low patience)*\n"
            break

        # 2. INTERVIEWER AGENT
        interviewer_prompt = f"""
        respondent_message: "{personas_response_text}"
        conversation_so_far: {history[-4:]}
        """
        
        interviewer_messages = [
            SystemMessage(content=INTERVIEWER_SYSTEM_PROMPT.format(
                interview_guide=str(interview_guide.questions),
                history=str(history[-3:])
            )),
            HumanMessage(content=interviewer_prompt)
        ]
        
        try:
            interviewer_thought = structured_interviewer.invoke(interviewer_messages)
            next_question = interviewer_thought.next_question
            
            if interviewer_thought.status == "WRAP_UP":
                print("      -> Interviewer decided to wrap up.")
                conversation_log += "\n*(Interviewer wrapped up the session)*\n"
                break
        except Exception as e:
            print(f"      -> [Interviewer Error] {e}")
            interviewer_thought = InterviewerThought(analysis="Error", next_question="Thank you", status="WRAP_UP")
            break
            
    # --- FINAL SUMMARY ---
    summary_prompt = f"""
    ANALYZE THIS INTERVIEW TRANSCRIPT:
    {conversation_log[:15000]}
    
    Based on the respondent's INNER THOUGHTS and verbal answers, fill this strict JSON:
    REQUIRED JSON STRUCTURE:
    {{
        "transcript_summary": "String: Key insights and summary of the conversation",
        "pain_level": Int (1-10),
        "willingness_to_pay": Int (1-10)
    }}
    Do not use keys like 'pain_score'. Use 'pain_level'.
    """
    
    try:
        print(f"      -> Generating summary for {p.name}...")
        summary_llm = llm_fast if use_fast_model else llm_generator
        summary_response = summary_llm.invoke([HumanMessage(content=summary_prompt)])
        raw_content = summary_response.content
        if isinstance(raw_content, list):
            raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
        
        cleaned_json = extract_json_from_text(raw_content)
        data_dict = json.loads(cleaned_json)
        
        # Patches
        if "pain_level" not in data_dict and "pain_score" in data_dict: data_dict["pain_level"] = data_dict["pain_score"]
        if "willingness_to_pay" not in data_dict and "pay_score" in data_dict: data_dict["willingness_to_pay"] = data_dict["pay_score"]

        final_data = {
            "persona": {
                "name": p.name,
                "role": p.role,
                "background": p.context[:200]
            },
            "transcript_summary": data_dict.get("transcript_summary", "No summary received"),
            "full_transcript": conversation_log,
            "pain_level": int(data_dict.get("pain_level", 0)),
            "willingness_to_pay": int(data_dict.get("willingness_to_pay", 0))
        }
        
        result = InterviewResult(**final_data)
        
        # Prepare Markdown Transcript Chunk
        transcript_markdown = f"## Interview Summary: {p.name}\n"
        transcript_markdown += f"**Role:** {p.role}\n**Pain:** {result.pain_level}/10\n**WTP:** {result.willingness_to_pay}/10\n\n"
        transcript_markdown += f"### Summary\n{result.transcript_summary}\n\n"
        transcript_markdown += f"### Full Transcript\n{conversation_log}\n---\n\n"
        
        return {
            "raw_interviews": [result],
            "interview_transcripts": [transcript_markdown]
        }
        
    except Exception as e:
        print(f"   -> CRITICAL SUMMARY ERROR for {p.name}: {e}")
        return {}

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
    
    # Select LLM
    llm = llm_fast if state.get("use_fast_model") else llm_generator
    if state.get("use_fast_model"):
        print("   -> [DEBUG] Using FAST Model (GPT-4o-mini) for Analysis")

    # 2. Invoke LLM (Gemini 3 Pro)
    research_report = None
    try:
        response = llm.invoke(messages)
        raw_content = response.content
        
        if isinstance(raw_content, list):
            raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
            
        cleaned_json_str = extract_json_from_text(raw_content)
        data_dict = json.loads(cleaned_json_str)
        research_report = ResearchReport(**data_dict)
        
        print(f"   -> Pivot Recommendation: {research_report.pivot_recommendation[:100]}...")
        
        # 3. File Persistence
        md_content = f"# Research Report: {current_idea.title}\n\n"
        md_content += "## ✅ Confirmed Hypotheses\n"
        for h in research_report.confirmed_hypotheses:
            md_content += f"- {h}\n"
        md_content += "\n## ❌ Rejected Hypotheses\n"
        for h in research_report.rejected_hypotheses:
            md_content += f"- {h}\n"
        md_content += "\n## 💡 Key Insights\n"
        for h in research_report.key_insights:
            md_content += f"- {h}\n"
        md_content += f"\n## 🔄 Pivot Recommendation\n{research_report.pivot_recommendation}\n"
        
        save_artifact(current_idea.title, "research_report.md", md_content)
        
        # 4. Save Aggregated Transcripts (from Parallel Simulations)
        interview_transcripts = state.get("interview_transcripts", [])
        if interview_transcripts:
            final_transcript_md = f"# User Interviews: {current_idea.title}\n\n"
            for chunk in interview_transcripts:
                final_transcript_md += chunk
            save_artifact(current_idea.title, "interviews_transcript.md", final_transcript_md)
            print("   -> Saved aggregated transcripts.")
        
    except Exception as e:
        print(f"   -> Analyst Error: {e}")
    
    # Increment interview cycle counter
    current_cycle = state.get("current_interview_cycle", 0)
    new_cycle = current_cycle + 1
    print(f"   -> Interview Cycle: {current_cycle} -> {new_cycle}")
        
    return {
        "research_report": research_report,
        "iteration_count": state["iteration_count"],
        "current_interview_cycle": new_cycle
    }
