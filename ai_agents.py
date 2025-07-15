import os
import google.generativeai as genai
from dotenv import load_dotenv
import time
import streamlit as st
from typing import Optional, List
import logging

# Import the RL agent
from rl_agent import rl_agent

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
else:
    model = None

def validate_api_key() -> bool:
    """
    Improved API key validation with better error handling and caching.
    
    Returns:
        bool: True if API key is valid and working
    """
    global model  # ← Move global declaration to the top
    
    # Check if API key exists first
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "":
        logger.warning("GEMINI_API_KEY not found in environment variables")
        return False
    
    # Check if API key has valid format (basic check)
    if not api_key.startswith("AIza") or len(api_key) < 35:
        logger.warning("GEMINI_API_KEY appears to have invalid format")
        return False
    
    # Use Streamlit session state to cache validation result
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = None
        st.session_state.api_key_last_checked = None
        st.session_state.cached_api_key = None
    
    # Check if API key has changed
    if st.session_state.cached_api_key != api_key:
        st.session_state.api_key_validated = None
        st.session_state.cached_api_key = api_key
        logger.info("API key changed, clearing validation cache")
    
    # Check if we have a recent validation (cache for 5 minutes)
    current_time = time.time()
    if (st.session_state.api_key_validated is not None and 
        st.session_state.api_key_last_checked is not None and
        current_time - st.session_state.api_key_last_checked < 300):  # 5 minutes
        return st.session_state.api_key_validated
    
    # Perform actual validation
    try:
        # Ensure model is configured
        if model is None:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # Make a minimal test request with timeout
        test_response = model.generate_content(
            "Hi", 
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=5,
                temperature=0.1,
            )
        )
        
        # Check if response is valid
        is_valid = bool(test_response and test_response.text)
        
        # Cache the result
        st.session_state.api_key_validated = is_valid
        st.session_state.api_key_last_checked = current_time
        
        if is_valid:
            logger.info("API key validation successful")
        else:
            logger.warning("API key validation failed - no response text")
            
        return is_valid
        
    except Exception as e:
        # Log the specific error for debugging
        error_msg = str(e)
        logger.error(f"API key validation error: {error_msg}")
        
        # Handle specific error types
        if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
            # Definitely invalid API key
            st.session_state.api_key_validated = False
            st.session_state.api_key_last_checked = current_time
            return False
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            # Rate limit 
            logger.warning("API rate limit or quota exceeded, assuming valid key")
            return True
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            # Network issue 
            logger.warning("Network issue during validation, assuming valid key")
            return True
        else:
            logger.warning("Temporary API issue during validation, assuming valid key")
            return True

def get_adaptive_writer_prompt(content: str, style_preference: str, rl_instructions: str) -> str:
    """
    Generate adaptive writer prompt based on RL learning
    """
    base_prompt = f"""
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
    """
    
    # Add RL-based adaptive instructions
    if rl_instructions:
        base_prompt += f"""
    
    ADAPTIVE LEARNING INSTRUCTIONS (Based on User Feedback):
    {rl_instructions}
    """
    
    base_prompt += f"""
    
    Original Content:
    {content}
    
    Please provide the enhanced version:
    """
    
    return base_prompt

def get_adaptive_reviewer_prompt(content: str, focus_areas: List[str], rl_instructions: str) -> str:
    """
    Generate adaptive reviewer prompt based on RL learning
    """
    focus_text = ", ".join(focus_areas)
    
    base_prompt = f"""
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
    """
    
    # Add RL-based adaptive instructions
    if rl_instructions:
        base_prompt += f"""
    
    ADAPTIVE LEARNING INSTRUCTIONS (Based on User Feedback):
    {rl_instructions}
    """
    
    base_prompt += f"""
    
    Content to Review:
    {content}
    
    Please provide the polished version of the content without explaining the changes made :
    """
    
    return base_prompt

