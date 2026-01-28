from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import json

class AgentMessage(BaseModel):
    role: str
    content: str  # Always stored as JSON string
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):
        # Convert content to JSON string if it's a dictionary
        if 'content' in data and isinstance(data['content'], dict):
            data['content'] = json.dumps(data['content'])
        super().__init__(**data)

    @classmethod
    def create(cls, role: str, content: Union[str, dict], **kwargs):
        """Create a new AgentMessage with automatic content serialization."""
        if isinstance(content, dict):
            content = json.dumps(content)
        return cls(role=role, content=content, **kwargs)

    @property
    def content_dict(self) -> dict:
        """Get content as a dictionary, parsing from JSON if needed."""
        try:
            return json.loads(self.content)
        except (json.JSONDecodeError, TypeError):
            return {"text": self.content}

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.memory = []
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process an incoming message and return a response."""
        pass
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with the agent's name."""
        print(f"[{level}] {self.name}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class AgentConfigurationError(AgentError):
    """Raised when there's an error in agent configuration."""
    pass

class AgentExecutionError(AgentError):
    """Raised when there's an error during agent execution."""
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception
