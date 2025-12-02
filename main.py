import operator
from typing import Annotated, List, Optional, TypedDict, Union

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph, START
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from config import llm_generator, llm_critic, llm_router, GENERATOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT
import time
import json
import re

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

# --- 2. Graph State ---

class GraphState(TypedDict):
    initial_input: str
    current_idea: Optional[BusinessIdea]
    critique: Optional[CritiqueFeedback]
    iteration_count: int
    messages: List[BaseMessage] # Optional, but good for history
    max_iterations: int # Add configurable max iterations

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
    ВАЖНО: Твой ответ должен быть СТРОГО валидным JSON объектом.
    Без Markdown, без слов "Вот JSON", без кавычек ```json.
    
    Формат JSON:
    {
      "title": "Название стартапа (String)",
      "description": "Суть продукта и ценность (String)",
      "monetization_strategy": "Модель заработка (String)",
      "target_audience": "Целевая аудитория (String)"
    }
    """
    
    if state["iteration_count"] == 0:
        print(">> Generating initial ZERO-TO-ONE concept...")
        user_content = f"""
        USER INPUT: '{state['initial_input']}'
        
        Task: Synthesize a Unicorn startup concept for the RUSSIAN MARKET (2025).
        {schema_instruction}
        """
    else:
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
            # print(f"   -> Raw Output causing error: {raw_content[:200]}...") 
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

    return {
        "current_idea": new_idea,
        "iteration_count": state["iteration_count"] + 1
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

# --- 4. Workflow (The Graph) ---

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
workflow.add_node("critic", critic_node)

workflow.add_edge(START, "generator")
workflow.add_edge("generator", "critic")

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "continue": "generator",
        "end": END
    }
)

# Compile the graph
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
