import streamlit as st
import json
import os
import time
import uuid
from datetime import datetime
from scraping.scraper import scrape_chapter, validate_url
from ai_agents import ai_writer, ai_reviewer, get_content_analysis, validate_api_key, batch_process, clear_api_validation_cache, get_api_status, get_rl_learning_insights
from vector_store import vector_store
from rl_agent import rl_agent
from voice_support import speak_text, stop_speaking, get_speaking_status

st.set_page_config(
    page_title="Dynamic AI Book Processor", 
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 1rem 0;
    border-bottom: 2px solid #f0f2f6;
    margin-bottom: 2rem;
}
.status-box {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}
.error-box {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;    
}
.info-box {
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}
.search-result {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 0.75rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

os.makedirs("final_versions", exist_ok=True)
os.makedirs("scraping/output", exist_ok=True)

def init_session_state():
    defaults = {
        "scraping_status": "",
        "original_text": "",
        "writer_output": "",
        "reviewer_output": "",
        "url_processed": "",
        "content_analysis": {},
        "chromadb_enabled": False,
        "chromadb_initialized": False,
        "search_results": [],
        "selected_result": None,
        "search_query": ""
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()
rl_agent.load_state()

# Header
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("📚 Dynamic AI Book Processor")
st.markdown("**Transform any chapter URL into publication-ready content**")
st.markdown("*A Human-in-the-Loop system with AI writing, reviewing, and final approval*")
st.markdown('</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🛠️ Control Panel")
    
    if validate_api_key():
        st.success("✅ Gemini API Connected")
    else:
        st.error("❌ Gemini API Key Missing")
        st.info("Add GEMINI_API_KEY to your .env file")
    
    st.markdown("---")
    
    with st.sidebar.expander("🔧 API Debug Info"):
        status = get_api_status()
        st.json(status)
        
        if st.button("🧹 Clear API Cache"):
            clear_api_validation_cache()
            st.success("✅ API validation cache cleared!")
    
    st.subheader("🧠 AI Learning Status")
    rl_insights = get_rl_learning_insights()
    
    if rl_insights["status"] == "enabled":
        stats = rl_insights["stats"]
        suggestions = rl_insights["suggestions"]
        
        if rl_insights["learning_active"]:
            st.success(f"🎯 Active Learning: {stats['success_rate']:.1f}% success rate")
        else:
            st.info("🌱 Learning Mode: Need 3+ feedback entries to activate")
        
        with st.expander("📊 Current AI Suggestions"):
            st.write(f"**Recommended Style:** {suggestions['recommended_style']}")
            st.write(f"**Recommended Focus:** {', '.join(suggestions['recommended_focus_areas'])}")
            st.write(f"**Confidence:** {suggestions['confidence_score']:.1f}/1.0")
            
            if suggestions['learning_insights']:
                st.write("**Learning Insights:**")
                for insight in suggestions['learning_insights']:
                    st.write(f"• {insight}")
        
        with st.expander("📈 Learning Statistics"):
            st.write(f"**Total Feedback:** {stats['total_feedback']}")
            st.write(f"**Good Feedback:** {stats['good_feedback']}")
            st.write(f"**Learning Patterns:** {stats['learning_patterns']}")
            
            if stats['recent_improvements']:
                st.write("**Recent Improvements:**")
                for improvement in stats['recent_improvements']:
                    st.write(f"• {improvement}")
            
            if st.button("🔄 Reset Learning Data", help="Clear all learning data (use with caution)"):
                rl_agent.reset_learning()
                st.success("🔄 Learning data reset!")
                st.rerun()
    else:
        st.error("❌ RL Learning system error")
    
    st.subheader("🔍 Semantic Search")
    chromadb_toggle = st.checkbox(
        "Enable ChromaDB",
        value=st.session_state.chromadb_enabled,
        help="Enable ChromaDB for searching and storing processed chapters"
    )
    
    if chromadb_toggle != st.session_state.chromadb_enabled:
        st.session_state.chromadb_enabled = chromadb_toggle
        if chromadb_toggle:
            with st.spinner("Initializing ChromaDB..."):
                if vector_store.initialize():
                    st.session_state.chromadb_initialized = True
                    st.success("✅ ChromaDB Initialized Successfully")
                    stats = vector_store.get_collection_stats()
                    if stats["status"] == "enabled":
                        st.info(f"📊 Stored chapters: {stats['total_chapters']}")
                else:
                    st.error("❌ ChromaDB Failed to Initialize")
                    st.session_state.chromadb_enabled = False
                    st.session_state.chromadb_initialized = False
        else:
            st.session_state.chromadb_initialized = False
    
    if st.session_state.chromadb_enabled and st.session_state.chromadb_initialized:
        st.markdown("**Search Saved Chapters:**")
        
        search_query = st.text_input(
            "Search by theme/content:",
            value=st.session_state.search_query,
            placeholder="e.g., 'romance scene', 'character development', 'chapter 1'",
            key="search_input"
        )
        
        col_search, col_clear = st.columns([3, 1])
        
        with col_search:
            if st.button("🔍 Search", type="primary"):
                if search_query.strip():
                    st.session_state.search_query = search_query
                    with st.spinner("Searching chapters..."):
                        st.session_state.search_results = vector_store.search_chapters(search_query, n_results=10)
                    st.rerun()
                else:
                    st.warning("Please enter a search query")
        
        with col_clear:
            if st.button("🗑️ Clear"):
                st.session_state.search_results = []
                st.session_state.search_query = ""
                st.session_state.selected_result = None
                st.rerun()
        
        if st.session_state.search_results:
            st.markdown(f"**Found {len(st.session_state.search_results)} results:**")
            
            for i, result in enumerate(st.session_state.search_results):
                with st.expander(f"📖 Result {i+1} (Score: {result['similarity_score']:.2f})"):
                    metadata = result['metadata']
                    
                    st.write(f"**Source:** {metadata.get('source_url', 'Unknown')[:50]}...")
                    st.write(f"**Date:** {metadata.get('timestamp', 'N/A')}")
                    st.write(f"**Style:** {metadata.get('processing_style', 'N/A')}")
                    st.write(f"**Words:** {metadata.get('word_count', 'N/A')}")
                    
                    st.write("**Preview:**")
                    st.text_area("", result['content'], height=100, disabled=True, key=f"preview_{i}")
                    
                    if st.button(f"📥 Load This Chapter", key=f"load_{i}"):
                        st.session_state.original_text = result['full_content']
                        st.session_state.writer_output = result['full_content']
                        st.session_state.reviewer_output = result['full_content']
                        st.session_state.url_processed = metadata.get('source_url', 'Loaded from search')
                        st.session_state.scraping_status = "loaded_from_search"
                        st.success("✅ Chapter loaded from search results!")
                        st.rerun()
        
        with st.expander("📊 Collection Management"):
            stats = vector_store.get_collection_stats()
            if stats["status"] == "enabled":
                st.write(f"**Total Chapters:** {stats['total_chapters']}")
                st.write(f"**Collection:** {stats['collection_name']}")
                
                if st.button("📋 View All Chapters"):
                    all_chapters = vector_store.get_all_chapters()
                    if all_chapters:
                        st.write("**All Stored Chapters:**")
                        for chapter in all_chapters[:10]:
                            metadata = chapter['metadata']
                            st.write(f"• {metadata.get('timestamp', 'Unknown')} - {metadata.get('source_url', 'Unknown')[:40]}...")
                    else:
                        st.info("No chapters stored yet.")
    
    st.markdown("---")
    
    st.subheader("📎 Chapter URL")
    chapter_url = st.text_input(
        "Paste Chapter URL Here:",
        placeholder="https://en.wikisource.org/wiki/Your_Chapter",
        help="Supports Wikisource, Project Gutenberg, Archive.org, and other text sources"
    )
    
    if chapter_url:
        if validate_url(chapter_url):
            st.success("✅ Valid URL format")
        else:
            st.error("❌ Invalid URL format")
    
    st.markdown("---")
    
    st.subheader("⚙️ Processing Options")
    
    style_preference = st.selectbox(
        "Writing Style:",
        ["modern", "classic", "contemporary", "literary", "casual"],
        help="Choose the writing style for AI rewriting"
    )
    
    focus_areas = st.multiselect(
        "Review Focus Areas:",
        ["grammar", "clarity", "flow", "consistency", "style", "engagement"],
        default=["grammar", "clarity", "flow"],
        help="Select areas for AI reviewer to focus on"
    )
    
    st.markdown("---")
    
    st.subheader("🚀 Actions")
    
    if st.button("🔄 Scrape & Process Chapter", type="primary"):
        if not chapter_url:
            st.error("Please enter a chapter URL first!")
        elif not validate_url(chapter_url):
            st.error("Please enter a valid URL!")
        else:
            with st.spinner("🔄 Processing chapter..."):
                st.session_state.scraping_status = "scraping"
                scraped_data = scrape_chapter(chapter_url)
                
                if scraped_data["status"] == "success":
                    st.session_state.original_text = scraped_data["content"]
                    st.session_state.url_processed = chapter_url
                    st.session_state.scraping_status = "scraped"
                    
                    results = batch_process(
                        scraped_data["content"], 
                        style_preference, 
                        focus_areas
                    )
                    
                    if results["status"] == "completed":
                        st.session_state.writer_output = results["writer_output"]
                        st.session_state.reviewer_output = results["reviewer_output"]
                        st.session_state.content_analysis = get_content_analysis(scraped_data["content"])
                        st.session_state.scraping_status = "completed"
                        st.success(f"✅ Processing completed in {results['processing_time']}s")
                        st.rerun()
                    else:
                        st.error(f"❌ AI Processing failed: {results.get('error', 'Unknown error')}")
                else:
                    st.error(f"❌ Scraping failed: {scraped_data.get('error', 'Unknown error')}")
                    st.session_state.scraping_status = "error"
    
    if st.session_state.original_text:
        if st.button("🤖 Re-run AI Agents Only"):
            with st.spinner("🔄 Re-running AI agents..."):
                results = batch_process(
                    st.session_state.original_text, 
                    style_preference, 
                    focus_areas
                )
                
                if results["status"] == "completed":
                    st.session_state.writer_output = results["writer_output"]
                    st.session_state.reviewer_output = results["reviewer_output"]
                    st.success("✅ AI agents re-run completed!")
                    st.rerun()
                else:
                    st.error(f"❌ AI re-processing failed: {results.get('error', 'Unknown error')}")
    
    st.markdown("---")
    
    st.subheader("💾 Save Options")
    
    if st.session_state.reviewer_output:
        if st.button("📝 Quick Save"):
            version_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"final_chapter_{timestamp}_{version_id}.txt"
            
            content = f"""[FINAL VERSION]
Timestamp: {timestamp}
Version ID: {version_id}
Source URL: {st.session_state.url_processed}

{st.session_state.reviewer_output}
"""
            
            with open(f"final_versions/{file_name}", "w", encoding="utf-8") as f:
                f.write(content)
            
            if st.session_state.chromadb_enabled and st.session_state.chromadb_initialized:
                metadata = {
                    "timestamp": timestamp,
                    "version_id": version_id,
                    "source_url": st.session_state.url_processed,
                    "title": f"Chapter {timestamp}",
                    "processing_style": style_preference,
                    "focus_areas": ', '.join(focus_areas),
                    "word_count": len(st.session_state.reviewer_output.split()),
                    "character_count": len(st.session_state.reviewer_output),
                    "save_type": "quick_save"
                }
                
                if vector_store.add_chapter(st.session_state.reviewer_output, metadata):
                    st.success(f"✅ Saved as `{file_name}` and added to ChromaDB")
                else:
                    st.success(f"✅ Saved as `{file_name}` (ChromaDB save failed)")
            else:
                st.success(f"✅ Saved as `{file_name}`")

if st.session_state.scraping_status in ["completed", "loaded_from_search"] and st.session_state.original_text:
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.info(f"📊 **Word Count:** {len(st.session_state.original_text.split())}")
    
    with col_info2:
        if st.session_state.content_analysis:
            reading_time = st.session_state.content_analysis.get("estimated_reading_time", "N/A")
            st.info(f"⏱️ **Reading Time:** {reading_time} min")
        else:
            word_count = len(st.session_state.original_text.split())
            reading_time = max(1, word_count // 200)  
            st.info(f"⏱️ **Reading Time:** ~{reading_time} min")
    
    with col_info3:
        source_display = st.session_state.url_processed[:30] + "..." if len(st.session_state.url_processed) > 30 else st.session_state.url_processed
        st.info(f"🔗 **Source:** {source_display}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📄 Original Content")
        st.text_area(
            "Scraped Text",
            st.session_state.original_text,
            height=450,
            disabled=True,
            key="original_display"
        )
        
        if st.session_state.content_analysis:
            with st.expander("📊 Content Analysis"):
                analysis = st.session_state.content_analysis
                st.write(f"**Word Count:** {analysis.get('word_count', 'N/A')}")
                st.write(f"**Character Count:** {analysis.get('character_count', 'N/A')}")
                st.write(f"**Est. Reading Time:** {analysis.get('estimated_reading_time', 'N/A')} min")
                if "analysis" in analysis:
                    st.write("**AI Analysis:**")
                    st.write(analysis["analysis"])
    
    with col2:
        st.subheader("✍️ AI Writer Output")
        st.session_state.writer_output = st.text_area(
            "Enhanced Text (Editable)",
            st.session_state.writer_output,
            height=450,
            key="writer_edit"
        )
    
    with col3:
        st.subheader("🧐 AI Reviewer Output")
        st.session_state.reviewer_output = st.text_area(
            "Final Text (Editable)",
            st.session_state.reviewer_output,
            height=450,
            key="reviewer_edit"
        )
    
    st.markdown("---")
    col_voice1, col_voice2, col_status = st.columns([1,1,2])
    
    with col_voice1:
        if st.button("🔊 Listen to Final Output", disabled=get_speaking_status()):
            if st.session_state.reviewer_output.strip():
                speak_text(st.session_state.reviewer_output)
                time.sleep(0.1)
                st.rerun() 
            else:
                st.warning("No content to read!")
    
    with col_voice2:
        if st.button("⏹️ Stop Voice", disabled=not get_speaking_status()):
            stop_speaking()
            time.sleep(0.1)
            st.rerun()
    
    with col_status:
        if get_speaking_status():
            st.info("🔊 Currently speaking...")
        else:
            st.info("🔇 Ready to speak")
    
    st.markdown("### 🧠 Rate AI Output")
    col_rate, col_submit = st.columns([1,2])
    with col_rate:
        rating = st.radio("How do you rate the final output?",["Good","Bad"], key="ai_rating")
    with col_submit:
        if st.button("✅ Submit Feedback"):
            metadata = {
                "source_url": st.session_state.url_processed,
                "processing_time": time.time(),
                "word_count": len(st.session_state.reviewer_output.split()),
                "character_count": len(st.session_state.reviewer_output)
            }
            
            rl_agent.update(
                rating=rating,
                output=st.session_state.reviewer_output,
                style_preference=style_preference,
                focus_areas=focus_areas,
                metadata=metadata
            )
            
            st.success("✅ Feedback recorded. Thanks for helping us improve!")
            
            new_suggestions = get_rl_learning_insights()
            if new_suggestions["status"] == "enabled":
                new_stats = new_suggestions["stats"]
                st.info(f"📈 Updated: {new_stats['success_rate']:.1f}% success rate ({new_stats['total_feedback']} total feedback)")

if st.session_state.scraping_status == "completed":
    st.markdown("### 🧠 AI Learning Insights")
    
    col_rl1, col_rl2 = st.columns(2)
    
    with col_rl1:
        rl_insights = get_rl_learning_insights()
        if rl_insights["status"] == "enabled" and rl_insights["learning_active"]:
            st.info(f"🎯 AI used learned preferences (Success rate: {rl_insights['stats']['success_rate']:.1f}%)")
        else:
            st.info("🌱 AI learning will activate after 3+ feedback entries")
    
    with col_rl2:
        if rl_insights["status"] == "enabled":
            suggestions = rl_insights["suggestions"]
            if suggestions["learning_insights"]:
                st.info(f"💡 Latest insight: {suggestions['learning_insights'][0]}")
            else:
                st.info("💡 Building learning insights...")
    
    st.markdown("---")
    st.subheader("💬 Final Review & Save")
    
    col_feedback, col_save = st.columns([2, 1])
    
    with col_feedback:
        feedback = st.text_area(
            "Comments & Notes (Optional):",
            placeholder="Add any comments, notes, or feedback about this version...",
            height=100
        )
    
    with col_save:
        st.markdown("**Save Options:**")
        
        if st.button("💾 Save with Feedback", type="primary"):
            version_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"final_chapter_{timestamp}_{version_id}.txt"
            
            content = f"""[FINAL VERSION]
Timestamp: {timestamp}
Version ID: {version_id}
Source URL: {st.session_state.url_processed}
Processing Style: {style_preference}
Focus Areas: {', '.join(focus_areas)}

[FEEDBACK & NOTES]
{feedback}

[FINAL CONTENT]
{st.session_state.reviewer_output}

[PROCESSING HISTORY]
Original Length: {len(st.session_state.original_text.split())} words
Writer Output Length: {len(st.session_state.writer_output.split())} words
Final Length: {len(st.session_state.reviewer_output.split())} words
"""
            
            with open(f"final_versions/{file_name}", "w", encoding="utf-8") as f:
                f.write(content)
            
            if st.session_state.chromadb_enabled and st.session_state.chromadb_initialized:
                metadata = {
                    "timestamp": timestamp,
                    "version_id": version_id,
                    "source_url": st.session_state.url_processed,
                    "title": f"Chapter {timestamp}",
                    "processing_style": style_preference,
                    "focus_areas": ', '.join(focus_areas),
                    "feedback": feedback,
                    "word_count": len(st.session_state.reviewer_output.split()),
                    "character_count": len(st.session_state.reviewer_output),
                    "save_type": "comprehensive_save"
                }
                
                if vector_store.add_chapter(st.session_state.reviewer_output, metadata):
                    st.success(f"📘 Comprehensive version saved as `{file_name}` and added to ChromaDB")
                else:
                    st.success(f"📘 Comprehensive version saved as `{file_name}` (ChromaDB save failed)")
            else:
                st.success(f"📘 Comprehensive version saved as `{file_name}`")
        
        st.download_button(
            label="📥 Download TXT",
            data=st.session_state.reviewer_output,
            file_name=f"chapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        if st.session_state.reviewer_output:
            export_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "source_url": st.session_state.url_processed,
                    "processing_style": style_preference,
                    "focus_areas": focus_areas,
                    "version_id": str(uuid.uuid4())[:8]
                },
                "content": {
                    "original": st.session_state.original_text,
                    "ai_written": st.session_state.writer_output,
                    "final_reviewed": st.session_state.reviewer_output
                },
                "feedback": feedback,
                "analysis": st.session_state.content_analysis
            }
            
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"chapter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

elif st.session_state.scraping_status == "error":
    st.error("❌ There was an error processing the URL. Please check the URL and try again.")

else:
    st.markdown("""
    ## 🚀 How to Use
    
    1. **Enable ChromaDB** (Optional): Toggle semantic search for saved chapters
    2. **Enter URL**: Paste any chapter URL in the sidebar
    3. **Configure**: Choose writing style and review focus areas
    4. **Process**: Click "Scrape & Process Chapter" to run the full pipeline
    5. **Review**: Edit the AI outputs as needed
    6. **Save**: Save the final version with optional feedback
    7. **Search**: Use semantic search to find and reuse saved chapters
    
    ### 🌐 Supported Sources
    - **Wikisource** - Free literary texts
    - **Project Gutenberg** - Public domain books
    - **Archive.org** - Digital library content
    - **And many more** - Generic web scraping support
    
    ### ✨ Features
    - **Dynamic scraping** from any URL
    - **AI-powered rewriting** with style preferences
    - **Professional reviewing** with focus areas
    - **Human oversight** with editable outputs
    - **Version control** with timestamps and IDs
    - **Export options** in multiple formats
    - **Semantic search** of saved chapters (ChromaDB)
    - **Content management** and reuse capabilities
    """)
    
    if os.path.exists("final_versions") and os.listdir("final_versions"):
        st.markdown("### 📁 Recent Saved Versions")
        files = sorted(os.listdir("final_versions"), reverse=True)[:5]
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join("final_versions", file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                st.write(f"📄 `{file}` - {mod_time.strftime('%Y-%m-%d %H:%M')}")

st.markdown("---")
st.markdown("""
<div class="footer">
<p><strong>Dynamic AI Book Processor - Transform any chapter into publication-ready content</strong> | Created by <strong>Balaji V</strong></p>
<p><a href="https://github.com/Balaji1472" target="_blank">View my GitHub</a></p>
</div>
""", unsafe_allow_html=True)