import streamlit as st
import json
# Import the compiled graph from main.py
from main import app

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

user_input = st.text_area("Enter your startup idea:", height=100, placeholder="e.g., Uber for walking robotic dogs...")

if st.button("🚀 Start Simulation", type="primary"):
    if not user_input:
        st.warning("Please enter an idea first.")
    else:
        st.divider()
        
        # Initialize State for Graph
        inputs = {
            "initial_input": user_input, 
            "iteration_count": 0, 
            "current_idea": None, 
            "critique": None, 
            "messages": [],
            "max_iterations": max_iter  # Pass the slider value
        }
        
        # Initialize Chat History for Export
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Clear history on new run
        st.session_state.chat_history = []
        
        # Container for the stream
        stream_container = st.container()
        
        with stream_container:
            # Run the LangGraph Stream
            # Stream mode ensures we see steps as they happen
            for event in app.stream(inputs, config={"recursion_limit": max_iter*2 + 10}):
                
                # --- HANDLE GENERATOR OUTPUT ---
                if "generator" in event:
                    data = event["generator"]
                    idea = data["current_idea"]
                    iter_count = data["iteration_count"]
                    
                    with st.chat_message("assistant", avatar="🧠"):
                        st.subheader(f"✨ Idea Version {iter_count}")
                        st.markdown(f"**Title:** {idea.title}")
                        st.markdown(f"> *{idea.description}*")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**💰 Monetization**")
                            st.info(idea.monetization_strategy)
                        with c2:
                            st.markdown("**🎯 Target Audience**")
                            st.info(idea.target_audience)
                        
                        # Add to history
                        st.session_state.chat_history.append(f"**Generator Iteration {iter_count}:**\n{idea.title}\n{idea.description}\n")
                
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
                        st.markdown("### 🗣️ User Interviews Simulated")
                        for interview in raw_interviews:
                            with st.container():
                                st.markdown(f"**{interview.persona.name}** ({interview.persona.role})")
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    st.metric("Pain Level", f"{interview.pain_level}/10")
                                    st.metric("WTP", f"{interview.willingness_to_pay}/10")
                                with col2:
                                    st.progress(interview.pain_level / 10)
                                    st.caption(interview.transcript_summary[:200] + "...")
                                st.divider()
                        st.session_state.chat_history.append(f"**Interviews Completed:** {len(raw_interviews)} personas\n")
                
                # Handle Analyst Event
                if "analyst" in event:
                    state = event["analyst"]
                    research_report = state.get("research_report")
                    if research_report:
                        st.markdown("### 📊 Analyst Report")
                        st.warning(f"**🔄 Pivot Recommendation:**\n{research_report.pivot_recommendation}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**✅ Confirmed Hypotheses:**")
                            for h in research_report.confirmed_hypotheses:
                                st.markdown(f"- {h}")
                        with col2:
                            st.markdown("**❌ Rejected Hypotheses:**")
                            for h in research_report.rejected_hypotheses:
                                st.markdown(f"- {h}")
                        
                        st.markdown("**💡 Key Insights:**")
                        for insight in research_report.key_insights:
                            st.info(insight)
                        
                        st.session_state.chat_history.append(f"**Analyst Report:**\n{research_report.pivot_recommendation}\n")
                
                # --- HANDLE CRITIC OUTPUT ---
                elif "critic" in event:
                    data = event["critic"]
                    critique = data["critique"]
                    
                    with st.chat_message("user", avatar="🧐"):
                        st.subheader("⚖️ VC Verdict")
                        
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
                        
                        # Add to history
                        st.session_state.chat_history.append({
                            "role": "critic",
                            "score": critique.score,
                            "content": critique
                        })

        st.success("Simulation Complete.")
        
        # --- EXPORT FUNCTIONALITY ---
        if st.session_state.chat_history:
            st.divider()
            st.subheader("📥 Export History")
            
            # Format as Markdown
            md_output = f"# 🦄 AI Validator Session\n\n**Seed Idea:** {user_input}\n\n---\n\n"
            
            for item in st.session_state.chat_history:
                if item["role"] == "generator":
                    idea = item["content"]
                    md_output += f"## 🧠 Generator (Iteration {item['iteration']})\n"
                    md_output += f"**Title:** {idea.title}\n\n"
                    md_output += f"**Description:** {idea.description}\n\n"
                    md_output += f"**Monetization:** {idea.monetization_strategy}\n\n"
                    md_output += f"**Target Audience:** {idea.target_audience}\n\n"
                    md_output += "---\n\n"
                elif item["role"] == "critic":
                    critique = item["content"]
                    status = "APPROVED" if critique.is_approved else "REJECTED"
                    md_output += f"## 🧐 Critic Verdict\n"
                    md_output += f"**Status:** {status}\n\n"
                    md_output += f"**Score:** {critique.score}/10\n\n"
                    md_output += f"**Feedback:** {critique.feedback}\n\n"
                    md_output += "---\n\n"
            
            st.download_button(
                label="Download Chat History (Markdown)",
                data=md_output,
                file_name="unicorn_validator_history.md",
                mime="text/markdown"
            )
