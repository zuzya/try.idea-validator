import operator
from typing import Annotated, List, Optional, TypedDict, Union

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph, START
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
from config import llm_generator, llm_critic, llm_router, GENERATOR_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT

load_dotenv()

# --- 1. Data Structures (Pydantic Models) ---

class BusinessIdea(BaseModel):
    title: str = Field(description="The name of the business idea")
    description: str = Field(description="A detailed description of the idea")
    monetization_strategy: str = Field(description="How the business will make money")
    target_audience: str = Field(description="Who the product is for")

class CritiqueFeedback(BaseModel):
    is_approved: bool = Field(description="Whether the idea is ready for launch")
    feedback: str = Field(description="Actionable advice for improvement")
    score: int = Field(description="Rating from 1-10", ge=1, le=10)

# --- 2. Graph State ---

class GraphState(TypedDict):
    initial_input: str
    current_idea: Optional[BusinessIdea]
    critique: Optional[CritiqueFeedback]
    iteration_count: int
    messages: List[BaseMessage] # Optional, but good for history

# --- 3. Nodes & Logic ---

def generator_node(state: GraphState) -> GraphState:
    """
    Generates or refines a business idea using Gemini 3 Pro (Visionary).
    """
    print(f"\n--- GENERATOR NODE (Iteration {state['iteration_count']}) ---")
    
    # 1. Bind Structured Output
    structured_llm = llm_generator.with_structured_output(BusinessIdea)
    
    # 2. Construct the User Message based on state
    if state["iteration_count"] == 0:
        print(">> Generating initial ZERO-TO-ONE concept...")
        user_content = f"""
        USER INPUT: '{state['initial_input']}'
        
        Task: Synthesize a Unicorn startup concept based on late 2025 trends.
        """
    else:
        print(">> PIVOTING based on Critique...")
        # We need to serialize the objects to string for the prompt
        current_json = state["current_idea"].model_dump_json(indent=2)
        critique_json = state["critique"].model_dump_json(indent=2)
        
        user_content = f"""
        CRITIQUE RECEIVED. YOU MUST ITERATE OR PIVOT.
        
        PREVIOUS IDEA VERSION:
        {current_json}
        
        CRITIC FEEDBACK (GPT-5.1):
        {critique_json}
        
        INSTRUCTIONS:
        1. Address the 'fatal_flaws' or specific feedback points.
        2. If the Unit Economics were rejected, change the monetization model.
        3. If the Moat was weak, invent a technical advantage.
        """

    # 3. Invoke LLM with the Powerful System Prompt
    messages = [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    new_idea = structured_llm.invoke(messages)
    
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
    
    feedback = structured_llm.invoke(messages)
    
    print(f"   -> Verdict: {feedback.is_approved} (Score: {feedback.score}/10)")
    print(f"   -> Key Feedback: {feedback.feedback[:100]}...") # Print preview
        
    return {"critique": feedback}

# --- 4. Workflow (The Graph) ---

def should_continue(state: GraphState) -> str:
    """
    Determines the next step in the graph.
    """
    critique = state.get("critique")
    iteration = state["iteration_count"]
    MAX_ITERATIONS = 5
    
    if critique and critique.is_approved:
        return "end"
    
    if iteration >= MAX_ITERATIONS:
        print("Max iterations reached.")
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
