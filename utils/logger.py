import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

class ResearchLogger:
    """Custom logger for the research assistant with file and console output."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.logger = logging.getLogger("ResearchAssistant")
        self.logger.setLevel(log_level)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Default log file if none provided
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"research_{timestamp}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.log_file = log_file
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log an info message."""
        self.logger.info(message, extra=extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a debug message."""
        self.logger.debug(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a warning message."""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log an error message."""
        self.logger.error(message, extra=extra, exc_info=True)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a critical message."""
        self.logger.critical(message, extra=extra, exc_info=True)
    
    def log_metric(self, name: str, value: Any, step: Optional[int] = None):
        """Log a metric value for tracking performance."""
        self.logger.info(f"METRIC: {name} = {value} (step: {step if step is not None else 'N/A'}")
    
    def log_phase_start(self, phase_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Log the start of a research phase."""
        self.logger.info(f"PHASE_START: {phase_name}", extra={"metadata": metadata or {}})
    
    def log_phase_end(self, phase_name: str, status: str, metadata: Optional[Dict[str, Any]] = None):
        """Log the end of a research phase."""
        self.logger.info(f"PHASE_END: {phase_name} - {status}", extra={"metadata": metadata or {}})
    
    def log_agent_action(self, agent_name: str, action: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an agent's action."""
        self.logger.debug(f"AGENT_ACTION: {agent_name} - {action}", extra={"metadata": metadata or {}})
    
    def log_source_processed(self, source_url: str, status: str, metadata: Optional[Dict[str, Any]] = None):
        """Log the processing status of a source."""
        self.logger.info(f"SOURCE_PROCESSED: {source_url} - {status}", extra={"metadata": metadata or {}})
    
    def log_research_event(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a custom research event."""
        self.logger.info(f"EVENT:{event_type.upper()} - {message}", extra={"metadata": metadata or {}})
