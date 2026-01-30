# Autonomous Research Assistant (ARA)

The **Autonomous Research Assistant (ARA)** is an AI-powered system that automates the end-to-end research workflow — from discovering reliable web sources to generating well-structured, citation-backed research briefs. Users only need to provide a research topic; ARA autonomously handles retrieval, analysis, and report generation.

This project is designed for students, researchers, and developers who require fast, organized, and reproducible research outputs.

---

## Features

* Automated web search using the Serper API to retrieve relevant and credible sources
* Content extraction and preprocessing to clean, structure, and normalize web data
* AI-powered summarization using OpenAI GPT-4 to identify and synthesize key insights
* Automatic generation of structured research reports in Markdown format
* Transparent source tracking with clear references and citations

---

## Tech Stack

* Python 3.8+
* OpenAI API (GPT-4)
* Serper API for web search

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/your-username/autonomous-research-assistant.git
cd autonomous-research-assistant
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Update the `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

---

## Usage

Run the research assistant using the following command:

```bash
python research_assistant.py
```

When prompted, enter a research topic. The assistant will:

* Search the web for relevant sources
* Extract, clean, and summarize the collected content
* Generate a structured research report
* Save the final report in the `reports/` directory

---

## Example Run

```bash
python research_assistant.py
```

```
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
```

---

## Configuration

ARA behavior can be customized using the `.env` file:

| Variable             | Description                         | Default            |
| -------------------- | ----------------------------------- | ------------------ |
| `MAX_SOURCES`        | Number of web sources to analyze    | 5                  |
| `MAX_CONTEXT_LENGTH` | Maximum tokens processed per source | 4000               |
| `MODEL_NAME`         | OpenAI model used for summarization | gpt-4-1106-preview |

---

## Output

All generated research briefs are stored in the `reports/` directory in Markdown format. These files can be easily reviewed, edited, or converted into other formats such as PDF for further use.

