import time
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()

# Single API key
API_KEY = os.getenv("OPENROUTER_API_KEY")

# If not in env, try Streamlit secrets
if not API_KEY:
    try:
        import streamlit as st
        # Accessing st.secrets can raise an error if no secrets file exists
        API_KEY = st.secrets.get("OPENROUTER_API_KEY")
    except Exception:
        pass

if not API_KEY:
    raise ValueError(
        "OpenRouter API Key not found. Please set the OPENROUTER_API_KEY environment variable "
        "or add it to .streamlit/secrets.toml."
    )

# Create a single client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
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