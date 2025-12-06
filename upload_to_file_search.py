"""
Upload personas.json to Google File Search
"""

import os
import json
import google.generativeai as genai
import time
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_to_jsonl(input_file: str, output_file: str) -> str:
    """
    Convert personas.json to JSONL format optimized for semantic search.
    Each line contains: "input persona: ... synthesized text: ..."
    
    Args:
        input_file: Path to input personas.json
        output_file: Path to output JSONL file
    
    Returns:
        Path to created JSONL file
    """
    logger.info(f"Converting {input_file} to JSONL format...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} personas")
    
    # Create JSONL with descriptive text for semantic search
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, entry in enumerate(data):
            # Extract fields
            input_persona = entry.get("input persona", "")
            synthesized_text = entry.get("synthesized text", "")
            description = entry.get("description", "")
            
            # Create a descriptive text block for semantic search
            # Format: Storing all info on one line for easy retrieval
            text_content = f"Input persona: {input_persona} | Synthesized text: {synthesized_text}"
            
            # Write as plain text (one persona per line)
            f.write(text_content + "\n")
            
            if (idx + 1) % 1000 == 0:
                logger.info(f"Processed {idx + 1}/{len(data)} personas")
    
    logger.info(f"Created JSONL file: {output_file}")
    return output_file

def upload_to_google_file_search(
    jsonl_file: str,
    api_key: str,
    store_id_file: str = "file_search_store_id.txt",
    display_name: str = "Personas Dataset"
) -> str:
    """
    Upload JSONL file to Google File Search and save the file ID.
    
    Args:
        jsonl_file: Path to JSONL file
        api_key: Google API key
        store_id_file: Path to save file/store ID
        display_name: Display name for uploaded file
    
    Returns:
        File ID/name from Google
    """
    logger.info("Initializing Google Generative AI...")
    genai.configure(api_key=api_key)
    
    # Upload the file
    logger.info(f"Uploading {jsonl_file} to Google File Search...")
    logger.info(f"This may take a few minutes for large files...")
    
    file_upload = genai.upload_file(
        path=jsonl_file,
        display_name=display_name,
        mime_type="text/plain"  # JSONL is plain text format
    )
    
    logger.info(f"File uploaded with name: {file_upload.name}")
    logger.info(f"File state: {file_upload.state.name}")
    
    # Wait for processing to complete
    while file_upload.state.name == "PROCESSING":
        logger.info("Waiting for file to be processed...")
        time.sleep(5)
        file_upload = genai.get_file(file_upload.name)
    
    if file_upload.state.name == "FAILED":
        raise ValueError(f"File upload failed: {file_upload.state}")
    
    logger.info(f"File processed successfully!")
    logger.info(f"File URI: {file_upload.uri}")
    logger.info(f"File size: {file_upload.size_bytes} bytes")
    
    # Save the file name/ID for future use
    with open(store_id_file, "w") as f:
        f.write(file_upload.name)
    
    logger.info(f"Saved file ID to {store_id_file}")
    
    return file_upload.name

def main():
    """Main execution"""
    # Configuration
    PERSONAS_FILE = "personas.json"
    JSONL_FILE = "personas.jsonl"
    STORE_ID_FILE = "file_search_store_id.txt"
    
    # Get API key from environment (loaded from .env file)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("ERROR: GOOGLE_API_KEY not found!")
        logger.error("Please add it to your .env file:")
        logger.error("  GOOGLE_API_KEY=your-api-key-here")
        return
    
    try:
        # Step 1: Convert to JSONL
        jsonl_path = convert_to_jsonl(PERSONAS_FILE, JSONL_FILE)
        
        # Step 2: Upload to Google File Search
        file_id = upload_to_google_file_search(
            jsonl_file=jsonl_path,
            api_key=api_key,
            store_id_file=STORE_ID_FILE
        )
        
        logger.info("\n" + "="*60)
        logger.info("SUCCESS!")
        logger.info("="*60)
        logger.info(f"File ID: {file_id}")
        logger.info(f"Store ID saved to: {STORE_ID_FILE}")
        logger.info(f"JSONL file: {JSONL_FILE}")
        logger.info("\nYou can now use this file ID in your Recruiter class!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
