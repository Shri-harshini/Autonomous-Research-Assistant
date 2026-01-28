import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging
from datetime import datetime
from pathlib import Path
import os
import markdown
from jinja2 import Environment, FileSystemLoader, Template
from .base_agent import BaseAgent, AgentMessage

@dataclass
class ReportSection:
    """Data class to store report sections."""
    title: str
    content: str
    subsections: List['ReportSection'] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []

@dataclass
class ReportMetadata:
    """Data class to store report metadata."""
    title: str
    topic: str
    generated_date: str
    author: str
    version: str
    sources_count: int
    confidence_score: float

class OutputGenerator(BaseAgent):
    """
    Output Generator Agent responsible for:
    - Creating well-formatted reports
    - Supporting multiple output formats (HTML, Markdown, PDF)
    - Using customizable templates
    - Including proper source citations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the OutputGenerator with optional configuration."""
        super().__init__(
            name="OutputGenerator",
            description="Generates well-formatted research reports"
        )
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.output_dir = self.config.get("output_dir", "reports")
        self.template_dir = self.config.get("template_dir", "templates")
        self.default_format = self.config.get("default_format", "html")
        self.author = self.config.get("author", "Autonomous Research Assistant")
        self.version = self.config.get("version", "1.0")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = None
    
    def _get_jinja_env(self):
        """Get or create Jinja2 environment."""
        if self.jinja_env is None:
            template_path = Path(self.template_dir)
            if template_path.exists():
                self.jinja_env = Environment(
                    loader=FileSystemLoader(self.template_dir),
                    autoescape=True
                )
            else:
                # Create a simple template if directory doesn't exist
                self.jinja_env = Environment(loader=FileSystemLoader('.'))
        return self.jinja_env
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process report generation request.
        
        Args:
            message: AgentMessage containing synthesis results and format preferences
            
        Returns:
            AgentMessage with report generation results
        """
        try:
            content = message.content_dict
            
            # Extract synthesis data
            synthesis = content.get("synthesis", {})
            output_format = content.get("format", self.default_format)
            include_toc = content.get("include_toc", True)
            custom_template = content.get("template", None)
            
            if not synthesis:
                raise ValueError("No synthesis data provided for report generation")
            
            self.logger.info(f"Generating {output_format} report for topic: {synthesis.get('topic', 'Unknown')}")
            
            # 1. Create report structure
            report_sections = await self.create_report_sections(synthesis)
            
            # 2. Create metadata
            metadata = self.create_metadata(synthesis)
            
            # 3. Generate report based on format
            if output_format.lower() == "html":
                report_content = await self.generate_html_report(
                    metadata, report_sections, include_toc, custom_template
                )
                file_extension = "html"
            elif output_format.lower() == "markdown":
                report_content = await self.generate_markdown_report(
                    metadata, report_sections, include_toc
                )
                file_extension = "md"
            elif output_format.lower() == "pdf":
                # For PDF, we'll first generate HTML then convert
                html_content = await self.generate_html_report(
                    metadata, report_sections, include_toc, custom_template
                )
                report_content = await self.convert_to_pdf(html_content)
                file_extension = "pdf"
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # 4. Save report to file
            filename = self.generate_filename(metadata, file_extension)
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "report": {
                        "filepath": filepath,
                        "filename": filename,
                        "format": output_format,
                        "size": len(report_content),
                        "sections": len(report_sections)
                    }
                },
                metadata={
                    "agent": self.name,
                    "format": output_format,
                    "filepath": filepath
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in OutputGenerator: {str(e)}", exc_info=True)
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def create_report_sections(self, synthesis: Dict[str, Any]) -> List[ReportSection]:
        """
        Create report sections from synthesis data.
        
        Args:
            synthesis: Synthesis results dictionary
            
        Returns:
            List of ReportSection objects
        """
        sections = []
        
        # Executive Summary
        if synthesis.get("executive_summary"):
            sections.append(ReportSection(
                title="Executive Summary",
                content=synthesis["executive_summary"]
            ))
        
        # Key Findings
        key_findings = synthesis.get("key_findings", [])
        if key_findings:
            findings_content = self._format_key_findings(key_findings)
            sections.append(ReportSection(
                title="Key Findings",
                content=findings_content
            ))
        
        # Trends
        trends = synthesis.get("trends", [])
        if trends:
            trends_content = self._format_trends(trends)
            sections.append(ReportSection(
                title="Identified Trends",
                content=trends_content
            ))
        
        # Areas of Agreement
        agreements = synthesis.get("agreements", [])
        if agreements:
            agreements_content = self._format_agreements(agreements)
            sections.append(ReportSection(
                title="Areas of Agreement",
                content=agreements_content
            ))
        
        # Areas of Disagreement
        disagreements = synthesis.get("disagreements", [])
        if disagreements:
            disagreements_content = self._format_disagreements(disagreements)
            sections.append(ReportSection(
                title="Areas of Disagreement",
                content=disagreements_content
            ))
        
        # Knowledge Gaps
        knowledge_gaps = synthesis.get("knowledge_gaps", [])
        if knowledge_gaps:
            gaps_content = self._format_knowledge_gaps(knowledge_gaps)
            sections.append(ReportSection(
                title="Knowledge Gaps",
                content=gaps_content
            ))
        
        # Sources
        if synthesis.get("source_count", 0) > 0:
            sources_content = f"This report is based on {synthesis['source_count']} sources analyzed."
            sections.append(ReportSection(
                title="Sources",
                content=sources_content
            ))
        
        return sections
    
    def _format_key_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format key findings for the report."""
        content = []
        
        # Group by importance
        by_importance = {}
        for finding in findings:
            importance = finding.get("importance", "low")
            if importance not in by_importance:
                by_importance[importance] = []
            by_importance[importance].append(finding)
        
        # Format by importance level
        for importance in ["high", "medium", "low"]:
            if importance in by_importance:
                content.append(f"\n### {importance.title()} Importance Findings\n")
                for i, finding in enumerate(by_importance[importance], 1):
                    confidence = finding.get("confidence", 0)
                    sources = len(finding.get("sources", []))
                    content.append(f"{i}. {finding.get('finding', '')}")
                    content.append(f"   - Confidence: {confidence:.2f}")
                    content.append(f"   - Sources: {sources}")
                    content.append("")
        
        return "\n".join(content)
    
    def _format_trends(self, trends: List[Dict[str, Any]]) -> str:
        """Format trends for the report."""
        content = []
        
        for i, trend in enumerate(trends, 1):
            direction = trend.get("direction", "unknown")
            confidence = trend.get("confidence", 0)
            timeframe = trend.get("timeframe", "unknown")
            
            content.append(f"\n### Trend {i}: {trend.get('trend', '')}\n")
            content.append(f"**Direction:** {direction.title()}")
            content.append(f"**Confidence:** {confidence:.2f}")
            content.append(f"**Timeframe:** {timeframe}")
            
            evidence = trend.get("evidence", [])
            if evidence:
                content.append("\n**Evidence:**")
                for ev in evidence[:2]:  # Limit to 2 evidence items
                    content.append(f"- {ev}")
            
            content.append("")
        
        return "\n".join(content)
    
    def _format_agreements(self, agreements: List[Dict[str, Any]]) -> str:
        """Format agreements for the report."""
        content = []
        
        for i, agreement in enumerate(agreements, 1):
            consensus = agreement.get("consensus_level", 0)
            sources = len(agreement.get("supporting_sources", []))
            
            content.append(f"\n### Agreement {i}: {agreement.get('topic', '')}\n")
            content.append(f"**Consensus Level:** {consensus:.2f}")
            content.append(f"**Supporting Sources:** {sources}")
            
            key_points = agreement.get("key_points", [])
            if key_points:
                content.append("\n**Key Points:**")
                for point in key_points:
                    content.append(f"- {point}")
            
            content.append("")
        
        return "\n".join(content)
    
    def _format_disagreements(self, disagreements: List[Dict[str, Any]]) -> str:
        """Format disagreements for the report."""
        content = []
        
        for i, disagreement in enumerate(disagreements, 1):
            confidence = disagreement.get("confidence", 0)
            
            content.append(f"\n### Disagreement {i}: {disagreement.get('topic', '')}\n")
            content.append(f"**Confidence:** {confidence:.2f}")
            content.append(f"**Explanation:** {disagreement.get('explanation', '')}")
            
            conflicting_views = disagreement.get("conflicting_views", [])
            if conflicting_views:
                content.append("\n**Conflicting Views:**")
                for view in conflicting_views:
                    view_type = view.get("view", "unknown")
                    content.append(f"\n**{view_type.title()} View:**")
                    sentences = view.get("sentences", [])
                    for sentence in sentences[:2]:  # Limit to 2 sentences
                        content.append(f"- {sentence[0] if isinstance(sentence, tuple) else sentence}")
            
            content.append("")
        
        return "\n".join(content)
    
    def _format_knowledge_gaps(self, gaps: List[Dict[str, Any]]) -> str:
        """Format knowledge gaps for the report."""
        content = []
        
        for i, gap in enumerate(gaps, 1):
            importance = gap.get("importance", "low")
            
            content.append(f"\n### Knowledge Gap {i}: {gap.get('gap', '')}\n")
            content.append(f"**Importance:** {importance.title()}")
            
            suggested_research = gap.get("suggested_research", [])
            if suggested_research:
                content.append("\n**Suggested Research:**")
                for research in suggested_research:
                    content.append(f"- {research}")
            
            related_topics = gap.get("related_topics", [])
            if related_topics:
                content.append(f"\n**Related Topics:** {', '.join(related_topics)}")
            
            content.append("")
        
        return "\n".join(content)
    
    def create_metadata(self, synthesis: Dict[str, Any]) -> ReportMetadata:
        """Create report metadata."""
        return ReportMetadata(
            title=f"Research Report: {synthesis.get('topic', 'Unknown Topic')}",
            topic=synthesis.get('topic', 'Unknown Topic'),
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            author=self.author,
            version=self.version,
            sources_count=synthesis.get('source_count', 0),
            confidence_score=self._calculate_overall_confidence(synthesis)
        )
    
    def _calculate_overall_confidence(self, synthesis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the report."""
        scores = []
        
        # Confidence from key findings
        key_findings = synthesis.get("key_findings", [])
        if key_findings:
            avg_finding_confidence = sum(f.get("confidence", 0) for f in key_findings) / len(key_findings)
            scores.append(avg_finding_confidence)
        
        # Confidence from trends
        trends = synthesis.get("trends", [])
        if trends:
            avg_trend_confidence = sum(t.get("confidence", 0) for t in trends) / len(trends)
            scores.append(avg_trend_confidence)
        
        # Consensus level from agreements
        agreements = synthesis.get("agreements", [])
        if agreements:
            avg_consensus = sum(a.get("consensus_level", 0) for a in agreements) / len(agreements)
            scores.append(avg_consensus)
        
        # Return average or default
        return sum(scores) / len(scores) if scores else 0.5
    
    def generate_filename(self, metadata: ReportMetadata, extension: str) -> str:
        """Generate a filename for the report."""
        # Clean topic for filename
        topic_clean = metadata.topic.lower().replace(" ", "_").replace("/", "_").replace(":", "_")
        topic_clean = "".join(c for c in topic_clean if c.isalnum() or c == "_")
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"research_report_{topic_clean}_{timestamp}.{extension}"
    
    async def generate_html_report(self, metadata: ReportMetadata, 
                                 sections: List[ReportSection], 
                                 include_toc: bool = True,
                                 custom_template: Optional[str] = None) -> str:
        """Generate HTML report."""
        env = self._get_jinja_env()
        
        # Prepare template data
        template_data = {
            "title": metadata.title,
            "topic": metadata.topic,
            "generated_date": metadata.generated_date,
            "author": metadata.author,
            "version": metadata.version,
            "sources_count": metadata.sources_count,
            "confidence_score": metadata.confidence_score,
            "sections": [{"title": s.title, "content": s.content} for s in sections],
            "include_toc": include_toc
        }
        
        try:
            # Try to use custom template if specified
            if custom_template and os.path.exists(os.path.join(self.template_dir, custom_template)):
                template = env.get_template(custom_template)
            elif os.path.exists(os.path.join(self.template_dir, "report_template.html")):
                template = env.get_template("report_template.html")
            else:
                # Use built-in template
                template = self._get_default_html_template()
            
            return template.render(**template_data)
            
        except Exception as e:
            self.logger.warning(f"Error using template: {str(e)}. Using default template.")
            template = self._get_default_html_template()
            return template.render(**template_data)
    
    def _get_default_html_template(self) -> Template:
        """Get default HTML template."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007acc;
            padding-bottom: 10px;
        }
        h2 {
            color: #007acc;
            margin-top: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 5px;
        }
        h3 {
            color: #555;
            margin-top: 20px;
        }
        .metadata {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 5px 0;
        }
        .toc a {
            color: #007acc;
            text-decoration: none;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        .confidence {
            background-color: #e8f5e8;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .high-confidence { background-color: #d4edda; }
        .medium-confidence { background-color: #fff3cd; }
        .low-confidence { background-color: #f8d7da; }
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="metadata">
                <strong>Generated:</strong> {{ generated_date }}<br>
                <strong>Author:</strong> {{ author }}<br>
                <strong>Version:</strong> {{ version }}<br>
                <strong>Sources:</strong> {{ sources_count }}<br>
                <strong>Overall Confidence:</strong> {{ "%.2f"|format(confidence_score) }}
            </div>
        </header>
        
        {% if include_toc and sections %}
        <nav class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {% for section in sections %}
                <li><a href="#{{ section.title|lower|replace(' ', '-') }}">{{ section.title }}</a></li>
                {% endfor %}
            </ul>
        </nav>
        {% endif %}
        
        <main>
            {% for section in sections %}
            <section id="{{ section.title|lower|replace(' ', '-') }}">
                <h2>{{ section.title }}</h2>
                <div class="section-content">
                    {{ section.content|safe }}
                </div>
            </section>
            {% endfor %}
        </main>
        
        <footer>
            <hr>
            <p><em>This report was generated automatically by {{ author }} on {{ generated_date }}.</em></p>
        </footer>
    </div>
</body>
</html>
        """
        return Template(template_str)
    
    async def generate_markdown_report(self, metadata: ReportMetadata,
                                     sections: List[ReportSection],
                                     include_toc: bool = True) -> str:
        """Generate Markdown report."""
        lines = []
        
        # Header
        lines.append(f"# {metadata.title}")
        lines.append("")
        
        # Metadata
        lines.append("## Report Metadata")
        lines.append("")
        lines.append(f"- **Generated:** {metadata.generated_date}")
        lines.append(f"- **Author:** {metadata.author}")
        lines.append(f"- **Version:** {metadata.version}")
        lines.append(f"- **Sources:** {metadata.sources_count}")
        lines.append(f"- **Overall Confidence:** {metadata.confidence_score:.2f}")
        lines.append("")
        
        # Table of Contents
        if include_toc and sections:
            lines.append("## Table of Contents")
            lines.append("")
            for section in sections:
                lines.append(f"- [{section.title}](#{section.title.lower().replace(' ', '-')})")
            lines.append("")
        
        # Sections
        for section in sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*This report was generated automatically by {metadata.author} on {metadata.generated_date}.*")
        
        return "\n".join(lines)
    
    async def convert_to_pdf(self, html_content: str) -> str:
        """
        Convert HTML to PDF.
        Note: This is a placeholder implementation.
        In practice, you would use libraries like weasyprint or pdfkit.
        """
        # For now, return the HTML content
        # In a real implementation, you would:
        # 1. Install weasyprint or pdfkit
        # 2. Convert HTML to PDF
        # 3. Return the PDF content
        self.logger.warning("PDF conversion not implemented. Returning HTML content.")
        return html_content

# Example usage
async def test_output_generator():
    """Test function for the OutputGenerator."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    generator = OutputGenerator({
        "output_dir": "test_reports",
        "author": "Test Assistant"
    })
    
    try:
        # Create test synthesis data
        synthesis_data = {
            "topic": "renewable energy adoption",
            "executive_summary": "This synthesis analyzes renewable energy adoption based on multiple sources. Key findings include significant growth in solar and wind energy adoption.",
            "key_findings": [
                {
                    "finding": "Solar power costs have decreased by 89% since 2010",
                    "confidence": 0.9,
                    "sources": ["source1", "source2"],
                    "importance": "high"
                },
                {
                    "finding": "Wind energy provides 10% of global electricity",
                    "confidence": 0.7,
                    "sources": ["source2", "source3"],
                    "importance": "medium"
                }
            ],
            "trends": [
                {
                    "trend": "Increasing adoption of renewable energy",
                    "direction": "increasing",
                    "confidence": 0.8,
                    "timeframe": "2020-2023",
                    "evidence": ["Source 1 data", "Source 2 analysis"]
                }
            ],
            "agreements": [
                {
                    "topic": "Cost reduction in solar energy",
                    "consensus_level": 0.9,
                    "supporting_sources": ["source1", "source2"],
                    "key_points": ["Costs have decreased significantly", "Technology improvements"]
                }
            ],
            "disagreements": [
                {
                    "topic": "Impact on wildlife",
                    "confidence": 0.6,
                    "explanation": "Sources present conflicting information",
                    "conflicting_views": [
                        {
                            "view": "negative",
                            "sentences": ["Wind turbines harm bird populations"]
                        },
                        {
                            "view": "minimal",
                            "sentences": ["Impact is minimal with proper planning"]
                        }
                    ]
                }
            ],
            "knowledge_gaps": [
                {
                    "gap": "Long-term environmental impact",
                    "importance": "high",
                    "suggested_research": ["Long-term studies", "Environmental monitoring"],
                    "related_topics": ["wildlife", "ecosystem"]
                }
            ],
            "source_count": 3
        }
        
        # Test HTML generation
        message = AgentMessage.create(
            role="user",
            content={
                "synthesis": synthesis_data,
                "format": "html",
                "include_toc": True
            }
        )
        
        result = await generator.process(message)
        
        # Get content as dictionary
        result_content = result.content_dict
        
        print("\nOutput Generation Results:")
        print("-" * 50)
        
        if result_content.get("status") == "success":
            report_info = result_content.get("report", {})
            print(f"✅ Report generated successfully!")
            print(f"   Format: {report_info.get('format', '')}")
            print(f"   File: {report_info.get('filename', '')}")
            print(f"   Path: {report_info.get('filepath', '')}")
            print(f"   Size: {report_info.get('size', 0)} bytes")
            print(f"   Sections: {report_info.get('sections', 0)}")
        else:
            print(f"❌ Error: {result_content.get('error', 'Unknown error')}")
        
        # Test Markdown generation
        print("\n" + "="*50)
        print("Testing Markdown generation...")
        
        message_md = AgentMessage.create(
            role="user",
            content={
                "synthesis": synthesis_data,
                "format": "markdown",
                "include_toc": True
            }
        )
        
        result_md = await generator.process(message_md)
        result_md_content = result_md.content_dict
        
        if result_md_content.get("status") == "success":
            report_md_info = result_md_content.get("report", {})
            print(f"✅ Markdown report generated successfully!")
            print(f"   File: {report_md_info.get('filename', '')}")
            print(f"   Path: {report_md_info.get('filepath', '')}")
        else:
            print(f"❌ Error: {result_md_content.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_output_generator())
