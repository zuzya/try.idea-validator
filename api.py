"""
FastAPI Backend for AI Unicorn Validator
Replaces Streamlit with SSE-based real-time streaming
"""
import asyncio
import json
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from main import app as graph_app
from models import BusinessIdea


class ValidationRequest(BaseModel):
    idea: str
    max_iterations: int = 5
    num_personas: int = 3
    interview_iterations: int = 1
    mock_simulation: bool = False
    enable_simulation: bool = True
    enable_critic: bool = True
    use_fast_model: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    print("🚀 AI Unicorn Validator API starting...")
    yield
    print("👋 API shutting down...")


app = FastAPI(
    title="AI Unicorn Validator API",
    description="Validate startup ideas with AI agents",
    version="3.0.0",
    lifespan=lifespan
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_event(event_type: str, data: dict) -> str:
    """Format event for SSE."""
    json_data = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n"


async def stream_validation(request: ValidationRequest) -> AsyncGenerator[str, None]:
    """Stream LangGraph events as SSE."""
    import os
    
    # Set mock mode
    os.environ["MOCK_SIMULATION"] = "true" if request.mock_simulation else "false"
    
    initial_state = {
        "initial_input": request.idea,
        "iteration_count": 0,
        "max_iterations": request.max_iterations,
        "mode": "full",
        "messages": [],
        "enable_simulation": request.enable_simulation,
        "enable_critic": request.enable_critic,
        "use_fast_model": request.use_fast_model,
        "num_personas": request.num_personas,
        "interview_iterations": request.interview_iterations,
        "current_interview_cycle": 0
    }
    
    yield serialize_event("start", {"message": "Validation started", "idea": request.idea})
    
    try:
        event_count = 0
        
        for event in graph_app.stream(
            initial_state, 
            config={"recursion_limit": request.max_iterations * 2 + 10}
        ):
            event_count += 1
            event_keys = list(event.keys())
            node_name = event_keys[0] if event_keys else "unknown"
            
            print(f"   [API] Event #{event_count}: {node_name}")
            
            # Process each node type
            if "generator" in event:
                state = event["generator"]
                idea = state.get("current_idea")
                if idea:
                    yield serialize_event("generator", {
                        "iteration": state.get("iteration_count", 0),
                        "idea": {
                            "title": idea.title,
                            "description": idea.description,
                            "monetization_strategy": idea.monetization_strategy,
                            "target_audience": idea.target_audience
                        }
                    })
            
            elif "researcher" in event:
                state = event["researcher"]
                guide = state.get("interview_guide")
                if guide:
                    yield serialize_event("researcher", {
                        "personas": [
                            {"name": p.name, "role": p.role, "archetype": p.archetype, "context": p.context}
                            for p in guide.target_personas
                        ],
                        "hypotheses": [
                            {"type": h.type, "description": h.description}
                            for h in guide.hypotheses_to_test
                        ],
                        "questions": guide.questions
                    })
            
            elif "recruiter" in event:
                state = event["recruiter"]
                personas = state.get("selected_personas", [])
                if personas:
                    yield serialize_event("recruiter", {
                        "personas": [
                            {
                                "name": p.get("name", "Unknown"),
                                "role": p.get("role", "Unknown"),
                                "bio": p.get("bio", ""),
                                "company_context": p.get("company_context", ""),
                                "key_frustrations": p.get("key_frustrations", []),
                                "tech_stack": p.get("tech_stack", [])
                            }
                            for p in personas
                        ]
                    })
            
            elif "simulation" in event:
                state = event["simulation"]
                interviews = state.get("raw_interviews", [])
                if interviews:
                    yield serialize_event("simulation", {
                        "interviews": [
                            {
                                "persona": {
                                    "name": getattr(i.persona, "name", "Unknown"),
                                    "role": getattr(i.persona, "role", "Unknown")
                                },
                                "pain_level": i.pain_level,
                                "willingness_to_pay": i.willingness_to_pay,
                                "transcript_summary": i.transcript_summary,
                                "full_transcript": getattr(i, "full_transcript", "")
                            }
                            for i in interviews
                        ]
                    })
            
            elif "analyst" in event:
                state = event["analyst"]
                report = state.get("research_report")
                if report:
                    yield serialize_event("analyst", {
                        "key_insights": report.key_insights,
                        "confirmed_hypotheses": report.confirmed_hypotheses,
                        "rejected_hypotheses": report.rejected_hypotheses,
                        "pivot_recommendation": report.pivot_recommendation
                    })
            
            elif "critic" in event:
                state = event["critic"]
                critique = state.get("critique")
                if critique:
                    yield serialize_event("critic", {
                        "score": critique.score,
                        "is_approved": critique.is_approved,
                        "feedback": critique.feedback
                    })
            
            # Small delay to prevent flooding
            await asyncio.sleep(0.01)
        
        yield serialize_event("complete", {"message": "Validation complete", "total_events": event_count})
        
    except Exception as e:
        print(f"   [API ERROR] {e}")
        yield serialize_event("error", {"message": str(e)})


@app.post("/api/validate")
async def validate_idea(request: ValidationRequest):
    """
    Start idea validation and stream events via SSE.
    """
    return StreamingResponse(
        stream_validation(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Unicorn Validator API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
