from typing import TypedDict, List, Optional, Literal
from langchain_core.messages import BaseMessage
from models import BusinessIdea, InterviewGuide, InterviewResult, ResearchReport, CritiqueFeedback

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
    use_fast_model: bool # Debug mode flag
