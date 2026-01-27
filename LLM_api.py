import time
from openai import OpenAI
from groq import Groq

import os
from dotenv import load_dotenv

load_dotenv()

# Try Groq first (faster, higher limits), fallback to OpenRouter
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Determine which provider to use
if GROQ_API_KEY:
    print("Using Groq API (fast, reliable)")
    client = Groq(api_key=GROQ_API_KEY)
    LLM_PROVIDER = "groq"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
elif OPENROUTER_API_KEY:
    print("Using OpenRouter API (fallback)")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    LLM_PROVIDER = "openrouter"
    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
else:
    raise ValueError(
        "No API key found. Please set GROQ_API_KEY (recommended) or OPENROUTER_API_KEY in .env"
    )

def send_request(prompt):
    """Send a single request to the API and return the result."""
    print(f"Sending request...")
    start_time = time.time()
    
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>",
            "X-Title": "<YOUR_SITE_NAME>",
        },
        model="meta-llama/llama-4-scout",   
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    response = completion.choices[0].message.content
    print(f"Response: {response}")
    print(f"Generation time: {elapsed_time:.2f} seconds")
    
    return response

def main():
    prompt = "What is the meaning of life?"
    
    print("Starting request...")
    overall_start_time = time.time()
    
    response = send_request(prompt)
    
    overall_end_time = time.time()
    overall_elapsed_time = overall_end_time - overall_start_time
    
    print(f"\n===== SUMMARY =====")
    print(f"Total execution time: {overall_elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()