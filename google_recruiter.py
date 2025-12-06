import os
import json
import logging
import numpy as np
import google.generativeai as genai
from google.api_core import retry
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
INDEX_FILE = "personas_index.json"
EMBEDDING_MODEL = "models/text-embedding-004"
GENERATION_MODEL = "gemini-1.5-flash"

# --- Pydantic Models ---

class RichPersona(BaseModel):
    """Represents a detailed persona selected for the interview."""
    name: str = Field(description="A generated name for the persona")
    role: str = Field(description="Role or profession of the persona")
    background: str = Field(description="Key background details relevant to the startup idea")
    attitude: str = Field(description="Attitude towards the idea (e.g., Enthusiastic, Skeptical, Critical)")
    original_text: str = Field(description="The original raw text from the dataset")

class RecruiterState(BaseModel):
    """State for the recruiter node."""
    startup_idea: str
    selected_personas: List[RichPersona] = []

# --- GoogleRecruiter Class ---

class GoogleRecruiter:
    def __init__(self, api_key: Optional[str] = None, index_file: str = INDEX_FILE):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found.")
        
        genai.configure(api_key=self.api_key)
        self.index_file = index_file
        self.embeddings = None
        self.texts = None
        self._load_index()

    def _load_index(self):
        """Loads the vector index."""
        if not os.path.exists(self.index_file):
            raise FileNotFoundError(
                f"Index file '{self.index_file}' not found. "
                "Please run 'build_vector_index.py' first."
            )
        
        logger.info(f"Loading index from {self.index_file}...")
        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.embeddings = np.array(data['embeddings'])
        self.texts = data['texts']
        logger.info(f"Loaded {len(self.texts)} personas and embeddings.")

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def search_personas(self, startup_idea: str, limit: int = 10) -> List[str]:
        """
        Searches for personas using vector similarity.
        """
        logger.info(f"Embedding query: {startup_idea[:50]}...")
        
        # Embed query
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=startup_idea,
            task_type="retrieval_query"
        )
        query_embedding = np.array(result['embedding'])
        
        # Compute cosine similarity
        # (Assuming embeddings are normalized? Usually yes from API, but dot product is safe for ranking)
        scores = np.dot(self.embeddings, query_embedding)
        
        # Get top K indices
        top_indices = np.argsort(scores)[-limit:][::-1]
        
        results = []
        for idx in top_indices:
            results.append(self.texts[idx])
            
        logger.info(f"Found {len(results)} relevant personas.")
        return results

# --- Recruiter Node ---

def recruiter_node(state: RecruiterState) -> RecruiterState:
    """
    Orchestrates the finding and selection of personas.
    """
    logger.info("Starting recruiter_node...")
    
    try:
        # 1. Initialize Recruiter
        recruiter = GoogleRecruiter()
        
        # 2. Search
        raw_chunks = recruiter.search_personas(state.startup_idea, limit=10)
        
        if not raw_chunks:
            logger.warning("No personas found.")
            return state
            
        context_text = "\n\n".join([f"Persona {i+1}:\n{chunk}" for i, chunk in enumerate(raw_chunks)])
        
        # 3. Parse and Select with Gemini
        parsing_model = genai.GenerativeModel(
            GENERATION_MODEL,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": list[RichPersona]
            }
        )
        
        selection_prompt = f"""
        Here is the description of a startup idea: "{state.startup_idea}"
        
        Here are {len(raw_chunks)} potential candidate profiles found in our database:
        
        {context_text}
        
        Your Task:
        1. Analyze these profiles.
        2. Select exactly 3 BEST target users and 1 TOUGH CRITIC.
        3. Extract their details and format them into the required JSON structure.
        4. For the 'attitude' field, label the critic as 'Critical' or 'Skeptical'.
        
        Return ONLY the JSON list.
        """
        
        logger.info("Asking Gemini to select and parse personas...")
        response = parsing_model.generate_content(selection_prompt)
        
        selected_personas_data = json.loads(response.text)
        state.selected_personas = [RichPersona(**p) for p in selected_personas_data]
        
        logger.info(f"Successfully selected {len(state.selected_personas)} personas.")
        
    except Exception as e:
        logger.error(f"Error in recruiter_node: {e}")
        raise
        
    return state

if __name__ == "__main__":
    # Test
    test_idea = "A subscription service for rare and exotic houseplants with AI care tips."
    try:
        initial_state = RecruiterState(startup_idea=test_idea)
        final_state = recruiter_node(initial_state)
        for p in final_state.selected_personas:
            print(f"\nName: {p.name}\nRole: {p.role}\nAttitude: {p.attitude}")
    except Exception as e:
        print(f"Error: {e}")
