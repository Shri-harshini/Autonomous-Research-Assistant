# API Reference - Autonomous Research Assistant

## Overview

This document provides detailed API reference for all components of the Autonomous Research Assistant system.

## Base Classes

### AgentMessage

The standard message format for inter-agent communication.

```python
class AgentMessage(BaseModel):
    role: str
    content: str  # JSON string or dictionary
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### Methods

##### `create(role: str, content: Union[str, dict], **kwargs) -> AgentMessage`
Creates a new AgentMessage with automatic content serialization.

**Parameters:**
- `role`: Message role ("user" or "assistant")
- `content`: Message content (string or dictionary)
- `**kwargs`: Additional metadata

**Returns:** AgentMessage instance

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "query": "climate change",
        "max_results": 5
    }
)
```

##### `content_dict` property
Returns content as a dictionary, parsing from JSON if needed.

**Returns:** Dictionary representation of content

### BaseAgent

Abstract base class for all agents.

```python
class BaseAgent(ABC):
    def __init__(self, name: str, description: str)
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage
```

## Core Agents

### 1. AgentCoordinator

Orchestrates the entire research workflow.

#### Initialization
```python
coordinator = AgentCoordinator(config: Optional[Dict] = None)
```

**Configuration Options:**
- `max_concurrent_tasks`: Maximum concurrent tasks (default: 3)
- `default_timeout`: Default timeout in seconds (default: 300)
- `retry_attempts`: Number of retry attempts (default: 2)

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Executes the complete research workflow.

**Input Format:**
```python
{
    "topic": str,           # Research topic
    "query": str,           # Search query (optional, defaults to topic)
    "max_sources": int,     # Maximum sources to collect (default: 5)
    "format": str           # Output format: "html", "markdown", "pdf"
}
```

**Output Format:**
```python
{
    "status": "success",
    "workflow_id": str,
    "results": [
        {
            "step": str,           # Step name
            "agent": str,          # Agent name
            "status": str,         # "completed" or "error"
            "result": dict,        # Step results
            "duration": float,     # Duration in seconds
            "error": str           # Error message (if failed)
        }
    ]
}
```

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "topic": "artificial intelligence in healthcare",
        "query": "AI medical diagnosis applications",
        "max_sources": 5,
        "format": "html"
    }
)

result = await coordinator.process(message)
```

##### `cleanup()`
Clean up resources and close connections.

### 2. WebResearcher

Conducts web searches and extracts content.

#### Initialization
```python
researcher = WebResearcher(config: Optional[Dict] = None)
```

**Configuration Options:**
- `search_provider`: "mock" or "serpapi" (default: "mock")
- `max_results`: Maximum results per search (default: 5)
- `timeout`: Request timeout in seconds (default: 30)
- `min_content_length`: Minimum content length (default: 500)

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Performs web search and content extraction.

**Input Format:**
```python
{
    "query": str,           # Search query
    "max_results": int,     # Maximum results (optional)
    "domains": list         # Preferred domains (optional)
}
```

**Output Format:**
```python
{
    "status": "success",
    "query": str,
    "results": [
        {
            "title": str,
            "url": str,
            "snippet": str,
            "domain": str,
            "content": str,        # Extracted content
            "confidence": float,   # Content confidence
            "last_updated": str
        }
    ]
}
```

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "query": "renewable energy trends 2024",
        "max_results": 3,
        "domains": ["nature.com", "science.org"]
    }
)

result = await researcher.process(message)
```

##### `cleanup()`
Close HTTP session and clean up resources.

### 3. VerificationAgent

Validates information and assesses source credibility.

#### Initialization
```python
verifier = VerificationAgent(config: Optional[Dict] = None)
```

**Configuration Options:**
- `high_credibility_threshold`: High credibility threshold (default: 0.8)
- `medium_credibility_threshold`: Medium credibility threshold (default: 0.5)

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Verifies content and assesses source credibility.

**Input Format:**
```python
{
    "content": str,         # Content to verify
    "sources": list         # List of source dictionaries
}
```

**Source Dictionary Format:**
```python
{
    "url": str,
    "title": str,
    "content": str,
    "domain": str
}
```

**Output Format:**
```python
{
    "status": "success",
    "verification": {
        "original_content": str,
        "credibility_score": float,    # 0.0 to 1.0
        "fact_checks": [
            {
                "claim": str,
                "sources": list,
                "verification_status": str,  # "verified", "disputed", "unverified"
                "confidence": float,
                "explanation": str
            }
        ],
        "source_analysis": {
            "total_sources": int,
            "high_credibility": int,
            "medium_credibility": int,
            "low_credibility": int,
            "domains": {
                "domain.com": {
                    "credibility_score": float,
                    "authority_level": str,
                    "bias_rating": str,
                    "fact_check_rating": str
                }
            },
            "overall_score": float
        },
        "recommendations": list,
        "warnings": list
    }
}
```

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "content": "AI improves diagnostic accuracy by 30%",
        "sources": [
            {
                "url": "https://nature.com/ai-diagnosis",
                "title": "AI in Medical Diagnosis",
                "content": "Recent studies show AI improves diagnosis..."
            }
        ]
    }
)