def ai_writer(content: str, style_preference: str = "modern") -> str:
    """
    AI Writer agent that rewrites content in an engaging style.
    Enhanced with RL-based prompt adaptation.
    
    Args:
        content (str): Original content to rewrite
        style_preference (str): Writing style preference
    
    Returns:
        str: Rewritten content
    """
    global model
    
    if not content or len(content.strip()) < 10:
        return "Error: Content too short or empty for AI processing."
    
    # Check API key before processing
    if not validate_api_key():
        return "Error: Invalid or missing Gemini API key. Please check your configuration."
    
    try:
        # Get adaptive instructions from RL agent
        rl_instructions = rl_agent.get_adaptive_prompt_instructions(agent_type="writer")
        
        # Generate adaptive prompt
        prompt = get_adaptive_writer_prompt(content, style_preference, rl_instructions)
        
        # Log RL integration (for debugging)
        if rl_instructions:
            logger.info(f"AI Writer using RL instructions: {rl_instructions[:100]}...")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.7,
            )
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Error: AI Writer could not generate content."
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"AI Writer error: {error_msg}")
        
        # Provide more specific error messages
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return "Error: API quota exceeded. Please try again later or check your API limits."
        elif "API_KEY_INVALID" in error_msg:
            return "Error: Invalid API key. Please check your GEMINI_API_KEY configuration."
        else:
            return f"Error in AI Writer: {error_msg}"

def ai_reviewer(content: str, focus_areas: list = None) -> str:
    """
    AI Reviewer agent that improves grammar, clarity, and overall quality.
    Enhanced with RL-based prompt adaptation.
    
    Args:
        content (str): Content to review and improve
        focus_areas (list): Specific areas to focus on during review
    
    Returns:
        str: Reviewed and improved content
    """
    global model
    
    if not content or len(content.strip()) < 10:
        return "Error: Content too short or empty for AI review."
    
    # Check API key before processing
    if not validate_api_key():
        return "Error: Invalid or missing Gemini API key. Please check your configuration."
    
    if focus_areas is None:
        focus_areas = ["grammar", "clarity", "flow", "consistency"]
    
    try:
        # Get adaptive instructions from RL agent
        rl_instructions = rl_agent.get_adaptive_prompt_instructions(agent_type="reviewer")
        
        # Generate adaptive prompt
        prompt = get_adaptive_reviewer_prompt(content, focus_areas, rl_instructions)
        
        # Log RL integration (for debugging)
        if rl_instructions:
            logger.info(f"AI Reviewer using RL instructions: {rl_instructions[:100]}...")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4000,
                temperature=0.5,
            )
        )
        
        if response and response.text:
            return response.text.strip()
        else:
            return "Error: AI Reviewer could not process content."
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"AI Reviewer error: {error_msg}")
        
        # Provide more specific error messages
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return "Error: API quota exceeded. Please try again later or check your API limits."
        elif "API_KEY_INVALID" in error_msg:
            return "Error: Invalid API key. Please check your GEMINI_API_KEY configuration."
        else:
            return f"Error in AI Reviewer: {error_msg}"

def get_content_analysis(content: str) -> dict:
    """
    Analyze content and provide insights.
    
    Args:
        content (str): Content to analyze
    
    Returns:
        dict: Analysis results
    """
    global model
    
    # Check API key before processing
    if not validate_api_key():
        return {"error": "Invalid or missing Gemini API key. Please check your configuration."}
    
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
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.3,
            )
        )
        
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
        error_msg = str(e)
        logger.error(f"Content analysis error: {error_msg}")
        
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return {"error": "API quota exceeded. Please try again later."}
        elif "API_KEY_INVALID" in error_msg:
            return {"error": "Invalid API key. Please check your GEMINI_API_KEY configuration."}
        else:
            return {"error": f"Analysis error: {error_msg}"}

