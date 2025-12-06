"""
Build Vector Index for Personas using Google Gemini Embeddings.
"""

import os
import json
import time
import logging
import numpy as np
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
EMBEDDING_MODEL = "models/text-embedding-004" # Or "models/embedding-001"

def build_index(input_file: str, output_file: str, api_key: str, limit: int = None):
    """
    Generates embeddings for personas and saves them.
    """
    genai.configure(api_key=api_key)
    
    logger.info(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if limit:
        data = data[:limit]
        logger.info(f"Limiting to first {limit} personas for testing.")
        
    logger.info(f"Loaded {len(data)} personas. Generating embeddings...")
    
    embeddings = []
    texts = []
    
    # Prepare texts
    for entry in data:
        # Combine fields for embedding
        text = f"Persona: {entry.get('input persona', '')}\nSynthesized Text: {entry.get('synthesized text', '')}"
        texts.append(text)
    
    # Batch processing
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        try:
            # Embed batch
            # task_type="retrieval_document" optimizes for search
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=batch_texts,
                task_type="retrieval_document",
                title="Persona Profile" # Optional title for document
            )
            
            # Result is usually a dict with 'embedding' key which is a list of lists
            batch_embeddings = result['embedding']
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//BATCH_SIZE + 1}/{total_batches}")
            
            # Rate limiting sleep
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error in batch {i}: {e}")
            # Try to recover or skip? For now, we raise to ensure integrity
            raise

    # Save results
    logger.info("Saving index...")
    
    # We save both the original data (or at least the text) and the embeddings
    # To save space, we might just save the index and reference the original file, 
    # but saving a consolidated file is easier for the recruiter.
    
    output_data = {
        "embeddings": embeddings,
        "texts": texts,
        "original_data": data # Optional: keep full metadata
    }
    
    # Using numpy for efficient saving/loading of embeddings could be better, 
    # but JSON is requested/portable.
    # Actually, saving 20k vectors (768 dims) in JSON is huge.
    # 20000 * 768 * 10 chars ~ 150MB.
    # It's acceptable.
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f)
        
    logger.info(f"Index saved to {output_file}")

if __name__ == "__main__":
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found.")
        exit(1)
        
    # Build partial index for testing (remove limit=1000 for full build)
    build_index("personas.json", "personas_index.json", api_key, limit=1000)
