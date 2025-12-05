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
            "use_fast_model": use_fast_model
        }
        
        with st.status("🚀 Running Validation Loop...", expanded=True) as status:
                st.write("Initializing agents...")
                
                # Run the Graph
                for event in graph_app.stream(initial_state, config={"recursion_limit": max_iter*2 + 10}):
                    
                    # Handle Generator Event
                    if "generator" in event:
                        state = event["generator"]
                        idea = state.get("current_idea")
                        if idea:
                            st.markdown(f"### 💡 Generated Idea (Iter {state['iteration_count']})")
                            st.info(f"**{idea.title}**\n\n{idea.description}\n\n*Monetization:* {idea.monetization_strategy}")
                            st.session_state.chat_history.append(f"**Generated Idea:** {idea.title}\n{idea.description}\n")

                    # Handle Researcher Event
                    if "researcher" in event:
                        state = event["researcher"]
                        interview_guide = state.get("interview_guide")
                        if interview_guide:
                            st.markdown("### 📋 Research Plan Created")
                            with st.expander("View Hypotheses & Target Personas", expanded=True):
                                st.markdown("**Target Personas for Interview:**")
                                for p in interview_guide.target_personas:
                                    with st.container():
                                        st.markdown(f"**{p.name}** - {p.role}")
                                        st.caption(f"*{p.archetype}:* {p.context}")
                                        st.divider()
                                
                                st.markdown("**Hypotheses to Test:**")
                                for h in interview_guide.hypotheses_to_test:
                                    st.markdown(f"- **[{h.type}]** {h.description}")
                            st.session_state.chat_history.append(f"**Research Plan:**\nPersonas: {len(interview_guide.target_personas)}\n")
                    
                    # Handle Simulation Event
                    if "simulation" in event:
                        state = event["simulation"]
                        raw_interviews = state.get("raw_interviews", [])
                        if raw_interviews:
                            st.markdown(f"### 🗣️ User Interviews Simulated ({len(raw_interviews)})")
                            
                            cols = st.columns(len(raw_interviews))
                            for idx, interview in enumerate(raw_interviews):
                                with cols[idx % 3]: # Wrap around if more than 3
                                    with st.container(border=True):
                                        st.markdown(f"**{interview.persona.name}**")
                                        st.caption(f"{interview.persona.role}")
                                        st.progress(interview.pain_level / 10, text=f"Pain: {interview.pain_level}/10")
                                        st.progress(interview.willingness_to_pay / 10, text=f"WTP: {interview.willingness_to_pay}/10")
                                        with st.popover("Transcript Summary"):
                                            st.markdown(interview.transcript_summary)
                            st.session_state.chat_history.append(f"**Interviews:** {len(raw_interviews)} conducted.\n")

                    # Handle Analyst Event
                    if "analyst" in event:
                        state = event["analyst"]
                        report = state.get("research_report")
                        if report:
                            st.markdown("### 📊 Analyst Report")
                            st.success(f"**Pivot Recommendation:**\n{report.pivot_recommendation}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("✅ **Confirmed**")
                                for h in report.confirmed_hypotheses:
                                    st.markdown(f"- {h}")
                            with col2:
                                st.markdown("❌ **Rejected**")
                                for h in report.rejected_hypotheses:
                                    st.markdown(f"- {h}")
                                    
                            with st.expander("Key Insights"):
                                for insight in report.key_insights:
                                    st.markdown(f"💡 {insight}")
                            st.session_state.chat_history.append(f"**Analyst Report:**\nRecommendation: {report.pivot_recommendation}\n")

                    # Handle Critic Event
                    if "critic" in event:
                        state = event["critic"]
                        critique = state.get("critique")
                        if critique:
                            st.markdown(f"### 🧐 Investor Critique (Score: {critique.score}/10)")
                            
                            # Dynamic Styling based on Score
                            status_class = "approved" if critique.is_approved else "rejected"
                            status_icon = "✅" if critique.is_approved else "❌"
                            
                            st.markdown(f"""
                            <div class="metric-card {status_class}">
                                <h3>Score: {critique.score}/10 {status_icon}</h3>
                                <p><strong>Status:</strong> {"APPROVED" if critique.is_approved else "REJECTED (Needs Pivot)"}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.write("### 🛑 Critical Feedback")
                            st.write(critique.feedback)
                            
                            if critique.is_approved:
                                st.balloons()
                                st.success("🦄 UNICORN DETECTED! FUNDING UNLOCKED.")
                            
                            st.session_state.chat_history.append(f"**Critique:** Score {critique.score}\n{critique.feedback}\n")


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