def batch_process(original_content: str, style_preference: str = "modern", focus_areas: list = None) -> dict:
    """
    Process content through both AI agents in sequence.
    Enhanced with RL learning integration.
    
    Args:
        original_content (str): Original content to process
        style_preference (str): Writing style preference
        focus_areas (list): Review focus areas
    
    Returns:
        dict: Results from both agents with RL metadata
    """
    results = {
        "original": original_content,
        "writer_output": "",
        "reviewer_output": "",
        "processing_time": 0,
        "status": "processing",
        "rl_suggestions": {},
        "adaptive_instructions_used": False
    }
    
    # Check API key before processing
    if not validate_api_key():
        results["status"] = "error"
        results["error"] = "Invalid or missing Gemini API key. Please check your configuration."
        return results
    
    # Get RL suggestions for this processing session
    rl_suggestions = rl_agent.get_smart_suggestions()
    results["rl_suggestions"] = rl_suggestions
    
    # Check if we have enough learning data to use adaptive instructions
    if rl_agent.state["total_feedback"] >= 3:
        results["adaptive_instructions_used"] = True
        logger.info("Using adaptive instructions based on RL learning")
    
    start_time = time.time()
    
    try:
        # Run AI Writer
        print("🔄 Running AI Writer...")
        results["writer_output"] = ai_writer(original_content, style_preference)
        
        # Check if writer failed
        if results["writer_output"].startswith("Error:"):
            results["status"] = "error"
            results["error"] = results["writer_output"]
            return results
        
        # Small delay to avoid rate limiting
        time.sleep(1)
        
        # Run AI Reviewer
        print("🔄 Running AI Reviewer...")
        results["reviewer_output"] = ai_reviewer(results["writer_output"], focus_areas)
        
        # Check if reviewer failed
        if results["reviewer_output"].startswith("Error:"):
            results["status"] = "error"
            results["error"] = results["reviewer_output"]
            return results
        
        results["processing_time"] = round(time.time() - start_time, 2)
        results["status"] = "completed"
        
        print(f"✅ Processing completed in {results['processing_time']} seconds")
        
        # Log successful processing with RL metadata
        if results["adaptive_instructions_used"]:
            logger.info(f"Batch processing completed with RL adaptation. Success rate: {rl_suggestions.get('success_rate', 0):.1f}%")
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        results["processing_time"] = round(time.time() - start_time, 2)
        logger.error(f"Batch processing error: {e}")
    
    return results

def get_rl_learning_insights() -> dict:
    """
    Get current RL learning insights for display in the UI
    
    Returns:
        dict: RL learning statistics and insights
    """
    try:
        suggestions = rl_agent.get_smart_suggestions()
        stats = rl_agent.get_learning_stats()
        
        return {
            "status": "enabled",
            "suggestions": suggestions,
            "stats": stats,
            "learning_active": rl_agent.state["total_feedback"] >= 3
        }
    except Exception as e:
        logger.error(f"Error getting RL insights: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def clear_api_validation_cache():
    """
    Clear the API validation cache. Useful for testing or when API key changes.
    """
    if 'api_key_validated' in st.session_state:
        del st.session_state.api_key_validated
    if 'api_key_last_checked' in st.session_state:
        del st.session_state.api_key_last_checked
    if 'cached_api_key' in st.session_state:
        del st.session_state.cached_api_key
    logger.info("API validation cache cleared")

def get_api_status() -> dict:
    """
    Get detailed API status information for debugging.
    
    Returns:
        dict: API status information
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    status = {
        "api_key_exists": bool(api_key),
        "api_key_format_valid": bool(api_key and api_key.startswith("AIza") and len(api_key) >= 35),
        "cached_validation": st.session_state.get('api_key_validated'),
        "last_checked": st.session_state.get('api_key_last_checked'),
        "cache_age_seconds": None
    }
    
    if status["last_checked"]:
        status["cache_age_seconds"] = round(time.time() - status["last_checked"], 2)
    
    return status