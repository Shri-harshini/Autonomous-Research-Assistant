# Autonomous Research Assistant - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [API Reference](#api-reference)
8. [Examples](#examples)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)

## Overview

The Autonomous Research Assistant (ARA) is a multi-agent system designed to conduct comprehensive research on any topic. It automates the entire research workflow from information gathering to report generation.

### Key Features
- **Multi-Agent Architecture**: Specialized agents for different research tasks
- **Automated Web Research**: Gathers information from multiple sources
- **Source Verification**: Assesses credibility and fact-checks information
- **Intelligent Synthesis**: Combines information into coherent insights
- **Professional Reports**: Generates well-formatted HTML and Markdown reports
- **Source Management**: Persistent storage and organization of sources
- **Workflow Orchestration**: Coordinates agents for seamless execution

## Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Coordinator                        │
├─────────────────────────────────────────────────────────────┤
│  Web Researcher  │  Verification  │  Synthesizer  │ Output   │
│                 │     Agent      │    Agent     │ Generator │
├─────────────────────────────────────────────────────────────┤
│                   Source Manager                             │
├─────────────────────────────────────────────────────────────┤
│              Database & File Storage                         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Research Request** → Agent Coordinator
2. **Web Research** → Source Collection
3. **Verification** → Credibility Assessment
4. **Synthesis** → Information Integration
5. **Report Generation** → Final Output

## Components

### 1. Agent Coordinator (`agents/agent_coordinator.py`)
**Purpose**: Orchestrates the entire research workflow

**Key Features**:
- Manages agent execution order
- Handles inter-agent communication
- Monitors task progress
- Error handling and recovery

**Methods**:
- `process()`: Execute complete research workflow
- `execute_workflow()`: Run coordinated research steps
- `execute_step()`: Execute individual workflow step

### 2. Web Researcher (`agents/web_researcher.py`)
**Purpose**: Conducts web searches and gathers information

**Key Features**:
- Async web searching
- Content extraction with trafilatura
- Source filtering and ranking
- Mock search provider for testing

**Methods**:
- `web_search()`: Perform web search
- `extract_web_content()`: Extract main content from web pages
- `process_search_results()`: Process and filter results

### 3. Verification Agent (`agents/verification_agent.py`)
**Purpose**: Validates information and assesses source credibility

**Key Features**:
- Domain credibility assessment
- Fact-checking claims
- Bias detection
- Cross-referencing sources

**Methods**:
- `analyze_sources()`: Assess source credibility
- `fact_check_content()`: Verify claims against sources
- `calculate_credibility_score()`: Overall credibility assessment

### 4. Synthesizer Agent (`agents/synthesizer_agent.py`)
**Purpose**: Combines information into coherent insights

**Key Features**:
- Key findings extraction
- Trend identification
- Agreement/disagreement detection
- Knowledge gap analysis

**Methods**:
- `extract_key_findings()`: Identify important findings
- `identify_trends()`: Detect trends in data
- `find_agreements()`: Find consensus areas
- `find_disagreements()`: Identify conflicts

### 5. Output Generator (`agents/output_generator.py`)
**Purpose**: Creates well-formatted research reports

**Key Features**:
- HTML report generation
- Markdown export
- Professional templates
- Table of contents

**Methods**:
- `generate_html_report()`: Create HTML reports
- `generate_markdown_report()`: Create Markdown reports
- `create_report_sections()`: Structure report content

### 6. Source Manager (`agents/source_manager.py`)
**Purpose**: Manages persistent storage of sources

**Key Features**:
- SQLite database storage
- Source deduplication
- Collection management
- Search and filtering

**Methods**:
- `add_sources()`: Add new sources
- `search_sources()`: Search stored sources
- `create_collection()`: Organize sources
- `find_duplicates()`: Detect duplicate content

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd ARA
   ```

2. **Create Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix/MacOS
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Create Necessary Directories**:
   ```bash
   mkdir -p data reports templates
   ```

## Configuration

### Environment Variables (.env)
```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Configuration
MAX_SOURCES=5
MAX_CONTEXT_LENGTH=4000
MODEL_NAME="gpt-4-1106-preview"

# Database
DB_PATH=data/sources.db
STORAGE_DIR=data/sources
```

### Agent Configuration
Each agent can be configured with custom parameters:

```python
config = {
    "web_researcher": {
        "search_provider": "mock",  # or "serpapi"
        "max_results": 5,
        "timeout": 30
    },
    "verification_agent": {
        "high_credibility_threshold": 0.8,
        "medium_credibility_threshold": 0.5
    },
    "synthesizer_agent": {
        "max_findings": 10,
        "max_trends": 5
    },
    "output_generator": {
        "output_dir": "reports",
        "template_dir": "templates"
    },
    "source_manager": {
        "db_path": "data/sources.db",
        "cache_size_limit": 1000
    }
}
```

## Usage

### Basic Usage

1. **Using the Agent Coordinator** (Recommended):
   ```python
   from agents.agent_coordinator import AgentCoordinator
   from agents.base_agent import AgentMessage
   
   coordinator = AgentCoordinator(config)
   
   message = AgentMessage.create(
       role="user",
       content={
           "topic": "artificial intelligence in healthcare",
           "query": "AI applications in medical diagnosis",
           "max_sources": 5,
           "format": "html"
       }
   )
   
   result = await coordinator.process(message)
   print(result.content_dict)
   ```

2. **Using Individual Agents**:
   ```python
   from agents.web_researcher import WebResearcher
   
   researcher = WebResearcher()
   message = AgentMessage.create(
       role="user",
       content={
           "query": "renewable energy trends",
           "max_results": 3
       }
   )
   
   result = await researcher.process(message)
   ```

### Command Line Interface

Run the complete system:
```bash
python main.py --topic "AI in healthcare" --format html
```

Run individual agents:
```bash
python -m agents.web_researcher
python -m agents.verification_agent
python -m agents.synthesizer_agent
python -m agents.output_generator
python -m agents.source_manager
```

### Integration Tests
```bash
python tests/integration_tests.py
```

## API Reference

### AgentMessage
The standard message format for agent communication.

```python
message = AgentMessage.create(
    role="user",
    content={
        "command": "add_sources",
        "sources": [...]
    }
)
```

### Common Response Format
```python
{
    "status": "success|error",
    "data": {...},
    "metadata": {
        "agent": "agent_name",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### Web Researcher API
- **Input**: `{"query": str, "max_results": int, "domains": list}`
- **Output**: `{"results": [{"title", "url", "snippet", "content"}]}`

### Verification Agent API
- **Input**: `{"content": str, "sources": list}`
- **Output**: `{"verification": {"credibility_score", "source_analysis"}}`

### Synthesizer Agent API
- **Input**: `{"topic": str, "sources": list}`
- **Output**: `{"synthesis": {"key_findings", "trends", "agreements"}}`

### Output Generator API
- **Input**: `{"synthesis": dict, "format": str, "include_toc": bool}`
- **Output**: `{"report": {"filepath", "filename", "format"}}`

### Source Manager API
- **Commands**: `add_sources`, `get_source`, `search_sources`, `create_collection`
- **Output**: Varies by command

## Examples

### Example 1: Basic Research Workflow
```python
import asyncio
from agents.agent_coordinator import AgentCoordinator
from agents.base_agent import AgentMessage

async def research_example():
    coordinator = AgentCoordinator()
    
    try:
        message = AgentMessage.create(
            role="user",
            content={
                "topic": "climate change impacts",
                "query": "effects of climate change on agriculture",
                "max_sources": 5,
                "format": "html"
            }
        )
        
        result = await coordinator.process(message)
        
        if result.content_dict["status"] == "success":
            print("Research completed successfully!")
            workflow_results = result.content_dict["results"]
            
            for step in workflow_results:
                print(f"{step['step']}: {step['status']}")
        
    finally:
        await coordinator.cleanup()

asyncio.run(research_example())
```

### Example 2: Custom Source Management
```python
from agents.source_manager import SourceManager
from agents.base_agent import AgentMessage

async def source_management_example():
    manager = SourceManager()
    
    # Add sources
    sources = [
        {
            "url": "https://example.com/article1",
            "title": "Climate Change Article",
            "content": "Full article content...",
            "credibility_score": 0.8
        }
    ]
    
    add_message = AgentMessage.create(
        role="user",
        content={
            "command": "add_sources",
            "sources": sources
        }
    )
    
    result = await manager.process(add_message)
    print(f"Added {result.content_dict['added']} sources")
    
    # Search sources
    search_message = AgentMessage.create(
        role="user",
        content={
            "command": "search_sources",
            "query": {"domain": "example.com"}
        }
    )
    
    search_result = await manager.process(search_message)
    print(f"Found {search_result.content_dict['count']} sources")
```

### Example 3: Report Generation
```python
from agents.output_generator import OutputGenerator
from agents.base_agent import AgentMessage

async def report_generation_example():
    generator = OutputGenerator()
    
    synthesis_data = {
        "topic": "AI in Healthcare",
        "executive_summary": "AI is transforming healthcare...",
        "key_findings": [
            {
                "finding": "AI improves diagnostic accuracy",
                "confidence": 0.9,
                "sources": ["source1"],
                "importance": "high"
            }
        ],
        "trends": [],
        "agreements": [],
        "disagreements": [],
        "knowledge_gaps": [],
        "source_count": 1
    }
    
    message = AgentMessage.create(
        role="user",
        content={
            "synthesis": synthesis_data,
            "format": "html",
            "include_toc": True
        }
    )
    
    result = await generator.process(message)
    
    if result.content_dict["status"] == "success":
        report_info = result.content_dict["report"]
        print(f"Report generated: {report_info['filepath']}")
```

## Testing

### Running Tests
```bash
# Run all integration tests
python tests/integration_tests.py

# Run specific agent tests
python -m agents.web_researcher
python -m agents.verification_agent
python -m agents.synthesizer_agent
python -m agents.output_generator
python -m agents.source_manager
```

### Test Coverage
The integration tests cover:
- Agent initialization
- Source management operations
- Web research functionality
- Verification processes
- Synthesis capabilities
- Output generation
- Coordinated workflows
- Error handling
- Performance benchmarks
- Data integrity

### Writing Custom Tests
```python
import asyncio
from agents.agent_coordinator import AgentCoordinator
from agents.base_agent import AgentMessage

async def custom_test():
    # Set up test environment
    config = {
        "output_dir": "test_reports",
        "db_path": "test.db"
    }
    
    coordinator = AgentCoordinator(config)
    
    try:
        # Your test logic here
        message = AgentMessage.create(
            role="user",
            content={"topic": "test topic"}
        )
        
        result = await coordinator.process(message)
        
        # Assertions
        assert result.content_dict["status"] == "success"
        print("Test passed!")
        
    finally:
        await coordinator.cleanup()

asyncio.run(custom_test())
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path and virtual environment

2. **Database Errors**:
   - Ensure data directory exists: `mkdir -p data`
   - Check file permissions
   - Delete corrupted database: `rm data/sources.db`

3. **API Key Errors**:
   - Verify API keys in `.env` file
   - Check API key validity and permissions

4. **Timeout Errors**:
   - Increase timeout values in config
   - Check internet connection
   - Verify API endpoints are accessible

5. **Memory Issues**:
   - Reduce `max_sources` parameter
   - Clear source cache regularly
   - Increase system memory if possible

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization
- Use SSD for database storage
- Increase cache size for frequently accessed sources
- Limit concurrent operations
- Use connection pooling for database operations

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `python tests/integration_tests.py`
5. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public methods
- Write unit tests for new features

### Adding New Agents
1. Create new agent file in `agents/` directory
2. Inherit from `BaseAgent` class
3. Implement required `process()` method
4. Add agent to coordinator initialization
5. Write integration tests
6. Update documentation

### Reporting Issues
- Use GitHub Issues for bug reports
- Include error messages and stack traces
- Provide steps to reproduce
- Include system information (Python version, OS)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT API
- Trafilatura for content extraction
- Jinja2 for template rendering
- SQLite for data storage
- aiohttp for async HTTP requests
