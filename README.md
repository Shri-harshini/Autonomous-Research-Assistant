## Autonomous Research Assistant ##

An AI-powered research assistant that automates the entire research workflow — from finding reliable sources on the web to generating well-structured, citation-backed research briefs. Just provide a topic and let the assistant do the heavy lifting.

This project is designed for students, researchers, and developers who want fast, organized, and reproducible research outputs.


**Features**

* Automated Web Search – Fetches relevant sources using the Serper API
* Content Extraction & Processing – Cleans and prepares web content for analysis
* AI-Powered Summarization – Uses OpenAI’s GPT‑4 to summarize key insights
* Markdown Report Generation – Creates clean, readable research briefs
* Source Tracking & Citations – Keeps references transparent and traceable

## Tech Stack ##

* Python 3.8+
* OpenAI API (GPT‑4)
* Serper API for web search

## Getting Started ##
 1. Clone the Repository

```bash
git clone https://github.com/your-username/autonomous-research-assistant.git
cd autonomous-research-assistant
```

2. Install Dependencies

```bash
pip install -r requirements.txt
```
3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

## Update `.env` with your API keys: ##

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

 You can get a free Serper API key from serper.dev

## Usage ##

Run the research assistant:

```bash
python research_assistant.py
```

When prompted, enter your research topic. The assistant will:

1. Search the web for relevant sources
2. Extract and summarize content
3. Generate a structured research report
4. Save the report in the `reports/` directory


## Example Run ##

```text
python research_assistant.py
Autonomous Research Assistant
----------------------------
Enter a topic to research: latest advancements in quantum computing

Researching: latest advancements in quantum computing
Searching the web for relevant sources...
Processing source 1/5: Quantum Computing Advancements in 2023
Processing source 2/5: Breakthrough in Quantum Error Correction
Processing source 3/5: The Future of Quantum Computing

 Report saved to:
reports/research_latest_advancements_in_quantum_computing_20250127_0942.md

---

## Configuration ##
 
You can customize the assistant’s behavior via the `.env` file:

| Variable             | Description                         | Default            |
| -------------------- | ----------------------------------- | ------------------ |
| `MAX_SOURCES`        | Number of web sources to analyze    | 5                  |
| `MAX_CONTEXT_LENGTH` | Max tokens per source               | 4000               |
| `MODEL_NAME`         | OpenAI model used for summarization | gpt-4-1106-preview |


## Output ##

All generated research briefs are saved in the **`reports/`** directory in Markdown format, making them easy to read, edit, or convert to PDF.

**
License**

This project is licensed under the MIT License** — feel free to use, modify, and distribute it.

## Why This Project?

This assistant demonstrates how agentic AI, web search, and LLMs can be combined to build practical automation tools. It’s ideal for showcasing skills in:

* AI agents
* Retrieval-Augmented Generation (RAG)
* API integration
* Real-world LLM applications

