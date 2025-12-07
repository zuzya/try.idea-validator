import json
import re
import pathlib
from langchain_core.messages import HumanMessage, SystemMessage
from config import (
    llm_generator, llm_critic, llm_fast,
    GENERATOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT, 
    RESEARCHER_SYSTEM_PROMPT, INTERVIEWER_SYSTEM_PROMPT, PERSONA_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT, MOCK_SIMULATION
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
        print("   -> [DEBUG] Using FAST Model (Gemini Flash)")

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
        print("   -> [DEBUG] Using FAST Model (Gemini Flash) for Critique")
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
        critique_content += f"**Score:** {feedback.score}/100\n\n"
        critique_content += f"## Feedback\n{feedback.feedback}\n\n"
        critique_content += f"## Strategic Advice\n{feedback.strategic_advice}\n"
        
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
        print("   -> [DEBUG] Using FAST Model (Gemini Flash) for Research")

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
    Finds relevant personas using Google Vector Search and selects the best ones.
    """
    print(f"\n--- RECRUITER NODE ---")
    
    current_idea = state["current_idea"]
    startup_idea = f"{current_idea.title}: {current_idea.description}"
    
    selected_personas = []
    
    try:
        # 1. Initialize Recruiter
        recruiter = GoogleRecruiter()
        
        # 2. Search
        print(f"   -> Searching for personas relevant to: {current_idea.title}...")
        raw_chunks = recruiter.search_personas(startup_idea, limit=10)
        
        if not raw_chunks:
            print("   -> WARNING: No personas found via Recruiter. Will fall back to synthetic personas.")
            return state
            
        context_text = "\n\n".join([f"Persona {i+1}:\n{chunk}" for i, chunk in enumerate(raw_chunks)])
        
        # 3. Parse and Select with Gemini
        # We use the fast model or generator model
        llm = llm_fast if state.get("use_fast_model") else llm_generator
        
        # Use structured output if possible, or manual parsing
        # Manual parsing is safer with Gemini sometimes
        
        selection_prompt = f"""
        Here is the description of a startup idea: "{startup_idea}"
        
        Here are {len(raw_chunks)} potential candidate profiles found in our database:
        
        {context_text}
        
        Your Task:
        1. Analyze these profiles.
        2. Select exactly 3 BEST target users (most likely to buy/use) and 1 TOUGH CRITIC (skeptical/challenging).
        3. Extract their details and format them into the required JSON structure.
        4. For the 'attitude' field, label the critic as 'Critical' or 'Skeptical'.
        5. For 'original_text', include the relevant excerpt from the source.
        
        CRITICAL: Return ONLY a valid JSON list of objects.
        Format:
        [
          {{
            "name": "Name",
            "role": "Role",
            "background": "Background details",
            "attitude": "Enthusiastic/Critical",
            "original_text": "Original text snippet"
          }}
        ]
        """
        
        messages = [
            SystemMessage(content="You are an expert Recruiter."),
            HumanMessage(content=selection_prompt)
        ]
        
        print(f"   -> [Recruiter] Selecting best candidates form {len(raw_chunks)} chunks...")
        response = llm.invoke(messages)
        
        cleaned_json = extract_json_from_text(response.content)
        data_list = json.loads(cleaned_json)
        
        selected_personas = [RichPersona(**p) for p in data_list]
        
        print(f"   -> [Recruiter] Selected {len(selected_personas)} personas from database:")
        for i, p in enumerate(selected_personas, 1):
            print(f"      {i}. {p.name} ({p.role})")
            print(f"         Attitude: {p.attitude}")
            print(f"         Background: {p.background[:100]}...")
            
    except Exception as e:
        print(f"   -> Recruiter Error: {e}")
        print("   -> Continuing with synthetic personas only.")
        
    return {
        "selected_personas": [p.model_dump() for p in selected_personas], # Store as dicts in state
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
    
    # Get personas from Recruiter (priority) or Researcher (fallback)
    selected_personas_dicts = state.get("selected_personas", [])
    
    personas_to_interview = []
    
    if selected_personas_dicts:
        print(f"   -> Using {len(selected_personas_dicts)} personas from RECRUITER (Real Data)")
        # Convert dicts back to objects for easier handling, or just use dicts
        for p_dict in selected_personas_dicts:
            # Map RichPersona to TargetPersona structure for simulation
            # RichPersona: name, role, background, attitude, original_text
            # TargetPersona: name, role, archetype, context
            
            # We enrich the context with the background and original text
            rich_p = RichPersona(**p_dict)
            
            # Create a TargetPersona object for the simulation loop
            target_p = TargetPersona(
                name=rich_p.name,
                role=rich_p.role,
                archetype=rich_p.attitude,
                context=f"{rich_p.background}. {rich_p.original_text[:300]}..."
            )
            
            personas_to_interview.append(target_p)
            
    else:
        print("   -> Using synthetic personas from RESEARCHER")
        personas_to_interview = interview_guide.target_personas

    if not personas_to_interview:
        print("   -> CRITICAL: No personas to interview.")
        return state
    
    print(f"   -> Found {len(personas_to_interview)} personas to interview")
    
    # Loop & Simulate
    raw_interviews = []

    # Loop & Simulate
    raw_interviews = []
    full_transcript_logs = [] # Store (name, transcript_text)

    # Prepare LLMs
    # Interviewer: Use Fast model (Gemini Flash) or Generator (Pro)
    interviewer_llm = llm_fast if state.get("use_fast_model") else llm_generator
    structured_interviewer = interviewer_llm.with_structured_output(InterviewerThought)
    
    # Persona: Always use Fast model (Gemini Flash) for speed in loop
    persona_llm = llm_fast 
    structured_persona = persona_llm.with_structured_output(PersonaThought)

    for p in personas_to_interview:
        print(f"   -> Simulating interview with {p.name} ({p.role})...")
        
        conversation_log = "" # For artifact
        
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
            full_transcript_logs.append((p.name, "Mock Transcript"))
            continue
        
        # --- TURN-BY-TURN LOOP ---
        history = []
        
        # Initial greeting / context
        conversation_log += f"### Interview with {p.name}\n"
        conversation_log += f"**Role**: {p.role} | **Archetype**: {p.archetype}\n"
        conversation_log += f"**Context**: {p.context[:200]}...\n\n"
        
        MAX_TURNS = 10
        patience = 100
        
        # Initial Question from Guide
        next_question = interview_guide.questions[0]
        
        for turn in range(MAX_TURNS):
            # 1. PERSONA AGENT
            # Formulate Persona Prompt
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
            
            # Log to artifact
            conversation_log += f"**Interviewer**: {next_question}\n"
            conversation_log += f"**{p.name} (Thought)**: *{persona_thought.inner_monologue}* (Mood: {persona_thought.mood})\n"
            conversation_log += f"**{p.name} (Said)**: {persona_thought.verbal_response}\n\n"
            
            print(f"      [{turn+1}/{MAX_TURNS}] {p.name}: {persona_thought.verbal_response[:50]}... (Mood: {persona_thought.mood})")
            
            # Check exit conditions
            if patience < 10:
                print("      -> Persona lost patience. Ending.")
                conversation_log += "\n*(Interview ended early due to low patience)*\n"
                break
                
            # 2. INTERVIEWER AGENT
            # Decide next move
            interviewer_prompt = f"""
            LAST RESPONSE: "{persona_thought.verbal_response}"
            
            Analyze the response. Is it honest? Do we need to dig deeper?
            Decide the next question based on the guide: {interview_guide.questions}
            """
            
            interviewer_messages = [
                SystemMessage(content=INTERVIEWER_SYSTEM_PROMPT.format(interview_guide=interview_guide.model_dump_json(), history=history[-5:])),
                HumanMessage(content=interviewer_prompt)
            ]
            
            try:
                interviewer_app = structured_interviewer.invoke(interviewer_messages)
                next_question = interviewer_app.next_question
                
                if interviewer_app.status == "WRAP_UP":
                    print("      -> Interviewer decided to wrap up.")
                    conversation_log += "\n*(Interviewer wrapped up the session)*\n"
                    break
            except Exception as e:
                print(f"      -> [Interviewer Error] {e}")
                break
                
        # --- END LOOP ---
        
        # Store full log
        full_transcript_logs.append((p.name, conversation_log))
        
        # 3. FINAL SUMMARY (Meta-Analysis)
        # We ask the Analyst model to summarize this specific interview based on the FULL logs
        summary_prompt = f"""
        ANALYZE THIS INTERVIEW TRANSCRIPT:
        {conversation_log}
        
        Based on the respondent's INNER THOUGHTS and verbal answers:
        1. How much pain do they really feel? (1-10)
        2. Would they actually pay? (1-10)
        3. Summarize the key insights.
        
        Return STRICT JSON (InterviewResult schema).
        """
        
        try:
            # Re-use extract_json_from_text logic with Generator model for better reasoning
            summary_response = llm_generator.invoke([HumanMessage(content=summary_prompt)])
            
            raw_content = summary_response.content
            # Handle Gemini's list output
            if isinstance(raw_content, list):
                raw_content = "".join([b.get("text", "") for b in raw_content if isinstance(b, dict)])
            
            cleaned_json = extract_json_from_text(raw_content)
            data_dict = json.loads(cleaned_json)
            
            # Fix nested objects if any
            if "persona" not in data_dict:
                 data_dict["persona"] = {}
            data_dict["persona"]["name"] = p.name
            data_dict["persona"]["role"] = p.role
            data_dict["persona"]["background"] = p.context[:100]

            result = InterviewResult(**data_dict)
            raw_interviews.append(result)
            
        except Exception as e:
            print(f"   -> Summary Error for {p.name}: {e}")

    # --- SAVE ARTIFACT: TRANSCRIPTS ---
    if raw_interviews:
        # Build the final big markdown file
        final_md = f"# User Interviews: {current_idea.title}\n\n"
        
        # We iterate through results, and find matching log
        # Since order is preserved (raw_interviews and full_transcript_logs have same order/length usually)
        # We will loop by index
        for i, result in enumerate(raw_interviews):
            final_md += f"## Interview Summary: {result.persona.name}\n"
            final_md += f"**Role:** {result.persona.role}\n"
            final_md += f"**Pain Level:** {result.pain_level}/10\n"
            final_md += f"**Willingness to Pay:** {result.willingness_to_pay}/10\n\n"
            final_md += f"### Summary\n{result.transcript_summary}\n\n"
            
            # Find matching log
            log_text = ""
            if i < len(full_transcript_logs):
                 # Verify name match just in case
                 if full_transcript_logs[i][0] == result.persona.name:
                     log_text = full_transcript_logs[i][1]
            
            final_md += f"### Full Transcript (Turn-by-Turn)\n"
            final_md += f"{log_text}\n"
            final_md += "---\n\n"
            
        save_artifact(current_idea.title, "interviews_transcript.md", final_md)
    # ----------------------------------

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
    
    # Select LLM
    llm = llm_fast if state.get("use_fast_model") else llm_generator
    if state.get("use_fast_model"):
        print("   -> [DEBUG] Using FAST Model (Gemini Flash) for Analysis")

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
        
    except Exception as e:
        print(f"   -> Analyst Error: {e}")
        
    return {
        "research_report": research_report,
        "iteration_count": state["iteration_count"]
    }
