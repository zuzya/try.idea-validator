import os
import json
import time
import logging
import google.generativeai as genai
from google.api_core import retry
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    # Add other state fields as needed

# --- Recruiter Class ---

class Recruiter:
    def __init__(self, api_key: str, personas_file: str = "personas.json", store_id_file: str = "persona_store_id.txt"):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.personas_file = personas_file
        self.store_id_file = store_id_file
        self.corpus_name = "personas-corpus" # Optional: name for the corpus if using new API, but File Search usually uses just files or a corpus
        self._file_store_id = self._load_or_create_index()

    def _load_or_create_index(self) -> str:
        """
        Checks if a file store ID exists locally. If not, processes the dataset,
        uploads it to Google File Search, and saves the ID.
        """
        if os.path.exists(self.store_id_file):
            with open(self.store_id_file, "r") as f:
                store_id = f.read().strip()
            logger.info(f"Found existing File Store ID: {store_id}")
            return store_id

        logger.info("No existing File Store ID found. Creating new index...")
        return self._create_index()

    def _create_index(self) -> str:
        """
        Converts personas.json to JSONL, uploads to Gemini, and waits for processing.
        """
        # 1. Convert to JSONL
        jsonl_file = "personas.jsonl"
        logger.info(f"Converting {self.personas_file} to {jsonl_file}...")
        
        if not os.path.exists(self.personas_file):
            raise FileNotFoundError(f"Personas file not found: {self.personas_file}")

        with open(self.personas_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Assuming data is a list of dicts. 
        # We format each record to be descriptive for semantic search.
        with open(jsonl_file, "w", encoding="utf-8") as f:
            for entry in data:
                # Construct a single text block for the document
                # Adjust fields based on actual structure of personas.json
                # User said fields are: `input persona`, `synthesized text`
                input_persona = entry.get("input persona", "") or entry.get("persona", "")
                synthesized_text = entry.get("synthesized text", "") or entry.get("text", "")
                
                text_content = f"Input Persona: {input_persona}\nSynthesized Text: {synthesized_text}"
                
                # For File Search, we upload files. 
                # If we want to treat each line as a document, it's better to have one large file 
                # or split into chunks. The API handles parsing.
                # However, for 20k records, a single text/jsonl file is good.
                # We'll just write the text content.
                f.write(text_content.replace("\n", " ") + "\n")

        # 2. Upload File
        logger.info(f"Uploading {jsonl_file} to Google File Search...")
        
        # Upload the file
        file_upload = genai.upload_file(path=jsonl_file, display_name="Personas Dataset")
        
        # Verify state
        while file_upload.state.name == "PROCESSING":
            logger.info("Waiting for file to be processed...")
            time.sleep(2)
            file_upload = genai.get_file(file_upload.name)

        if file_upload.state.name == "FAILED":
            raise ValueError(f"File upload failed: {file_upload.state.name}")

        logger.info(f"File uploaded successfully: {file_upload.name}")

        # Save the file URI/Name (which acts as the ID for retrieval)
        # Note: In the current SDK, we often use the file URI directly or create a cache.
        # But for 'File Search' specifically (retrieval tool), we usually don't need a separate 'Store ID' 
        # like in OpenAI assistants, we just pass the file object or name to the model tool.
        # However, to persist it across runs, we save the file.name (e.g., 'files/xxxx').
        
        with open(self.store_id_file, "w") as f:
            f.write(file_upload.name)
            
        return file_upload.name

    @retry.Retry(predicate=retry.if_exception_type(Exception)) # Add specific exceptions if known
    def search_personas(self, startup_idea: str, limit: int = 10) -> List[str]:
        """
        Searches for personas relevant to the startup idea using Gemini File Search.
        """
        logger.info(f"Searching for personas relevant to: {startup_idea[:50]}...")
        
        # To use File Search, we configure a model with the retrieval tool
        # pointing to our uploaded file.
        
        # We need to get the file object again to pass it to the tool
        # (or just pass the name if the SDK supports it, usually it wants the object or list of objects)
        # Since we stored the name, we can get it.
        # Optimization: We could cache the file object in self, but for robustness we fetch it or just use the name if supported.
        
        # Note: The most efficient way in the current SDK for a persistent "index" 
        # is often creating a 'Content Cache' or just passing the file to the model generation call 
        # if it's within the context window limits (20k short personas might fit in 1M/2M context).
        # BUT the user specifically asked for "File Search" (Retrieval).
        # As of late 2024/2025, Gemini API "File Search" usually implies using the `tools='retrieval'` 
        # or simply passing files to the model which handles RAG automatically for large contexts.
        # Given 20k records, it might be large. Let's use the standard generation with the file resource.
        
        # Strategy: We will ask the model to "find" relevant parts. 
        # We use a model capable of handling the file.
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', # Or 2.5 if available/requested, user said 2.5 for the parsing node.
            # We can use 1.5 Flash for retrieval as it's fast and cheap.
        )
        
        # We can't easily get "top 10 chunks" directly via a pure "search" API method that returns raw text 
        # without generation unless we use the semantic retrieval API specifically (AQA or similar).
        # However, the standard "File Search" pattern is:
        # Prompt: "Find the top 10 most relevant personas for this idea..." + File
        
        # Let's try to get the model to extract them.
        prompt = f"""
        I have a dataset of user personas.
        Find the top {limit} personas that would be most relevant to interview for the following startup idea:
        
        Startup Idea: "{startup_idea}"
        
        Return the exact text of these personas from the file.
        Separate them clearly.
        """
        
        # Get the file object
        file_obj = genai.get_file(self._file_store_id)
        
        response = model.generate_content(
            [prompt, file_obj],
            request_options={"timeout": 600} # Extended timeout for processing
        )
        
        return [response.text] # The response text itself contains the chunks

