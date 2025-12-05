"""
Filter PersonaHub dataset for human-like personas using pandas.

Filtering criteria:
1. Length: 20-150 words
2. Contains human markers (age, location, profession, hobbies, emotions)
3. Excludes AI-related terms
"""

import json
import pandas as pd
import re
from typing import Optional

# Keywords that indicate human-like personas
HUMAN_MARKERS = [
    'years old', 'year old', 'living in', 'live in', 'working as', 'work as',
    'enjoy', 'enjoys', 'enjoyed', 'hate', 'hates', 'hated', 
    'struggle with', 'struggles with', 'love', 'loves', 'loved',
    'passionate about', 'interested in', 'hobby', 'hobbies',
    'my job', 'my family', 'my life', 'my career', 'my home',
    'i am a', "i'm a", 'profession', 'occupation'
]

# Terms that indicate AI/assistant entities (to exclude)
AI_MARKERS = [
    'assistant', 'ai', 'language model', 'function', 'code',
    'algorithm', 'machine learning', 'neural network', 'chatbot',
    'virtual assistant', 'digital assistant', 'automated'
]

def count_words(text: str) -> int:
    """Count words in text."""
    if pd.isna(text) or not isinstance(text, str):
        return 0
    return len(text.split())

def contains_human_markers(text: str) -> bool:
    """Check if text contains human-like markers."""
    if pd.isna(text) or not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(marker in text_lower for marker in HUMAN_MARKERS)

def contains_ai_markers(text: str) -> bool:
    """Check if text contains AI-related terms."""
    if pd.isna(text) or not isinstance(text, str):
        return False
    text_lower = text.lower()
    return any(marker in text_lower for marker in AI_MARKERS)

def filter_personas(
    input_file: str,
    output_file: str,
    min_words: int = 20,
    max_words: int = 150,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Filter PersonaHub dataset for human-like personas using pandas.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to save filtered JSON file
        min_words: Minimum word count (default: 20)
        max_words: Maximum word count (default: 150)
        verbose: Print filtering statistics
    
    Returns:
        Filtered DataFrame
    """
    # Load input data into pandas DataFrame
    print(f"Loading data from {input_file}...")
    df = pd.read_json(input_file)
    
    initial_count = len(df)
    print(f"Loaded {initial_count} records")
    
    # Try to identify the persona field
    persona_field = None
    for field in ['persona', 'input_persona', 'synthesized_text', 'text', 'instruction']:
        if field in df.columns:
            persona_field = field
            print(f"Using '{field}' as persona field")
            break
    
    if persona_field is None:
        print("Error: No persona field found in dataset!")
        print(f"Available columns: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # Create a copy to work with
    df = df.copy()
    
    # Add word count column
    df['word_count'] = df[persona_field].apply(count_words)
    
    # Add marker columns for analysis
    df['has_human_markers'] = df[persona_field].apply(contains_human_markers)
    df['has_ai_markers'] = df[persona_field].apply(contains_ai_markers)
    
    if verbose:
        print("\nInitial statistics:")
        print(f"  Word count range: {df['word_count'].min()} - {df['word_count'].max()}")
        print(f"  Records with human markers: {df['has_human_markers'].sum()} ({df['has_human_markers'].sum()/len(df)*100:.2f}%)")
        print(f"  Records with AI markers: {df['has_ai_markers'].sum()} ({df['has_ai_markers'].sum()/len(df)*100:.2f}%)")
    
    # Apply filters
    print(f"\nApplying filters...")
    
    # Filter by word count
    before_length = len(df)
    df = df[(df['word_count'] >= min_words) & (df['word_count'] <= max_words)]
    print(f"  Length filter ({min_words}-{max_words} words): {before_length} → {len(df)} (-{before_length - len(df)})")
    
    # Filter out AI markers
    before_ai = len(df)
    df = df[~df['has_ai_markers']]
    print(f"  AI exclusion filter: {before_ai} → {len(df)} (-{before_ai - len(df)})")
    
    # Filter for human markers
    before_human = len(df)
    df = df[df['has_human_markers']]
    print(f"  Human marker filter: {before_human} → {len(df)} (-{before_human - len(df)})")
    
    # Remove temporary columns
    filtered_df = df.drop(columns=['word_count', 'has_human_markers', 'has_ai_markers'])
    
    # Save to JSON
    filtered_df.to_json(output_file, orient='records', force_ascii=False, indent=2)
    
    # Print statistics
    if verbose:
        print("\n" + "="*60)
        print("FILTERING RESULTS")
        print("="*60)
        print(f"Input records:    {initial_count}")
        print(f"Filtered records: {len(filtered_df)}")
        print(f"Retention rate:   {len(filtered_df)/initial_count*100:.2f}%")
        print(f"\nSaved to: {output_file}")
        
        # Show sample filtered personas
        if len(filtered_df) > 0:
            print("\n" + "="*60)
            print("SAMPLE FILTERED PERSONAS (first 3)")
            print("="*60)
            for i, (idx, row) in enumerate(filtered_df.head(3).iterrows()):
                persona_text = row[persona_field]
                print(f"\n{i+1}. [{count_words(persona_text)} words]")
                print(persona_text[:300] + ("..." if len(persona_text) > 300 else ""))
    
    return filtered_df

if __name__ == "__main__":
    filter_personas(
        input_file='personahub_instruction_20k.json',
        output_file='personahub_filtered_human.json',
        min_words=20,
        max_words=150,
        verbose=True
    )
