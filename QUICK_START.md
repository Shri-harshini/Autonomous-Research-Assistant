# Quick Start Guide - Autonomous Research Assistant

## Get Started in 5 Minutes

This guide will help you set up and run the Autonomous Research Assistant (ARA) in just a few minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Internet connection (for web research)

## Installation

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd ARA

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (optional for testing)
# OPENAI_API_KEY=your_key_here
# SERPER_API_KEY=your_key_here
```

### 4. Create Directories
```bash
mkdir -p data reports templates
```

## Your First Research

### Method 1: Using the Coordinator (Recommended)
```python
import asyncio
from agents.agent_coordinator import AgentCoordinator
from agents.base_agent import AgentMessage

async def quick_research():
    # Initialize the coordinator
    coordinator = AgentCoordinator()
    
    try:
        # Create research request
        message = AgentMessage.create(
            role="user",
            content={
                "topic": "artificial intelligence in healthcare",
                "query": "AI applications in medical diagnosis",
                "max_sources": 3,
                "format": "html"
            }
        )
        
        # Run research
        print("🔍 Starting research...")
        result = await coordinator.process(message)
        
        # Check results
        if result.content_dict["status"] == "success":
            print("✅ Research completed!")
            
            workflow_results = result.content_dict["results"]
            for step in workflow_results:
                status_icon = "✅" if step["status"] == "completed" else "❌"
                print(f"{status_icon} {step['step'].title()}: {step['status']}")
                
                if step["status"] == "completed" and "result" in step:
                    if step["step"] == "output_generation":
                        report = step["result"]["report"]
                        print(f"   📄 Report: {report['filename']}")
        else:
            print(f"❌ Research failed: {result.content_dict.get('error')}")
    
    finally:
        # Clean up
        await coordinator.cleanup()

# Run the research
asyncio.run(quick_research())
```

### Method 2: Command Line
```bash
python main.py --topic "AI in healthcare" --format html
```

### Method 3: Individual Agents
```python
import asyncio
from agents.web_researcher import WebResearcher
from agents.base_agent import AgentMessage

async def quick_search():
    researcher = WebResearcher()
    
    try:
        message = AgentMessage.create(
            role="user",
            content={
                "query": "renewable energy trends",
                "max_results": 3
            }
        )
        
        result = await researcher.process(message)
        
        if result.content_dict["status"] == "success":
            sources = result.content_dict["results"]
            print(f"Found {len(sources)} sources:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source['title']}")
                print(f"   {source['url']}")
    
    finally:
        await researcher.cleanup()

asyncio.run(quick_search())
```

## Understanding the Results

### Research Workflow Steps
1. **Web Research**: Gathers sources from the web
2. **Verification**: Assesses source credibility
3. **Synthesis**: Combines information into insights
4. **Output Generation**: Creates the final report

### Report Location
Reports are saved in the `reports/` directory with names like:
```
research_report_artificial_intelligence_in_healthcare_20240128_123456.html
```

### Report Contents
- Executive Summary
- Key Findings (with confidence scores)
- Identified Trends
- Areas of Agreement
- Areas of Disagreement
- Knowledge Gaps
- Source References

## Common Use Cases

### 1. Academic Research
```python
message = AgentMessage.create(
    role="user",
    content={
        "topic": "quantum computing applications",
        "query": "quantum computing in cryptography",
        "max_sources": 10,
        "format": "html"
    }
)
```

### 2. Market Research
```python
message = AgentMessage.create(
    role="user",
    content={
        "topic": "electric vehicle market",
        "query": "EV market trends 2024",
        "max_sources": 8,
        "format": "markdown"
    }
)
```

### 3. Technology Analysis
```python
message = AgentMessage.create(
    role="user",
    content={
        "topic": "blockchain technology",
        "query": "blockchain use cases beyond cryptocurrency",
        "max_sources": 5,
        "format": "html"
    }
)
```

## Configuration Options

### Basic Configuration
```python
config = {
    "output_dir": "my_reports",
    "max_sources": 5,
    "format": "html"
}
```

### Advanced Configuration
```python
config = {
    "web_researcher": {
        "search_provider": "serpapi",  # Requires SERPER_API_KEY
        "max_results": 10
    },
    "verification_agent": {
        "high_credibility_threshold": 0.8
    },
    "output_generator": {
        "author": "Your Name",
        "template_dir": "custom_templates"
    }
}
```

## Troubleshooting

### Common Issues

#### "No sources found"
- The mock search provider might return 0 results
- Try a different query or use real API keys
- Check internet connection

#### "ModuleNotFoundError"
```bash
# Install missing dependencies
pip install -r requirements.txt
```

#### Database errors
```bash
# Remove corrupted database
rm data/sources.db
```

#### Permission errors
```bash
# Create directories with proper permissions
mkdir -p data reports templates
chmod 755 data reports templates
```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tips
- Reduce `max_sources` for faster research
- Use SSD for database storage
- Increase timeout values for slow connections

## Next Steps

1. **Explore Features**: Try different output formats (HTML, Markdown)
2. **Customize Templates**: Create custom report templates
3. **Add Real APIs**: Configure SERPER_API_KEY for real web search
4. **Source Management**: Use SourceManager to build knowledge bases
5. **Integration**: Integrate with your applications

## Examples Repository

Check the `examples/` directory for:
- Basic research scripts
- Custom agent configurations
- Integration examples
- Template customization

## Support

- 📖 [Full Documentation](DOCUMENTATION.md)
- 🔧 [API Reference](API_REFERENCE.md)
- 🧪 [Run Tests](python tests/integration_tests.py)
- 📧 Report issues on GitHub

## Quick Reference

| Task | Command | Code |
|------|---------|------|
| Full Research | `python main.py --topic "topic"` | `AgentCoordinator` |
| Web Search Only | `python -m agents.web_researcher` | `WebResearcher` |
| Verify Sources | `python -m agents.verification_agent` | `VerificationAgent` |
| Synthesize Info | `python -m agents.synthesizer_agent` | `SynthesizerAgent` |
| Generate Report | `python -m agents.output_generator` | `OutputGenerator` |
| Manage Sources | `python -m agents.source_manager` | `SourceManager` |
| Run Tests | `python tests/integration_tests.py` | Integration Tests |

## Success! 🎉

You've successfully set up and run the Autonomous Research Assistant! 

What's next?
- Try different research topics
- Customize report templates
- Integrate with your workflow
- Build custom agents

Happy researching! 🚀
