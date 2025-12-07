import streamlit as st
import json
# Import the compiled graph from main.py
from main import app as graph_app, BusinessIdea
import time

st.set_page_config(page_title="AI Idea Validator 2025", layout="wide", page_icon="🦄")

# Custom CSS for 2025 Look
st.markdown("""
<style>
    .stChatMessage { border-radius: 12px; border: 1px solid #eee; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #666; }
    .approved { border-left: 5px solid #00cc00 !important; background-color: #e8f5e9; }
    .rejected { border-left: 5px solid #ff4444 !important; background-color: #ffebee; }
</style>
""", unsafe_allow_html=True)

st.title("🦄 AI Unicorn Validator (Gen 3)")
st.caption("Powered by Gemini 3.0 Pro (Visionary) & GPT-5.1 (Reasoning)")

# Input
with st.sidebar:
    st.header("Configuration")
    max_iter = st.slider("Max Iterations", 1, 10, 5)
    num_personas = st.slider("Number of Respondents", 1, 3, 3)
    interview_iterations = st.slider("Interview Cycles", 1, 3, 1, help="How many times to run the interview loop before critic review")
    mock_simulation = st.checkbox("Mock User Interviews (faster testing)", value=False)
    st.info("System is ready. API connections secure.")
    
    if mock_simulation:
        import os
        os.environ["MOCK_SIMULATION"] = "true"
        st.warning("⚠️ Mock Mode: User interviews will be simulated with fake data")
    else:
        import os
        os.environ["MOCK_SIMULATION"] = "false"

    st.divider()
    st.subheader("Validation Modes")
    enable_simulation = st.checkbox("Run Simulation (Research & Interviews)", value=True, help="Enable synthetic user interviews and analysis.")
    enable_critic = st.checkbox("Enable Investor Critic (Iterative Refinement)", value=True, help="Enable VC critique and iterative improvement loop.")
    
    st.divider()
    use_fast_model = st.checkbox("⚡ Debug Mode (Fast Models)", value=False, help="Use Gemini 2.5 Flash for all agents. Much faster, but less smart.")

user_input = st.text_area("Enter your startup idea:", height=100, placeholder="e.g., Uber for walking robotic dogs...")

