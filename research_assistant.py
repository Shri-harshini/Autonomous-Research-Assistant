import os
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import markdown
from pathlib import Path
from dotenv import load_dotenv
import tiktoken
from openai import OpenAI
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "serper_api_key": os.getenv("SERPER_API_KEY"),
    "max_sources": int(os.getenv("MAX_SOURCES", 5)),
    "max_context_length": int(os.getenv("MAX_CONTEXT_LENGTH", 4000)),
    "model_name": os.getenv("MODEL_NAME", "gpt-4-1106-preview"),
}

# Initialize OpenAI client
client = OpenAI(api_key=CONFIG["openai_api_key"])

@dataclass
class ResearchSource:
    title: str
    url: str
    content: str
    summary: str = ""

class ResearchAssistant:
    def __init__(self):
        self.sources: List[ResearchSource] = []
        self.encoding = tiktoken.encoding_for_model("gpt-4")

    def search_web(self, query: str) -> List[Dict[str, str]]:
        """Search the web for relevant sources."""
        if not CONFIG["serper_api_key"]:
            raise ValueError("SERPER_API_KEY not found in environment variables")
            
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": CONFIG["max_sources"]
        })
        headers = {
            'X-API-KEY': CONFIG["serper_api_key"],
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        results = response.json()
        
        sources = []
        for result in results.get('organic', [])[:CONFIG["max_sources"]]:
            sources.append({
                'title': result.get('title', 'Untitled'),
                'url': result.get('link', '')
            })
        return sources

    def fetch_webpage_content(self, url: str) -> str:
        """Fetch and clean webpage content."""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return ""

    def summarize_content(self, content: str, query: str) -> str:
        """Summarize content using OpenAI's API."""
        try:
            response = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": f"You are a research assistant. Provide a concise summary of the following content, focusing on aspects relevant to: {query}"},
                    {"role": "user", "content": content[:CONFIG["max_context_length"]]}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Summary unavailable"

    def research_topic(self, topic: str) -> str:
        """Conduct research on a given topic."""
        print(f"🔍 Researching: {topic}")
        
        # Search for sources
        print("🌐 Searching the web for relevant sources...")
        sources = self.search_web(topic)
        
        if not sources:
            return "No relevant sources found for the given topic."
            
        # Process each source
        for i, source in enumerate(sources, 1):
            print(f"📄 Processing source {i}/{len(sources)}: {source['title']}")
            content = self.fetch_webpage_content(source['url'])
            if not content:
                continue
                
            summary = self.summarize_content(content, topic)
            self.sources.append(ResearchSource(
                title=source['title'],
                url=source['url'],
                content=content[:2000],  # Store first 2000 chars
                summary=summary
            ))
        
        return self.generate_report(topic)
    
    def generate_report(self, topic: str) -> str:
        """Generate a research report from the collected sources."""
        if not self.sources:
            return "No valid sources were found to generate a report."
            
        # Prepare source summaries
        source_texts = []
        for i, source in enumerate(self.sources, 1):
            source_text = f"""
            ## Source {i}: {source.title}
            **URL:** {source.url}
            
            **Summary:**
            {source.summary}
            """
            source_texts.append(source_text)
        
        # Generate final report
        try:
            response = client.chat.completions.create(
                model=CONFIG["model_name"],
                messages=[
                    {"role": "system", "content": "You are a research assistant. Generate a comprehensive research report based on the following sources."},
                    {"role": "user", "content": f"""
                    Topic: {topic}
                    
                    Based on the following sources, create a well-structured research report.
                    Include an introduction, key findings, and a conclusion.
                    
                    Sources:
                    {'\n'.join(source_texts)}
                    """}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            self.save_report(topic, report)
            return report
            
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    def save_report(self, topic: str, content: str):
        """Save the research report to a markdown file."""
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Create a filename from the topic
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{reports_dir}/research_{topic[:50].replace(' ', '_')}_{timestamp}.md"
        
        # Save the report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Research Report: {topic}\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(content)
            
            # Add sources section
            f.write("\n## Sources\n\n")
            for i, source in enumerate(self.sources, 1):
                f.write(f"{i}. [{source.title}]({source.url})\n   Summary: {source.summary[:200]}...\n\n")
        
        print(f"✅ Report saved to: {filename}")

def main():
    print("🤖 Autonomous Research Assistant")
    print("----------------------------")
    
    # Check for API keys
    if not CONFIG["openai_api_key"] or CONFIG["openai_api_key"] == "your_openai_api_key_here":
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    if not CONFIG["serper_api_key"] or CONFIG["serper_api_key"] == "your_serper_api_key_here":
        print("❌ Error: SERPER_API_KEY not found in .env file")
        print("Get a free API key from https://serper.dev/")
        return
    
    # Get research topic from user
    topic = input("Enter a topic to research: ").strip()
    if not topic:
        print("❌ Please provide a research topic")
        return
    
    # Conduct research
    assistant = ResearchAssistant()
    report = assistant.research_topic(topic)
    
    # Display results
    print("\n📝 Research Report:")
    print("=" * 50)
    print(report)
    print("=" * 50)

if __name__ == "__main__":
    main()
