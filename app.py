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
    st.info("System is ready. API connections secure.")

user_input = st.text_area("Enter your startup idea:", height=100, placeholder="e.g., Uber for walking robotic dogs...")

if st.button("🚀 Start Simulation", type="primary"):
    if not user_input:
        st.warning("Please enter an idea first.")
    else:
        st.divider()
        
        # Initialize State for Graph
        inputs = {"initial_input": user_input, "iteration_count": 0, "current_idea": None, "critique": None, "messages": []}
        
        # Container for the stream
        stream_container = st.container()
        
        with stream_container:
            # Run the LangGraph Stream
            # Stream mode ensures we see steps as they happen
            for event in app.stream(inputs, config={"recursion_limit": max_iter*2 + 2}):
                
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

        st.success("Simulation Complete.")
