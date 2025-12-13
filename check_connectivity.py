import os
import google.generativeai as genai
import time
from dotenv import load_dotenv

# Load env vars manually to ensure we see what the app sees
load_dotenv()

PROXY = os.getenv("PROXY_URL")
API_KEY = os.getenv("GEMINI_API_KEY")

print(f"--- VPS DIAGNOSTICS ---")
print(f"PROXY_URL: {PROXY}")
print(f"GEMINI_API_KEY: {'Present' if API_KEY else 'MISSING'}")

# Ensure proxy is set in env
if PROXY:
    os.environ["HTTP_PROXY"] = PROXY
    os.environ["HTTPS_PROXY"] = PROXY
    os.environ["http_proxy"] = PROXY
    os.environ["https_proxy"] = PROXY
    print("Set proxy env vars.")

genai.configure(api_key=API_KEY)

print("\n--- TEST 1: List Models (Simple API Call) ---")
try:
    start = time.time()
    models = list(genai.list_models())
    print(f"✅ Success! Found {len(models)} models in {time.time() - start:.2f}s")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n--- TEST 2: Embed Content (The Failing Call) ---")
try:
    start = time.time()
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="Test query",
        task_type="retrieval_query"
    )
    print(f"✅ Success! Embedding generated in {time.time() - start:.2f}s")
    print(f"Vector length: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ Failed: {e}")
