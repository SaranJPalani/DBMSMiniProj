import os
import google.generativeai as genai
import mysql.connector

genai.configure(api_key="AIzaSyDtTTvRIWq-iA0UZvTZWUwaEhr4DJfDwoE")

model = genai.GenerativeModel('models/gemini-pro-latest')

def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='DewangMYSQLC@270505',
            database='DBMSPROJ'
        )
    except mysql.connector.Error:
        return None

def generate_feedback_summary(session_id):
    """Generate AI summary of student feedback comments for a specific session"""
    conn = get_db_connection()
    if not conn:
        return "Unable to connect to database for feedback analysis."
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get session details
        cursor.execute("""
            SELECT fs.session_id, fs.course_id, c.course_name, f.name as faculty_name
            FROM feedbacksession fs
            LEFT JOIN courses c ON fs.course_id = c.course_id
            LEFT JOIN faculty f ON fs.faculty_id = f.faculty_id
            WHERE fs.session_id = %s
        """, (session_id,))
        
        session_info = cursor.fetchone()
        if not session_info:
            return "Session not found."
        
        # Get all student comments for this session (anonymized)
        cursor.execute("""
            SELECT comments
            FROM feedbackremarks 
            WHERE session_id = %s AND comments IS NOT NULL AND comments != ''
        """, (session_id,))
        
        comments = cursor.fetchall()
        
        if not comments:
            return "No student comments available for analysis."
        
        # Prepare all comments for AI analysis
        all_comments = []
        for comment in comments:
            if comment['comments'] and comment['comments'].strip():
                all_comments.append(comment['comments'].strip())
        
        if not all_comments:
            return "No meaningful student comments found for analysis."
        
        # Create AI prompt for feedback analysis
        comments_text = "\n".join([f"- {comment}" for comment in all_comments])
        
        prompt = f"""
Analyze these student feedback comments for {session_info['faculty_name']}'s {session_info['course_name']} course.

Student comments:
{comments_text}

Return your analysis as a JSON object with this exact structure (no other text):
{{
    "overall_sentiment": "Brief description of overall student sentiment (1-2 sentences)",
    "strengths": [
        "First main strength mentioned by students",
        "Second main strength mentioned by students", 
        "Third main strength (if applicable)"
    ],
    "improvements": [
        "First area students suggest for improvement",
        "Second area for improvement",
        "Third area (if applicable)"
    ],
    "recommendations": [
        "First practical recommendation for the instructor",
        "Second practical recommendation",
        "Third recommendation (if applicable)"
    ]
}}

IMPORTANT: 
- Always try to identify at least 1-2 strengths, even if feedback is mixed or critical
- Look for any positive aspects, teaching methods that work, or areas where students aren't complaining
- If no direct strengths are mentioned, infer them from what students are NOT criticizing
- For improvements and recommendations, be specific and actionable
- Make each item concise (1-2 sentences max). Write in natural, professional language.
- Return only the JSON object, no additional text or formatting.
"""
        
        # Generate AI response using Gemini
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        # Clean the response to extract only JSON
        # Remove any markdown code blocks or extra text
        if "```json" in ai_response:
            ai_response = ai_response.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_response:
            ai_response = ai_response.split("```")[1].strip()
        
        # Find JSON object boundaries
        start_idx = ai_response.find('{')
        end_idx = ai_response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            ai_response = ai_response[start_idx:end_idx+1]
        
        return ai_response
        
    except Exception as e:
        return f"Error generating feedback summary: {str(e)}"
    finally:
        if conn:
            conn.close()

# Original test code (keeping for reference)
if __name__ == "__main__":
    # Test the feedback summary function
    test_session_id = "SES1"  # Replace with actual session ID for testing
    summary = generate_feedback_summary(test_session_id)
    print("AI Feedback Summary:")
    print(summary)