if st.button("Start Validation Loop", type="primary"):
    if not user_input:
        st.warning("Please enter an idea first.")
    else:
        st.session_state.chat_history = []
        st.session_state.collected_interviews = []  # Clear previous interviews
        st.session_state.chat_history.append(f"**Idea:** {user_input}\n")
        
        # Initialize State
        initial_state = {
            "initial_input": user_input,
            "iteration_count": 0,
            "max_iterations": max_iter,
            "mode": "full",
            "messages": [],
            "enable_simulation": enable_simulation,
            "enable_critic": enable_critic,
            "use_fast_model": use_fast_model,
            "num_personas": num_personas,
            "interview_iterations": interview_iterations,
            "current_interview_cycle": 0
        }
        
        # === REAL-TIME RENDERING WITH PLACEHOLDERS ===
        # Create placeholders for each section BEFORE the loop
        # These will be updated in-place as events arrive (no DOM appending = no crash)
        
        with st.status("🚀 Running Validation Loop...", expanded=True) as status:
            st.write("Agents are working...")
            progress_text = st.empty()
            
            # Pre-create placeholders for real-time updates
            idea_placeholder = st.empty()
            guide_placeholder = st.empty()
            personas_placeholder = st.empty()
            interviews_placeholder = st.empty()
            report_placeholder = st.empty()
            critiques_placeholder = st.empty()
            
            # Track collected data for final rendering
            collected_ideas = []
            collected_interview_count = 0
            collected_critiques = []
            
            try:
                event_count = 0
                for event in graph_app.stream(initial_state, config={"recursion_limit": max_iter*2 + 10}):
                    event_count += 1
                    event_keys = list(event.keys())
                    print(f"   [APP] Event #{event_count}: {event_keys}")
                    progress_text.text(f"🔄 Processing: {event_keys[0] if event_keys else 'unknown'}...")
                    
                    # --- GENERATOR: Real-time render ---
                    if "generator" in event:
                        state = event["generator"]
                        idea = state.get("current_idea")
                        if idea:
                            collected_ideas.append((state['iteration_count'], idea))
                            # Update placeholder in-place
                            with idea_placeholder.container():
                                st.markdown(f"### 💡 Idea (Iteration {state['iteration_count']})")
                                with st.container(border=True):
                                    st.markdown(f"**{idea.title}**")
                                    st.write(idea.description)
                                    st.caption(f"💰 Monetization: {idea.monetization_strategy}")
                    
                    # --- RESEARCHER: Real-time render ---
                    if "researcher" in event:
                        state = event["researcher"]
                        guide = state.get("interview_guide")
                        if guide:
                            with guide_placeholder.container():
                                st.markdown("### 📋 Interview Guide")
                                with st.expander("View Full Research Plan", expanded=False):
                                    st.markdown("#### 🎯 Target Personas")
                                    for p in guide.target_personas:
                                        st.markdown(f"- **{p.name}** ({p.role}): {p.archetype}")
                                    st.markdown("#### 🔬 Hypotheses")
                                    for h in guide.hypotheses_to_test:
                                        st.markdown(f"- [{h.type}] {h.description}")
                    
                    # --- RECRUITER: Real-time render ---
                    if "recruiter" in event:
                        state = event["recruiter"]
                        personas = state.get("selected_personas", [])
                        if personas:
                            with personas_placeholder.container():
                                st.markdown("### 🕵️ Recruited Personas")
                                for p in personas:
                                    with st.expander(f"👤 {p.get('name', 'Unknown')} - {p.get('role', 'Unknown')}", expanded=True):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown(f"**📝 Bio:** {p.get('bio', 'N/A')}")
                                            st.markdown(f"**🏢 Context:** {p.get('company_context', 'N/A')}")
                                        with col2:
                                            st.markdown(f"**😤 Frustrations:** {', '.join(p.get('key_frustrations', []))}")
                                            st.markdown(f"**💻 Tech:** {', '.join(p.get('tech_stack', []))}")
                        
                        # Initialize progress bar after recruiter completes
                        with interviews_placeholder.container():
                            st.markdown(f"### 🗣️ Interviews: 0/{num_personas}")
                            st.progress(0.0, text=f"Starting interviews...")
                    
                    # --- SIMULATION: Progress bar + collect for transcript viewing ---
                    if "simulation" in event:
                        state = event["simulation"]
                        interviews = state.get("raw_interviews", [])
                        collected_interview_count += len(interviews)
                        # Collect interviews for later transcript viewing
                        if "collected_interviews" not in st.session_state:
                            st.session_state.collected_interviews = []
                        st.session_state.collected_interviews.extend(interviews)
                        
                        # Show progress bar
                        total_personas = num_personas
                        progress = collected_interview_count / total_personas
                        with interviews_placeholder.container():
                            st.markdown(f"### 🗣️ Interviews: {collected_interview_count}/{total_personas}")
                            st.progress(progress, text=f"Interviewing respondents...")
                    
                    # --- ANALYST: Real-time render ---
                    if "analyst" in event:
                        state = event["analyst"]
                        report = state.get("research_report")
                        if report:
                            with report_placeholder.container():
                                st.markdown("### 📊 Analyst Report")
                                st.success(f"**🔄 Pivot Recommendation:**\n\n{report.pivot_recommendation}")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("#### ✅ Confirmed")
                                    for h in report.confirmed_hypotheses:
                                        st.markdown(f"- {h}")
                                with col2:
                                    st.markdown("#### ❌ Rejected")
                                    for h in report.rejected_hypotheses:
                                        st.markdown(f"- {h}")
                                st.markdown("#### 💡 Key Insights")
                                for insight in report.key_insights:
                                    st.info(f"💡 {insight}")
                    
                    # --- CRITIC: Real-time render ---
                    if "critic" in event:
                        state = event["critic"]
                        critique = state.get("critique")
                        if critique:
                            collected_critiques.append(critique)
                            with critiques_placeholder.container():
                                for c in collected_critiques:
                                    st.markdown(f"### 🧐 Critique (Score: {c.score}/10)")
                                    st.write(c.feedback)
                                    if c.is_approved:
                                        st.success("🦄 UNICORN DETECTED!")
                
                progress_text.text(f"✅ Done! Processed {event_count} events.")
                status.update(label="✅ Validation Complete!", state="complete", expanded=False)
                
            except Exception as e:
                print(f"   [APP CRITICAL ERROR] {e}")
                st.error(f"Graph execution error: {e}")
        
        
        # Chat history populated during streaming
        for iteration, idea in collected_ideas:
            st.session_state.chat_history.append(f"**Idea (Iter {iteration}):** {idea.title}\n")
        if collected_interview_count > 0:
            st.session_state.chat_history.append(f"**Interviews:** {collected_interview_count} conducted.\n")

# --- TRANSCRIPT VIEWING ---
if st.session_state.get("collected_interviews"):
    st.divider()
    st.subheader("📜 Interview Transcripts")
    st.caption("Click to expand and view detailed transcripts from simulated interviews")
    
    for i, interview in enumerate(st.session_state.collected_interviews, 1):
        persona_name = interview.persona.name if hasattr(interview.persona, 'name') else f"Respondent {i}"
        persona_role = interview.persona.role if hasattr(interview.persona, 'role') else "Unknown"
        
        with st.expander(f"👤 {persona_name} ({persona_role}) - Pain: {interview.pain_level}/10, WTP: {interview.willingness_to_pay}/10", expanded=False):
            # Summary
            st.markdown("### 📝 Summary")
            st.info(interview.transcript_summary)
            
            # Full Transcript
            st.markdown("### 💬 Full Transcript")
            full_transcript = getattr(interview, 'full_transcript', '')
            if full_transcript:
                st.markdown(full_transcript)
            else:
                st.caption("Full transcript not available")


# --- EXPORT FUNCTIONALITY ---
if st.session_state.get("chat_history"):
    st.divider()
    st.subheader("📥 Export History")
    
    # Format as Markdown
    md_output = f"# 🦄 AI Validator Session\n\n**Seed Idea:** {user_input}\n\n---\n\n"
    
    for item in st.session_state.chat_history:
        md_output += f"{item}\n---\n"
    
    st.download_button(
        label="Download Chat History (Markdown)",
        data=md_output,
        file_name="unicorn_validator_history.md",
        mime="text/markdown"
    )

