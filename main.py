#!/usr/bin/env python3
"""
Autonomous Research Assistant

A multi-agent system for conducting comprehensive research on any given topic.
"""
import asyncio
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from agents.research_orchestrator import ResearchOrchestrator
from utils.logger import ResearchLogger

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_CONFIG = {
    "max_sources": 10,
    "max_tokens": 4000,
    "model_name": "gpt-4-1106-preview",
    "output_dir": "reports",
    "enable_web_search": True,
    "enable_academic_search": True,
    "min_verification_sources": 2,
    "timeout_seconds": 300,  # 5 minutes
}

class ResearchAssistant:
    """Main class for the Autonomous Research Assistant."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the research assistant with configuration."""
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.logger = ResearchLogger()
        self._validate_config()
        
        # Create output directories
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Validate the configuration and check for required API keys."""
        required_keys = ["OPENAI_API_KEY"]
        
        if self.config.get("enable_web_search", False) and not os.getenv("SERPER_API_KEY"):
            self.logger.warning(
                "SERPER_API_KEY not found in environment variables. "
                "Web search will be disabled."
            )
            self.config["enable_web_search"] = False
        
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )
    
    async def research(self, topic: str) -> Dict[str, Any]:
        """
        Conduct research on the given topic.
        
        Args:
            topic: The research topic or question
            
        Returns:
            Dict containing research results and metadata
        """
        self.logger.info(f"Starting research on topic: {topic}")
        
        try:
            # Initialize the research orchestrator
            orchestrator = ResearchOrchestrator(topic, self.config)
            
            # Execute the research workflow
            report = await orchestrator.start_research()
            
            # Save the final report
            output_file = self._save_report(report, topic)
            
            self.logger.info(f"Research completed successfully. Report saved to: {output_file}")
            
            return {
                "status": "completed",
                "report_path": str(output_file),
                "topic": topic,
                "config": self.config
            }
            
        except Exception as e:
            self.logger.error(f"Research failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "topic": topic
            }
    
    def _save_report(self, report: Dict[str, Any], topic: str) -> Path:
        """Save the research report to a file."""
        # Create a filename from the topic
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:50]
        timestamp = self._get_timestamp()
        filename = f"research_{safe_topic}_{timestamp}.md"
        output_path = Path(self.config["output_dir"]) / filename
        
        # Format the report as markdown
        markdown_content = self._format_report(report)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_path
    
    def _format_report(self, report: Dict[str, Any]) -> str:
        """Format the research report as markdown."""
        # This will be implemented with proper markdown formatting
        return json.dumps(report, indent=2)
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in a filename-friendly format."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

async def main():
    """Command-line interface for the research assistant."""
    parser = argparse.ArgumentParser(description="Autonomous Research Assistant")
    parser.add_argument("topic", nargs="?", help="Research topic or question")
    parser.add_argument("--config", help="Path to configuration file (JSON)")
    parser.add_argument("--output-dir", help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Override output directory if specified
    if args.output_dir:
        config["output_dir"] = args.output_dir
    
    # Get topic from command line or prompt
    topic = args.topic
    if not topic:
        topic = input("Enter research topic or question: ").strip()
        if not topic:
            print("Error: No research topic provided")
            return
    
    # Initialize and run the research assistant
    assistant = ResearchAssistant(config)
    result = await assistant.research(topic)
    
    # Print results
    if result["status"] == "completed":
        print(f"\n✅ Research completed successfully!")
        print(f"📄 Report saved to: {result['report_path']}")
    else:
        print(f"\n❌ Research failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
