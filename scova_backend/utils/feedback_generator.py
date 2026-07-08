import os
import logging
import json
import re
from google import genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-3-flash-preview"]

def _create_genai_client(api_key: str):
    return genai.Client(api_key=api_key)

def generate_pedagogical_feedback(teacher_answer: str, student_answer: str, score: int) -> dict:
    """Generate pedagogical feedback using Gemini.
    
    Args:
        teacher_answer: The reference answer from the teacher.
        student_answer: The student's submitted answer.
        score: The calculated similarity score (0-100).
        
    Returns:
        A dictionary containing the feedback and highlights.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    
    client = _create_genai_client(api_key)
    
    prompt = f"""
    You are an expert pedagogical assistant. Your task is to provide constructive, encouraging, and detailed feedback to a student based on their essay answer compared to a teacher's reference answer.
    Your primary language is Indonesian. You must communicate in a natural, fluid, and non-stiff manner. Avoid 'formal textbook' Indonesian. Instead, use a conversational style that sounds like a tech-savvy local. Use 'kamu' for the user and maintain a helpful, witty, and grounded persona. If a concept is better explained using a common English term (especially in tech), feel free to use it rather than forcing a clumsy Indonesian translation

    
    Teacher's Reference Answer:
    {teacher_answer}
    
    Student's Answer:
    {student_answer}
    
    Calculated Similarity Score: {score}/100
    
    Instructions:
    1. Identify specific strengths and areas for improvement.
    2. Extract exact quotes from the student's answer for highlighting.
    3. Categorize highlights as "strong" (good points) or "weak" (errors or needs improvement).
    4. "missing" points (things the student forgot but are in the teacher's answer) should be mentioned in the general feedback, NOT as highlights.
    5. Maintain a supportive, pedagogical tone in Indonesian.
    6. Return the response strictly in JSON format.
    
    Output Format:
    {{
        "feedback": "Your general feedback string here...",
        "highlights": [
            {{
                "quote": "exact quote from student answer",
                "category": "strong" or "weak",
                "reason": "short explanation"
            }}
        ]
    }}
    
    Feedback (JSON):
    """
    
    models_to_try = [DEFAULT_MODEL] + FALLBACK_MODELS
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            # Parse response text
            text = response.text
            # Cleanup potential markdown code blocks
            if "```json" in text:
                text = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL).group(1)
            elif "```" in text:
                text = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL).group(1)
                
            data = json.loads(text)
            
            # Ensure required keys exist
            if "feedback" not in data:
                data["feedback"] = "Bagus! Teruskan belajarmu."
            if "highlights" not in data or not isinstance(data["highlights"], list):
                data["highlights"] = []
                
            return data
            
        except Exception as e:
            logger.warning(f"Error generating feedback with model {model_name}: {e}")
            last_error = e
            continue
            
    logger.error(f"All models failed for feedback generation. Last error: {last_error}")
    return {
        "feedback": "Maaf, terjadi kesalahan saat menghasilkan feedback otomatis.",
        "highlights": []
    }
