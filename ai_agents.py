import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def ai_writer(content: str, style_preference: str = "modern") -> str:
    """
    AI Writer agent that rewrites content in an engaging style.
    
    Args:
        content (str): Original content to rewrite
        style_preference (str): Writing style preference
    
    Returns:
        str: Rewritten content
    """
    if not content or len(content.strip()) < 10:
        return "Error: Content too short or empty for AI processing."
    
    try:
        prompt = f"""
        You are a professional AI Writer specializing in book content enhancement.
        
        Task: Rewrite the following text in a more engaging, {style_preference}, and readable style while maintaining:
        - All original meaning and key information
        - Proper narrative flow and structure
        - Character development and plot elements
        - Historical or factual accuracy where applicable
        
        Guidelines:
        - Use vivid, descriptive language
        - Improve sentence variety and rhythm
        - Enhance dialogue naturalness
        - Maintain the original tone and genre
        - Keep the same approximate length
        
        Original Content:
        {content}
        
        Please provide the enhanced version:
        """
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Error: AI Writer could not generate content."
            
    except Exception as e:
        return f"Error in AI Writer: {str(e)}"

def ai_reviewer(content: str, focus_areas: list = None) -> str:
    """
    AI Reviewer agent that improves grammar, clarity, and overall quality.
    
    Args:
        content (str): Content to review and improve
        focus_areas (list): Specific areas to focus on during review
    
    Returns:
        str: Reviewed and improved content
    """
    if not content or len(content.strip()) < 10:
        return "Error: Content too short or empty for AI review."
    
    if focus_areas is None:
        focus_areas = ["grammar", "clarity", "flow", "consistency"]
    
    try:
        focus_text = ", ".join(focus_areas)
        
        prompt = f"""
        You are a professional AI Editor and Reviewer with expertise in book publishing.
        
        Task: Review and improve the following content, focusing on: {focus_text}
        
        Specific improvements to make:
        - Fix any grammar, spelling, or punctuation errors
        - Improve sentence clarity and readability
        - Enhance paragraph flow and transitions
        - Ensure consistent tone and style
        - Remove redundancies and improve conciseness
        - Maintain the author's voice and intent
        - Preserve all plot points and character development
        
        Quality standards:
        - Publication-ready prose
        - Smooth narrative flow
        - Professional editing quality
        - Reader engagement optimization
        
        Content to Review:
        {content}
        
        Please provide the polished, publication-ready version:
        """
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Error: AI Reviewer could not process content."
            
    except Exception as e:
        return f"Error in AI Reviewer: {str(e)}"

def get_content_analysis(content: str) -> dict:
    """
    Analyze content and provide insights.
    
    Args:
        content (str): Content to analyze
    
    Returns:
        dict: Analysis results
    """
    try:
        prompt = f"""
        Analyze the following text and provide a brief analysis:
        
        {content[:1000]}...
        
        Provide:
        1. Genre/Type
        2. Tone
        3. Reading Level
        4. Key Themes (max 3)
        5. Improvement Suggestions (max 3)
        
        Format as JSON with keys: genre, tone, reading_level, themes, suggestions
        """
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return {
                "analysis": response.text.strip(),
                "word_count": len(content.split()),
                "character_count": len(content),
                "estimated_reading_time": round(len(content.split()) / 200, 1)  # 200 WPM average
            }
        else:
            return {"error": "Could not analyze content"}
            
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}

def batch_process(original_content: str, style_preference: str = "modern", focus_areas: list = None) -> dict:
    """
    Process content through both AI agents in sequence.
    
    Args:
        original_content (str): Original content to process
        style_preference (str): Writing style preference
        focus_areas (list): Review focus areas
    
    Returns:
        dict: Results from both agents
    """
    results = {
        "original": original_content,
        "writer_output": "",
        "reviewer_output": "",
        "processing_time": 0,
        "status": "processing"
    }
    
    start_time = time.time()
    
    try:
        
        print("🔄 Running AI Writer...")
        results["writer_output"] = ai_writer(original_content, style_preference)
        
        time.sleep(1)
        
        print("🔄 Running AI Reviewer...")
        results["reviewer_output"] = ai_reviewer(results["writer_output"], focus_areas)
        
        results["processing_time"] = round(time.time() - start_time, 2)
        results["status"] = "completed"
        
        print(f"✅ Processing completed in {results['processing_time']} seconds")
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"❌ Error during processing: {e}")
    
    return results

def validate_api_key() -> bool:
    """
    Validate if Gemini API key is properly configured.
    
    Returns:
        bool: True if API key is valid
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False
        
        test_response = model.generate_content("Hello")
        return bool(test_response and test_response.text)
        
    except Exception:
        return False