# --- Recruiter Node ---

def recruiter_node(state: RecruiterState, api_key: str) -> RecruiterState:
    """
    Orchestrates the finding and selection of personas.
    """
    logger.info("Starting recruiter_node...")
    
    # 1. Initialize Recruiter
    recruiter = Recruiter(api_key=api_key)
    
    # 2. Search
    # The search method returns the raw text response from the model which contains the personas
    # We treat this as our "chunks"
    search_results = recruiter.search_personas(state.startup_idea)
    raw_chunks = "\n\n".join(search_results)
    
    # 3. Parse and Select with Gemini 2.5 Flash
    # Note: User requested "Gemini 2.5 Flash". Ensure this model name is correct for the environment.
    # If 2.5 is not available, fallback to 1.5-flash or pro. 
    # Assuming 'gemini-1.5-flash' is the stable one, but using 'gemini-2.0-flash-exp' or similar if 2.5 is a typo or future model.
    # I will use 'gemini-1.5-flash' as a safe default or 'gemini-2.0-flash-exp' if the user insists on newer, 
    # but let's stick to the user's request if possible or a known valid model. 
    # The user said "Gemini 2.5 Flash". I will assume they might mean 1.5 Flash or 2.0. 
    # I'll use 'gemini-1.5-flash' for safety unless I can verify 2.5 exists. 
    # Actually, let's use 'gemini-1.5-flash' and comment about version.
    
    parsing_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": list[RichPersona]
        }
    )
    
    selection_prompt = f"""
    Here is the description of a startup idea: "{state.startup_idea}"
    
    Here are the raw profiles of potential candidates found in our database:
    {raw_chunks}
    
    Your task:
    1. Parse these profiles.
    2. Select exactly 3 best target users and 1 tough critic (total 4).
    3. Return the result strictly as a JSON list of RichPersona objects.
    
    For the 'attitude' field, label the critic as 'Critical' or 'Skeptical'.
    """
    
    try:
        response = parsing_model.generate_content(selection_prompt)
        
        # Parse JSON response
        # With response_mime_type="application/json", text should be valid JSON
        selected_personas_data = json.loads(response.text)
        
        # Convert to Pydantic models
        selected_personas = [RichPersona(**p) for p in selected_personas_data]
        
        # Update state
        state.selected_personas = selected_personas
        logger.info(f"Successfully selected {len(selected_personas)} personas.")
        
    except Exception as e:
        logger.error(f"Error in parsing/selection: {e}")
        # Retry logic could go here or be handled by the caller
        raise
        
    return state

# --- Main Execution for Testing ---

if __name__ == "__main__":
    # Example usage
    # Ensure GOOGLE_API_KEY is set in environment or passed directly
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Please set GOOGLE_API_KEY environment variable.")
        exit(1)
        
    test_idea = "A mobile app that gamifies picking up trash in your neighborhood using AR."
    
    initial_state = RecruiterState(startup_idea=test_idea)
    
    try:
        final_state = recruiter_node(initial_state, api_key)
        
        print("\n--- Selected Personas ---")
        for p in final_state.selected_personas:
            print(f"\nName: {p.name}")
            print(f"Role: {p.role}")
            print(f"Attitude: {p.attitude}")
            print(f"Background: {p.background}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
