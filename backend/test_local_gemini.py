import os
from dotenv import load_dotenv
load_dotenv()

from app.main import call_gemini

print("Testing local call_gemini with new SDK...")
result = call_gemini("What is the capital of France?", "France is a country in Europe. Its capital is Paris.")
print("Result:", result)

