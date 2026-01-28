"""
Image upload and processing handler for AI Tutor Agent
"""

import os
from PIL import Image
import base64
from io import BytesIO
from datetime import datetime
from LLM_api import client, VISION_MODEL

# Directory for storing uploaded images
IMAGES_DIR = "uploaded_images"

def ensure_images_directory():
    """Create images directory if it doesn't exist."""
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

def save_uploaded_image(image_file, conversation_id: str) -> str:
    """
    Save an uploaded image to disk.
    
    Args:
        image_file: File storage object or path
        conversation_id: ID of the conversation
    
    Returns:
        Path to saved image
    """
    ensure_images_directory()
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_extension = image_file.filename.split('.')[-1]
    filename = f"{conversation_id}_{timestamp}.{file_extension}"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    # Save image
    image = Image.open(image_file)
    image.save(filepath)
    
    return filepath

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image to base64 for API transmission.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_llm(image_path: str, user_question: str, subject: str) -> str:
    """
    Analyze an image using vision-capable LLM.
    
    Args:
        image_path: Path to the image
        user_question: User's question about the image
        subject: The current learning subject
    
    Returns:
        AI response about the image
    """
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    
    # Determine image type
    image_type = image_path.split('.')[-1].lower()
    if image_type == 'jpg':
        image_type = 'jpeg'
    
    # Create vision message
    messages = [
        {
            "role": "system",
            "content": f"You are Socratic, an AI tutor teaching about {subject}. Use the Socratic method to guide the student through understanding the image."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_question
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_type};base64,{base64_image}"
                    }
                }
            ]
        }
    ]
    
    try:
        # Use vision model from LLM_api
        completion = client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            max_tokens=1000,
            extra_headers={
                "HTTP-Referer": "http://127.0.0.1:5000",
                "X-Title": "Socratic AI Tutor"
            }
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        # Fallback if vision model fails
        return f"I encountered an error analyzing the image: {str(e)}. Please try describing the image in text, and I'll help you understand it better."

def get_image_description(image_path: str) -> str:
    """
    Get a simple description of an image for accessibility.
    
    Args:
        image_path: Path to the image
    
    Returns:
        Brief description of the image
    """
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Provide a brief, descriptive caption for this image in one sentence."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encode_image_to_base64(image_path)}"
                    }
                }
            ]
        }
    ]
    
    try:
        completion = client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            max_tokens=100,
            extra_headers={
                "HTTP-Referer": "http://127.0.0.1:5000",
                "X-Title": "Socratic AI Tutor"
            }
        )
        return completion.choices[0].message.content
    except:
        return "Image uploaded"
