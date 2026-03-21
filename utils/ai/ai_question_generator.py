import google.generativeai as genai
from utils.ai.ai_response_parser import parse_ai_output

genai.configure(api_key="AIzaSyAuTjgedVd5mvYDmivqyeQOExJLhB1sE_U")


def generate_questions(text, num_questions, difficulty):

    prompt = f"""
Generate {num_questions} multiple choice questions.

Difficulty: {difficulty}

Format:
Question
A)
B)
C)
D)
Answer:

Text:
{text}
"""

    response = genai.generate_text(
        model="models/text-bison-001",
        prompt=prompt,
        temperature=0.4,
        max_output_tokens=1024
    )

    ai_text = response.result
    return parse_ai_output(ai_text)