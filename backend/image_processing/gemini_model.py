import os
import google.generativeai as genai
from PIL import Image
import dotenv

dotenv.load_dotenv()

# Configure Gemini with your API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Please set GOOGLE_API_KEY in your .env file")
    exit()

genai.configure(api_key=API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

# Load your image
image_path = "media/swim_lane.png"  # Change to your image path
image = Image.open(image_path)

# The comprehensive prompt for swimlane analysis
prompt = """Analyze this swimlane diagram and provide:

1. SWIMLANES: List all swimlanes/departments (horizontal rows or vertical columns)
2. ACTIVITIES: For each swimlane, list the activities/tasks in order
3. PROCESS FLOW: Describe the complete process flow from start to end
4. DECISION POINTS: Identify any decision points and where the flow branches
5. HANDOFFS: Note where work transfers between departments

Please be specific and use the exact text from the diagram. Format the response clearly."""

print("🚀 Sending image to Gemini...")
print("="*60)

# Send to Gemini
response = model.generate_content([prompt, image])

# Print the response
print("\n📊 GEMINI ANALYSIS:")
print("="*60)
print(response.text)
print("="*60)