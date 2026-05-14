# 📚 Dynamic AI Book Processor

**Transform any chapter URL into publication-ready content with AI-powered writing, reviewing, and human oversight.**

A comprehensive Human-in-the-Loop system that scrapes web content, enhances it with AI agents, and provides semantic search capabilities for content management.

## ✨ Features

- **🌐 Universal Web Scraping**: Extract content from any URL (Wikisource, Project Gutenberg, Archive.org, etc.)
- **🤖 Dual AI Agents**: AI Writer for style enhancement + AI Reviewer for grammar and clarity
- **🧠 Reinforcement Learning**: System learns from user feedback to improve output quality
- **🔍 Semantic Search**: ChromaDB integration for storing and searching processed chapters
- **🎙️ Voice Support**: Text-to-speech for listening to final outputs
- **📊 Content Analysis**: Automatic analysis of genre, tone, reading level, and themes
- **💾 Multiple Export Formats**: Save as TXT, JSON, or comprehensive versions with metadata
- **🔄 Real-time Editing**: Edit AI outputs before final approval
- **📈 Learning Insights**: Track AI performance and adaptation over time

## 🎥 Demo Video

**Watch the complete workflow demonstration:**
[📹 View Demo Video](https://drive.google.com/file/d/1t404sVz1x8Rn5mdypO-el_a7VcT__g2S/view?usp=sharing)


## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Gemini API Key (Google AI Studio)

### Installation

1. **Clone the repository**
   ```bash
   https://github.com/Balaji1472/Automated-Book-Publication-Agent.git
   cd Automated-Book-Publication-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   GEMINI_API_KEY="your_gemini_api_key_here" 
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🛠️ Usage

### Basic Workflow

1. **Configure Settings**: Choose writing style (modern, classic, etc.) and review focus areas
2. **Enter URL**: Paste any chapter URL in the sidebar
3. **Process**: Click "Scrape & Process Chapter" to run the full AI pipeline
4. **Review & Edit**: Modify AI outputs as needed
5. **Rate & Save**: Provide feedback and save the final version

### Advanced Features

#### Semantic Search
- Enable ChromaDB for persistent storage
- Search saved chapters by theme, content, or metadata
- Reuse and reference previous work

#### Reinforcement Learning
- System learns from user feedback (Good/Bad ratings)
- Adapts writing style and focus areas based on preferences
- Provides learning insights after 3+ feedback entries

#### Batch Processing
- Process multiple chapters efficiently
- Automatic content analysis and optimization
- Export management with version control

## 📋 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Scraper   │ -> │   AI Writer     │ -> │  AI Reviewer    │
│  (scraper.py)   │    │ (ai_agents.py)  │    │ (ai_agents.py)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ChromaDB      │    │   RL Agent      │    │   Voice TTS     │
│(vector_store.py)│    │ (rl_agent.py)   │    │(voice_support.py)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Writing Styles
- **Modern**: Contemporary language and flow
- **Classic**: Traditional literary style
- **Contemporary**: Current, accessible writing
- **Literary**: Elevated, artistic expression
- **Casual**: Conversational, informal tone

### Review Focus Areas
- **Grammar**: Spelling, punctuation, syntax
- **Clarity**: Sentence structure, readability
- **Flow**: Paragraph transitions, pacing
- **Consistency**: Tone, style, voice
- **Style**: Language enhancement
- **Engagement**: Reader interest optimization

## 📊 API Requirements

- **Gemini API**: Google's generative AI for text processing
- **ChromaDB**: Optional, for semantic search functionality
- **Streamlit**: Web interface framework

## 📁 Project Structure

```
dynamic-ai-book-processor/
├── app.py                 # Main Streamlit application
├── ai_agents.py          # AI Writer and Reviewer agents
├── rl_agent.py           # Reinforcement learning system
├── vector_store.py       # ChromaDB integration
├── voice_support.py      # Text-to-speech functionality
├── scraping/
│   └── scraper.py        # Web scraping utilities
├── final_versions/       # Saved processed chapters
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## 🤖 AI Agents

### AI Writer
- Rewrites content for better engagement
- Maintains original meaning and structure
- Adapts to user-specified writing styles
- Learns from user feedback via RL

### AI Reviewer
- Focuses on grammar, clarity, and flow
- Professional editing quality
- Customizable focus areas
- Preserves author's voice and intent

### RL Agent
- Learns from user ratings (Good/Bad)
- Adapts prompts based on successful patterns
- Provides smart suggestions for processing
- Tracks learning statistics and improvements

## 🔍 Semantic Search

ChromaDB integration enables:
- **Content Storage**: Persistent chapter storage with metadata
- **Similarity Search**: Find chapters by theme or content
- **Metadata Filtering**: Search by date, style, source, etc.
- **Content Reuse**: Load previous chapters for reference

## 📈 Learning System

The RL agent tracks:
- **Success Rate**: Percentage of good vs. bad ratings
- **Style Preferences**: Most successful writing styles
- **Focus Areas**: Most effective review focuses
- **Learning Insights**: Automatically generated improvement suggestions

## 🎯 Supported Sources

- **Wikisource**: Free literary texts and documents
- **Project Gutenberg**: Public domain books and literature
- **Archive.org**: Digital library content
- **Generic Web Pages**: Any text-based content

## 💾 Export Options

- **TXT**: Plain text format
- **JSON**: Structured data with metadata
- **Comprehensive**: Full processing history and feedback

## 🚨 Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure GEMINI_API_KEY is correctly set in .env
   - Check API key format (starts with "AIza")
   - Verify API quota and limits

2. **ChromaDB Issues**
   - Install chromadb: `pip install chromadb`
   - Check disk space for vector storage
   - Clear cache if initialization fails

3. **Scraping Issues**
   - Verify URL format and accessibility
   - Check internet connection
   - Some sites may block automated scraping

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Balaji V**
- GitHub: [@Balaji1472](https://github.com/Balaji1472)

## 🙏 Acknowledgments

- Google Gemini AI for powerful text generation
- ChromaDB for semantic search capabilities
- Streamlit for the intuitive web interface
- The open-source community for inspiration and tools

---

⭐ **Star this repository if you find it useful!** ⭐
