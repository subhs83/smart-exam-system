import json
import re


def parse_ai_output(ai_text):

    questions = []

    blocks = ai_text.split("Q")

    for block in blocks:

        if not block.strip():
            continue

        try:
            lines = block.split("\n")

            question = lines[0].split(":",1)[1].strip()

            option_a = lines[1].replace("A)", "").strip()
            option_b = lines[2].replace("B)", "").strip()
            option_c = lines[3].replace("C)", "").strip()
            option_d = lines[4].replace("D)", "").strip()

            answer = lines[5].split(":")[1].strip()

            questions.append({
                "question": question,
                "option_a": option_a,
                "option_b": option_b,
                "option_c": option_c,
                "option_d": option_d,
                "correct_answer": answer
            })

        except:
            continue

    return questions