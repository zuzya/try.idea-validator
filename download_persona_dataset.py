"""
Download PersonaHub dataset from HuggingFace.
Downloads the 'instruction' split and saves a sample of 20k rows.
"""

from datasets import load_dataset
import json

def download_personahub_dataset(output_file='personahub_instruction_20k.json', num_samples=20000):
    """
    Download PersonaHub dataset (instruction split) and save sample to JSON.
    
    Args:
        output_file: Path to save the JSON file
        num_samples: Number of samples to download (default: 20000)
    """
    print(f"Downloading PersonaHub dataset (instruction split)...")
    print(f"Requesting {num_samples} samples...")
    
    # Load the dataset from HuggingFace
    # Using streaming=True for efficiency with large datasets
    dataset = load_dataset(
        "proj-persona/PersonaHub",
        "instruction",
        split=f"train[:{num_samples}]",
        trust_remote_code=True
    )
    
    print(f"Downloaded {len(dataset)} samples")
    
    # Convert to list of dictionaries
    data = []
    for item in dataset:
        data.append(dict(item))
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data)} samples to {output_file}")
    print(f"File size: {len(json.dumps(data, ensure_ascii=False)) / 1024 / 1024:.2f} MB")
    
    # Print sample record to understand structure
    if data:
        print("\nSample record structure:")
        print(json.dumps(data[0], ensure_ascii=False, indent=2))
    
    return data

if __name__ == "__main__":
    download_personahub_dataset()