result = await verifier.process(message)
```

### 4. SynthesizerAgent

Combines information from multiple sources into coherent insights.

#### Initialization
```python
synthesizer = SynthesizerAgent(config: Optional[Dict] = None)
```

**Configuration Options:**
- `min_sources_for_consensus`: Minimum sources for consensus (default: 2)
- `confidence_threshold`: Confidence threshold (default: 0.6)
- `max_findings`: Maximum findings to return (default: 10)
- `max_trends`: Maximum trends to identify (default: 5)

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Synthesizes information from multiple sources.

**Input Format:**
```python
{
    "topic": str,           # Research topic
    "sources": list         # List of source dictionaries
}
```

**Output Format:**
```python
{
    "status": "success",
    "synthesis": {
        "topic": str,
        "executive_summary": str,
        "key_findings": [
            {
                "finding": str,
                "confidence": float,
                "sources": list,
                "category": str,
                "importance": str      # "high", "medium", "low"
            }
        ],
        "trends": [
            {
                "trend": str,
                "direction": str,      # "increasing", "decreasing", "stable"
                "evidence": list,
                "confidence": float,
                "timeframe": str
            }
        ],
        "agreements": [
            {
                "topic": str,
                "consensus_level": float,
                "supporting_sources": list,
                "key_points": list
            }
        ],
        "disagreements": [
            {
                "topic": str,
                "conflicting_views": list,
                "confidence": float,
                "explanation": str
            }
        ],
        "knowledge_gaps": [
            {
                "gap": str,
                "importance": str,
                "suggested_research": list,
                "related_topics": list
            }
        ],
        "source_count": int,
        "synthesis_date": str
    }
}
```

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "topic": "climate change impacts",
        "sources": verified_sources  # From verification agent
    }
)

result = await synthesizer.process(message)
```

### 5. OutputGenerator

Creates well-formatted research reports.

#### Initialization
```python
generator = OutputGenerator(config: Optional[Dict] = None)
```

**Configuration Options:**
- `output_dir`: Output directory (default: "reports")
- `template_dir`: Template directory (default: "templates")
- `default_format`: Default output format (default: "html")
- `author`: Report author (default: "Autonomous Research Assistant")
- `version`: Report version (default: "1.0")

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Generates reports in various formats.

**Input Format:**
```python
{
    "synthesis": dict,       # Synthesis results from synthesizer
    "format": str,           # "html", "markdown", "pdf"
    "include_toc": bool,     # Include table of contents
    "template": str          # Custom template name (optional)
}
```

**Output Format:**
```python
{
    "status": "success",
    "report": {
        "filepath": str,     # Full path to generated report
        "filename": str,     # Filename only
        "format": str,       # Report format
        "size": int,         # File size in bytes
        "sections": int      # Number of sections
    }
}
```

**Example:**
```python
message = AgentMessage.create(
    role="user",
    content={
        "synthesis": synthesis_results,
        "format": "html",
        "include_toc": True
    }
)

result = await generator.process(message)
```

### 6. SourceManager

Manages persistent storage and retrieval of sources.

#### Initialization
```python
manager = SourceManager(config: Optional[Dict] = None)
```

**Configuration Options:**
- `db_path`: Database file path (default: "data/sources.db")
- `storage_dir`: File storage directory (default: "data/sources")
- `cache_size_limit`: Maximum cache size (default: 1000)
- `duplicate_threshold`: Similarity threshold for duplicates (default: 0.8)

#### Methods

##### `process(message: AgentMessage) -> AgentMessage`
Handles various source management operations.

**Commands:**

###### `add_sources`
Adds new sources to the database.

**Input Format:**
```python
{
    "command": "add_sources",
    "sources": [
        {
            "url": str,
            "title": str,
            "content": str,
            "author": str,          # Optional
            "publish_date": str,    # Optional
            "credibility_score": float,
            "tags": list,
            "metadata": dict
        }
    ]
}
```

**Output Format:**
```python
{
    "status": "success",
    "added": int,
    "duplicates": int,
    "errors": int,
    "source_ids": list,
    "duplicate_ids": list,
    "error_messages": list
}
```

###### `get_source`
Retrieves a specific source.

**Input Format:**
```python
{
    "command": "get_source",
    "source_id": str
}
```

