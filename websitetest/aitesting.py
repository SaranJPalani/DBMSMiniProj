import os
import google.generativeai as genai

genai.configure()

model = genai.GenerativeModel('models/gemini-pro-latest')
response = model.generate_content("What is the capital of France?")

print(response.text)
