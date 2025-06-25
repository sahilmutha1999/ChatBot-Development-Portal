import os
import base64
import requests
import json
import dotenv

dotenv.load_dotenv()

# Get API key from environment
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Please set GOOGLE_API_KEY in your .env file")
    exit()

# Google Vision API endpoint
url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

# Read your image
image_path = "media/swim_lane.png"  # Change to your image path

# Convert image to base64
with open(image_path, "rb") as image_file:
    image_content = base64.b64encode(image_file.read()).decode('utf-8')

# Create request
request_body = {
    "requests": [
        {
            "image": {
                "content": image_content
            },
            "features": [
                {
                    "type": "TEXT_DETECTION",  # Extract text
                    "maxResults": 50
                },
                {
                    "type": "DOCUMENT_TEXT_DETECTION",  # Better for documents
                    "maxResults": 50
                }
            ]
        }
    ]
}

# Send request
print("🚀 Sending image to Google Vision API...")
response = requests.post(url, json=request_body)

# Check if successful
if response.status_code == 200:
    result = response.json()
    
    # Print the full text found
    print("\n📝 FULL TEXT DETECTED:")
    print("-" * 50)
    
    # Get text from DOCUMENT_TEXT_DETECTION (usually better for diagrams)
    if 'responses' in result and result['responses']:
        response_data = result['responses'][0]
        
        if 'fullTextAnnotation' in response_data:
            full_text = response_data['fullTextAnnotation']['text']
            print(full_text)
        else:
            print("No text detected")
    
    # Save full response to file for inspection
    with open("google_vision_response.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n✅ Full response saved to: google_vision_response.json")
    
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)