**Output Format:**
```python
{
    "status": "success",
    "source": {
        "id": str,
        "url": str,
        "title": str,
        "content": str,
        "domain": str,
        "author": str,
        "publish_date": str,
        "credibility_score": float,
        "tags": list,
        "metadata": dict
    }
}
```

###### `search_sources`
Searches for sources based on criteria.

**Input Format:**
```python
{
    "command": "search_sources",
    "query": {
        "url": str,              # Optional
        "domain": str,           # Optional
        "title": str,            # Optional
        "content": str,          # Optional
        "tags": list,            # Optional
        "min_credibility": float, # Optional
        "date_from": str,        # Optional
        "date_to": str,          # Optional
        "limit": int,            # Optional, default: 50
        "offset": int            # Optional, default: 0
    }
}
```

**Output Format:**
```python
{
    "status": "success",
    "sources": list,            # List of source dictionaries
    "count": int,
    "query": dict
}
```

###### `create_collection`
Creates a source collection.

**Input Format:**
```python
{
    "command": "create_collection",
    "collection": {
        "name": str,
        "description": str,
        "sources": list,         # List of source IDs
        "metadata": dict
    }
}
```

**Output Format:**
```python
{
    "status": "success",
    "collection": {
        "id": str,
        "name": str,
        "description": str,
        "sources": list,
        "created_date": str,
        "last_updated": str,
        "metadata": dict
    }
}
```

###### `update_source`
Updates an existing source.

**Input Format:**
```python
{
    "command": "update_source",
    "source_id": str,
    "updates": {
        "title": str,            # Optional
        "content": str,          # Optional
        "credibility_score": float, # Optional
        "tags": list,            # Optional
        "metadata": dict         # Optional
    }
}
```

**Output Format:**
```python
{
    "status": "success",
    "updated_fields": list
}
```

###### `delete_source`
Deletes a source.

**Input Format:**
```python
{
    "command": "delete_source",
    "source_id": str
}
```

**Output Format:**
```python
{
    "status": "success",
    "deleted_source": str
}
```

###### `find_duplicates`
Finds duplicate sources.

**Input Format:**
```python
{
    "command": "find_duplicates",
    "sources": list             # List of source dictionaries to check
}
```

**Output Format:**
```python
{
    "status": "success",
    "duplicates": [
        {
            "url": str,
            "title": str,
            "duplicate_of": str
        }
    ],
    "unique_count": int,
    "duplicate_count": int
}
```

###### `get_statistics`
Gets database statistics.

**Input Format:**
```python
{
    "command": "get_statistics"
}
```

**Output Format:**
```python
{
    "status": "success",
    "statistics": {
        "total_sources": int,
        "unique_domains": int,
        "average_credibility": float,
        "total_collections": int,
        "recently_accessed": int,
        "cache_size": int
    }
}
```

## Error Handling

All agents return consistent error responses:

```python
{
    "status": "error",
    "error": "Error message description",
    "metadata": {
        "agent": "agent_name"
    }
}
```

Common error types:
- `ValueError`: Invalid input parameters
- `ConnectionError`: Network issues
- `TimeoutError`: Operation timeout
- `DatabaseError`: Database issues
- `FileNotFoundError`: Missing files

## Async Patterns

All agent methods are async and should be called with await:

```python
import asyncio

async def research_example():
    coordinator = AgentCoordinator()
    try:
        result = await coordinator.process(message)
        return result
    finally:
        await coordinator.cleanup()

# Run the async function
result = asyncio.run(research_example())
```

## Configuration Examples

### Minimal Configuration
```python
config = {
    "output_dir": "reports",
    "db_path": "data/sources.db"
}
```

### Full Configuration
```python
config = {
    "web_researcher": {
        "search_provider": "serpapi",
        "max_results": 10,
        "timeout": 60
    },
    "verification_agent": {
        "high_credibility_threshold": 0.85,
        "medium_credibility_threshold": 0.6
    },
    "synthesizer_agent": {
        "max_findings": 15,
        "max_trends": 8,
        "confidence_threshold": 0.7
    },
    "output_generator": {
        "output_dir": "reports",
        "template_dir": "templates",
        "author": "Custom Research Assistant"
    },
    "source_manager": {
        "db_path": "data/sources.db",
        "cache_size_limit": 2000,
        "duplicate_threshold": 0.9
    },
    "max_concurrent_tasks": 5,
    "default_timeout": 600
}
```

## Best Practices

1. **Always cleanup**: Call `cleanup()` on agents when done
2. **Handle errors**: Check response status before processing results
3. **Use timeouts**: Set appropriate timeouts for network operations
4. **Validate input**: Ensure required fields are present
5. **Use caching**: Leverage source manager caching for performance
6. **Monitor resources**: Watch memory usage with large datasets
7. **Test thoroughly**: Use integration tests to verify workflows
