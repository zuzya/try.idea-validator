from langgraph.graph import END, StateGraph, START
from dotenv import load_dotenv
import os

from state import GraphState
from nodes import (
    generator_node, researcher_node, 
    simulation_node, analyst_node, critic_node,
    recruiter_node
)
from models import BusinessIdea

load_dotenv()

# --- Workflow Routing Logic ---

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

# --- Build the Graph ---

workflow = StateGraph(GraphState)

workflow.add_node("generator", generator_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("recruiter", recruiter_node)
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

workflow.add_edge("researcher", "recruiter")
workflow.add_edge("recruiter", "simulation")
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

# --- Main Execution (CLI Test) ---

if __name__ == "__main__":
    print("Starting Iterative Idea Validator (Refactored)...")
    
    initial_input = "Uber for walking cats"
    
    initial_state = GraphState(
        initial_input=initial_input,
        current_idea=None,
        critique=None,
        iteration_count=0,
        messages=[],
        enable_simulation=True,
        enable_critic=True,
        max_iterations=2,
        mode="full",
        research_report=None,
        interview_guide=None,
        raw_interviews=[]
    )
    
    # Run the graph
    for output in app.stream(initial_state):
        pass 
        
    print("\n--- FINAL STATE ---")
    final_state = app.invoke(initial_state)
    
    if final_state.get("current_idea"):
        print(f"Final Idea Title: {final_state['current_idea'].title}")
        print(f"Final Idea Description: {final_state['current_idea'].description}")
    
    if final_state.get("critique"):
        print(f"Final Score: {final_state['critique'].score}")
        print(f"Approved: {final_state['critique'].is_approved}")
