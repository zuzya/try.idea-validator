import os
from typing import TypedDict, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from config import llm_generator, llm_critic

# --- 1. State Definition ---

class InterviewState(TypedDict):
    messages: List[BaseMessage]
    researcher_guide: str
    user_persona: str
    user_hidden_context: str
    step_count: int
    max_steps: int

# --- 2. Prompts ---

RESEARCHER_INSTRUCTION = """
Ты — Senior UX Researcher. Твоя задача — провести проблемное интервью (CustDev) с пользователем.
У тебя есть ГАЙД (цель и вопросы), которому ты должен следовать.

ТВОЯ СТРАТЕГИЯ:
1. Задавай по ОДНОМУ вопросу за раз. Не перегружай пользователя.
2. Слушай ответы. Если пользователь сказал что-то интересное — копай глубже ("Почему?", "Расскажите подробнее").
3. Не продавай идею. Твоя цель — узнать правду о боли пользователя.
4. Будь вежлив, но профессионален.

ГАЙД ИНТЕРВЬЮ:
{guide}

КОГДА ЗАКАНЧИВАТЬ:
- Если ты задал все важные вопросы и получил ответы.
- Если пользователь явно не целевой или не хочет говорить.
- В этом случае напиши ТОЛЬКО одно слово: FINISHED
"""

USER_INSTRUCTION = """
Ты — Респондент на интервью. Твоя задача — отвечать на вопросы исследователя.

ТВОЯ ПЕРСОНА (КТО ТЫ):
{persona}

ТВОЙ СКРЫТЫЙ КОНТЕКСТ (ЧТО ТЫ ДУМАЕШЬ НА САМОМ ДЕЛЕ):
{hidden_context}

КАК ОТВЕЧАТЬ:
1. Будь естественным. Используй разговорный русский язык.
2. Не будь "полезным AI-ассистентом". Будь человеком. Можешь сомневаться, отвечать кратко, если тебе не интересно.
3. Опирайся СТРОГО на свой контекст. Если у тебя нет денег — так и скажи. Если ты ненавидишь новые технологии — скажи это.
4. Не придумывай факты, противоречащие твоей персоне.
"""

# --- 3. Nodes ---

def researcher_node(state: InterviewState) -> InterviewState:
    print(f"   [Researcher] Thinking... (Step {state['step_count']})")
    
    messages = state["messages"]
    guide = state["researcher_guide"]
    
    system_msg = SystemMessage(content=RESEARCHER_INSTRUCTION.format(guide=guide))
    
    # Filter messages to ensure we don't feed system prompts into the history incorrectly if needed,
    # but here we just append the system prompt to the current history for the LLM call.
    # Note: We don't save the system prompt to the state history, only the conversation.
    
    prompt = [system_msg] + messages
    
    response = llm_generator.invoke(prompt)
    
    return {
        "messages": [response],
        "step_count": state["step_count"] + 1
    }

def user_node(state: InterviewState) -> InterviewState:
    print(f"   [User] Thinking...")
    
    messages = state["messages"]
    persona = state["user_persona"]
    hidden_context = state["user_hidden_context"]
    
    system_msg = SystemMessage(content=USER_INSTRUCTION.format(
        persona=persona, 
        hidden_context=hidden_context
    ))
    
    prompt = [system_msg] + messages
    
    response = llm_critic.invoke(prompt)
    
    return {
        "messages": [response]
    }

# --- 4. Logic & Routing ---

def should_continue(state: InterviewState) -> Literal["user", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if Researcher said FINISHED
    if isinstance(last_message, AIMessage):
        if "FINISHED" in last_message.content:
            return "end"
            
    # Check max steps
    if state["step_count"] >= state["max_steps"]:
        print("   [System] Max steps reached.")
        return "end"
        
    return "user"

# --- 5. Graph Construction ---

workflow = StateGraph(InterviewState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("user", user_node)

workflow.add_edge(START, "researcher")

workflow.add_conditional_edges(
    "researcher",
    should_continue,
    {
        "user": "user",
        "end": END
    }
)

workflow.add_edge("user", "researcher")

simulation_app = workflow.compile()

# --- 6. Test Execution ---

if __name__ == "__main__":
    print("--- STARTING SIMULATION SUBGRAPH TEST ---")
    
    test_guide = """
    Цель: Узнать, как бухгалтеры справляются с рутиной.
    Вопросы:
    1. Расскажите, как проходит ваш типичный рабочий день?
    2. Что отнимает больше всего времени?
    3. Пробовали ли вы автоматизировать ввод первички?
    """
    
    test_persona = """
    Имя: Татьяна Ивановна.
    Возраст: 52 года.
    Роль: Главный бухгалтер в строительной фирме.
    """
    
    test_context = """
    Я очень устала от работы. У меня плохое зрение. 
    Я не доверяю облачным сервисам, потому что боюсь утечки данных.
    Денег у фирмы нет, директор экономит на всем.
    """
    
    initial_state = InterviewState(
        messages=[],
        researcher_guide=test_guide,
        user_persona=test_persona,
        user_hidden_context=test_context,
        step_count=0,
        max_steps=6
    )
    
    for event in simulation_app.stream(initial_state):
        for key, value in event.items():
            if "messages" in value:
                last_msg = value["messages"][-1]
                sender = "Researcher" if key == "researcher" else "User"
                print(f"\n{sender}: {last_msg.content}")
                
    print("\n--- SIMULATION FINISHED ---")
