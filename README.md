# Autonomous Research Assistant 🤖

An AI-powered research assistant that can automatically collect sources, summarize findings, and generate comprehensive research briefs on any given topic.

## Features

- 🔍 Web search for relevant sources
- 📄 Content extraction and processing
- 📝 AI-powered summarization using OpenAI's GPT-4
- 📂 Automatic report generation in Markdown format
- 📊 Source tracking and citation

## Prerequisites

- Python 3.8+
- OpenAI API key
- Serper API key (free tier available at [serper.dev](https://serper.dev/))

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SERPER_API_KEY=your_serper_api_key_here
   ```

## Usage

Run the research assistant:
```bash
python research_assistant.py
```

Enter your research topic when prompted. The assistant will:
1. Search the web for relevant sources
2. Extract and summarize content
3. Generate a comprehensive research report
4. Save the report in the `reports` directory

## Example

```
$ python research_assistant.py
🤖 Autonomous Research Assistant
----------------------------
Enter a topic to research: latest advancements in quantum computing
🔍 Researching: latest advancements in quantum computing
🌐 Searching the web for relevant sources...
📄 Processing source 1/5: Quantum Computing Advancements in 2023
📄 Processing source 2/5: Breakthrough in Quantum Error Correction
📄 Processing source 3/5: The Future of Quantum Computing
✅ Report saved to: reports/research_latest_advancements_in_quantum_computing_20250127_0942.md

📝 Research Report:
==================================================
[Generated report content...]
==================================================
```

## Configuration

Edit the `.env` file to customize:
- `MAX_SOURCES`: Number of sources to include (default: 5)
- `MAX_CONTEXT_LENGTH`: Maximum tokens for content processing (default: 4000)
- `MODEL_NAME`: OpenAI model to use (default: gpt-4-1106-preview)

## License

MIT
