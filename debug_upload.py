
import requests
import os

url = 'http://127.0.0.1:5001/api/upload_document'
file_path = 'test_debug_doc.txt'

# Create dummy file
with open(file_path, 'w') as f:
    f.write("Debug content for upload test.")

try:
    with open(file_path, 'rb') as f:
        files = {'document': f}
        print(f"Sending POST to {url}...")
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    print("Raw Response Content:")
    print(response.content.decode('utf-8'))
    
    try:
        json_resp = response.json()
        print("JSON Parsed Successfully:")
        print(json_resp)
    except Exception as e:
        print(f"JSON Parsing FAILED: {e}")

except Exception as e:
    print(f"Request Failed: {e}")

# Cleanup
if os.path.exists(file_path):
    os.remove(file_path)
