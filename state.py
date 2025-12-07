from typing import TypedDict, List, Optional, Literal, Annotated
import operator
from langchain_core.messages import BaseMessage
from models import BusinessIdea, InterviewGuide, InterviewResult, ResearchReport, CritiqueFeedback

class GraphState(TypedDict):
    initial_input: str
    current_idea: Optional[BusinessIdea]
    
    # --- Research Fields (Synthetic CustDev) ---
    interview_guide: Optional[InterviewGuide]  # Скрипт и гипотезы
    
    # Reducible fields for Parallel Execution (Map-Reduce)
    raw_interviews: Annotated[List[InterviewResult], operator.add]      # Результаты каждого "звонка"
    interview_transcripts: Annotated[List[str], operator.add]           # Полные логи диалогов (Markdown chunks) for artifact generation
    
    selected_personas: List[dict] = []         # Персоны от рекрутера (RichPersona objects as dicts)
    research_report: Optional[ResearchReport]  # Analyst output
    # -------------------------------------------
    
    critique: Optional[CritiqueFeedback]
    iteration_count: int
    messages: List[BaseMessage]  # Optional, but good for history
    max_iterations: int  # Add configurable max iterations
    mode: Literal["full", "research_only"] # New field for mode selection
    
    # --- Configuration Flags ---
    enable_simulation: bool
    enable_critic: bool
    use_fast_model: bool # Debug mode flag
    num_personas: int # Number of interviews to run (1-3)
    interview_iterations: int # How many interview cycles before going to critic (default 1)
    current_interview_cycle: int # Current cycle counter (starts at 0, incremented by analyst)
