import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

# Create a mock SynthesisResult class since we might not have the actual implementation
class SynthesisResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# Create a mock OutputGenerator class
class OutputGenerator:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
        
    async def generate_report(self, topic: str, synthesis: Any, sources: List[Dict], format: str = "html") -> str:
        """Generate a research report in the specified format."""
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate a timestamp for the report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"research_report_{topic.lower().replace(' ', '_')}_{timestamp}.{format}"
        report_path = os.path.join(reports_dir, report_filename)
        
        if format == "html":
            await self._generate_html_report(report_path, topic, synthesis, sources)
        else:
            await self._generate_markdown_report(report_path, topic, synthesis, sources)
            
        return report_path
    
    async def _generate_html_report(self, report_path: str, topic: str, synthesis: Any, sources: List[Dict]) -> None:
        """Generate an HTML report using Jinja2 templates."""
        try:
            from jinja2 import Environment, FileSystemLoader
            
            # Set up the template environment
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template("report_template.html")
            
            # Prepare the context
            context = {
                "title": topic,
                "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "topic": topic,
                "sections": self._prepare_sections(synthesis, sources)
            }
            
            # Render the template
            html_content = template.render(**context)
            
            # Write the report to a file
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
        except ImportError:
            # Fallback to a simple HTML report if Jinja2 is not available
            await self._generate_simple_html(report_path, topic, synthesis, sources)
    
    def _prepare_sections(self, synthesis: Any, sources: List[Dict]) -> List[Dict]:
        """Prepare the sections for the report."""
        sections = []
        
        # Add executive summary
        sections.append({
            "title": "Executive Summary",
            "content": f"<p>{synthesis.overall_summary}</p>"
        })
        
        # Add key findings
        findings_html = "<h3>Key Findings</h3><ul class='findings'>"
        for finding in synthesis.key_findings:
            confidence_class = "high-confidence" if finding["confidence"] > 0.7 else "medium-confidence" if finding["confidence"] > 0.4 else "low-confidence"
            confidence_text = f"<span class='confidence {confidence_class}'>Confidence: {int(finding['confidence'] * 100)}%</span>"
            findings_html += f"<li>{finding['finding']} {confidence_text}</li>"
        findings_html += "</ul>"
        sections.append({
            "title": "Key Findings",
            "content": findings_html
        })
        
        # Add trends
        if hasattr(synthesis, 'trends') and synthesis.trends:
            trends_html = "<h3>Emerging Trends</h3><ul class='trends'>"
            for trend in synthesis.trends:
                trends_html += f"<li>{trend}</li>"
            trends_html += "</ul>"
            sections.append({
                "title": "Emerging Trends",
                "content": trends_html
            })
        
        # Add agreements if they exist
        if hasattr(synthesis, 'agreements') and synthesis.agreements:
            agreements_html = "<h3>Areas of Agreement</h3><ul class='agreements'>"
            for agreement in synthesis.agreements:
                agreements_html += f"<li>{agreement['point']}"
                if 'supporting_sources' in agreement and agreement['supporting_sources']:
                    agreements_html += f" <small>(Supported by {len(agreement['supporting_sources'])} sources)</small>"
                agreements_html += "</li>"
            agreements_html += "</ul>"
            sections.append({
                "title": "Areas of Agreement",
                "content": agreements_html
            })
        
        # Add disagreements if they exist
        if hasattr(synthesis, 'disagreements') and synthesis.disagreements:
            disagreements_html = "<h3>Areas of Disagreement</h3>"
            for disagreement in synthesis.disagreements:
                disagreements_html += f"<div class='disagreement'>"
                disagreements_html += f"<h4>{disagreement['point']}</h4>"
                if 'source_views' in disagreement and disagreement['source_views']:
                    disagreements_html += "<ul>"
                    for source_id, view in disagreement['source_views'].items():
                        source = next((s for s in sources if str(sources.index(s) + 1) == str(source_id)), None)
                        source_ref = f"Source {source_id}"
                        if source:
                            source_ref = f"<a href='{source.get('url', '#')}' target='_blank'>{source.get('title', f'Source {source_id}')}</a>"
                        disagreements_html += f"<li><strong>{source_ref}:</strong> {view}</li>"
                    disagreements_html += "</ul>"
                disagreements_html += "</div>"
            sections.append({
                "title": "Areas of Disagreement",
                "content": disagreements_html
            })
        
        # Add knowledge gaps if they exist
        if hasattr(synthesis, 'knowledge_gaps') and synthesis.knowledge_gaps:
            gaps_html = "<h3>Knowledge Gaps</h3><ul class='gaps'>"
            for gap in synthesis.knowledge_gaps:
                gaps_html += f"<li>{gap}</li>"
            gaps_html += "</ul>"
            sections.append({
                "title": "Knowledge Gaps",
                "content": gaps_html
            })
        
        # Add sources
        if sources:
            sources_html = "<h3>References</h3><div class='sources'>"
            for i, source in enumerate(sources, 1):
                source_type = source.get('source_type', 'unknown').title()
                sources_html += f"""
                <div class='source'>
                    <span class='source-type'>{source_type}</span>
                    <strong>[{i}] {source.get('title', 'Untitled Source')}</strong><br>
                    {f"<em>URL:</em> <a href='{source['url']}' target='_blank'>{source['url']}</a><br>" if source.get('url') else ""}
                    {f"<div class='source-content'>{source.get('content', '')}</div>" if source.get('content') else ""}
                </div>
                """
            sources_html += "</div>"
            sections.append({
                "title": "References",
                "content": sources_html
            })
        
        return sections
    
    async def _generate_simple_html(self, report_path: str, topic: str, synthesis: Any, sources: List[Dict]) -> None:
        """Generate a simple HTML report without Jinja2."""
        # Prepare the findings HTML
        findings_html = ""
        for f in synthesis.key_findings:
            confidence_class = "high-confidence" if f['confidence'] > 0.7 else "medium-confidence" if f['confidence'] > 0.4 else "low-confidence"
            findings_html += f"<div class='finding'>{f['finding']} <span class='{confidence_class}''>(Confidence: {int(f['confidence']*100)}%)</span></div>"
        
        # Prepare additional sections
        sections_html = ""
        for section in self._prepare_sections(synthesis, sources):
            if section['title'] not in ['Executive Summary', 'Key Findings']:
                sections_html += f"<h2>{section['title']}</h2>{section['content']}"

        # Create the HTML content
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Research Report: {topic}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        .finding {{ margin-bottom: 10px; }}
        .source {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; }}
        .confidence {{ 
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .high-confidence {{ background-color: #d4edda; color: #155724; }}
        .medium-confidence {{ background-color: #fff3cd; color: #856404; }}
        .low-confidence {{ background-color: #f8d7da; color: #721c24; }}
        footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <h1>Research Report: {topic}</h1>
    <p><em>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
    
    <h2>Executive Summary</h2>
    <p>{synthesis.overall_summary}</p>
    
    <h2>Key Findings</h2>
    <div class='findings'>{findings_html}</div>
    
    {sections_html}
    
    <footer>
        <hr>
        <p>Generated by Autonomous Research Assistant</p>
    </footer>
</body>
</html>"""
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    async def _generate_markdown_report(self, report_path: str, topic: str, synthesis: Any, sources: List[Dict]) -> None:
        """Generate a markdown report."""
        # Prepare key findings
        key_findings = "\n".join([
            f"- {f['finding']} (Confidence: {int(f['confidence']*100)}%)" 
            for f in synthesis.key_findings
        ])
        
        # Prepare trends
        trends = "\n".join([f"- {trend}" for trend in synthesis.trends])
        
        # Prepare references
        references = []
        for i, source in enumerate(sources, 1):
            ref = f"{i}. **{source.get('title', 'Untitled Source')}**  \n"
            ref += f"   *Type*: {source.get('source_type', 'unknown').title()}  \n"
            if source.get('url'):
                ref += f"   *URL*: {source['url']}  \n"
            # Add content if available
            if source.get('content'):
                ref += f"   *Summary*: {source['content'][:200]}...  \n"
            references.append(ref)
        
        references_str = "\n".join(references)
        
        # Create the markdown content
        markdown = f"""# Research Report: {topic}

*Generated on: {date}*

## Executive Summary

{summary}

## Key Findings

{findings}

## Emerging Trends

{trends}

## Areas of Agreement

{agreements}

## Areas of Disagreement

{disagreements}

## Knowledge Gaps

{gaps}

## References

{references}

---

*Generated by Autonomous Research Assistant*
""".format(
            topic=topic,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            summary=synthesis.overall_summary,
            findings=key_findings,
            trends=trends,
            agreements="\n".join([f"- {a['point']}" for a in getattr(synthesis, 'agreements', [])]),
            disagreements="\n".join([f"- {d['point']}" for d in getattr(synthesis, 'disagreements', [])]),
            gaps="\n".join([f"- {gap}" for gap in getattr(synthesis, 'knowledge_gaps', [])]),
            references=references_str
        )
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown)

async def generate_sample_report():
    """Generate a sample research report."""
    # Create output directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Create a sample synthesis result
    synthesis = SynthesisResult(
        key_findings=[
            {
                "finding": "AI adoption in healthcare is growing rapidly",
                "confidence": 0.85,
                "supporting_sources": [0, 1, 2]
            },
            {
                "finding": "Ethical concerns remain a significant challenge",
                "confidence": 0.75,
                "supporting_sources": [1, 3]
            },
            {
                "finding": "AI can significantly reduce diagnostic errors",
                "confidence": 0.92,
                "supporting_sources": [0, 2]
            }
        ],
        trends=[
            "Increased use of AI for diagnostic purposes",
            "Rise of AI-powered telemedicine platforms",
            "Growing investment in healthcare AI startups",
            "Integration of AI with electronic health records (EHR) systems"
        ],
        agreements=[
            {
                "point": "AI improves diagnostic accuracy",
                "supporting_sources": [0, 1, 2, 3]
            },
            {
                "point": "AI can help reduce healthcare costs in the long run",
                "supporting_sources": [0, 2]
            }
        ],
        disagreements=[
            {
                "point": "Impact of AI on healthcare employment",
                "source_views": {
                    "1": "AI will create more jobs than it replaces by enabling new healthcare services",
                    "3": "Significant job displacement expected in administrative and diagnostic roles"
                }
            },
            {
                "point": "Regulation of AI in healthcare",
                "source_views": {
                    "2": "Strict regulation is needed to ensure patient safety and data privacy",
                    "4": "Over-regulation could stifle innovation in AI healthcare applications"
                }
            }
        ],
        knowledge_gaps=[
            "Long-term effects of AI diagnosis on patient outcomes",
            "Optimal human-AI collaboration models in clinical settings",
            "Impact of AI on healthcare provider-patient relationships"
        ],
        overall_summary="""The integration of AI in healthcare is transforming the industry, offering significant improvements in diagnostic accuracy, operational efficiency, and patient outcomes. However, this transformation is not without challenges, including ethical considerations, data privacy concerns, and workforce implications. This report provides a comprehensive analysis of the current state of AI in healthcare, highlighting key findings, emerging trends, areas of agreement and disagreement among experts, and important knowledge gaps that warrant further research."""
    )
    
    # Sample sources
    sources = [
        {
            "title": "AI in Healthcare: Current Applications and Future Outlook",
            "url": "https://example.com/ai-healthcare-report",
            "content": "This comprehensive report examines the current state of AI applications in healthcare, including diagnostic tools, treatment planning, and patient monitoring systems. It highlights the potential for AI to improve healthcare outcomes while addressing implementation challenges.",
            "source_type": "research report"
        },
        {
            "title": "The Impact of AI on Medical Diagnostics: A Systematic Review",
            "url": "https://example.com/ai-diagnostics-review",
            "content": "A systematic review of 127 studies on AI applications in medical diagnostics, analyzing accuracy rates, implementation challenges, and comparison with human experts across various medical specialties.",
            "source_type": "journal article"
        },
        {
            "title": "Ethical Considerations in AI Healthcare Applications",
            "url": "https://example.com/ai-ethics-healthcare",
            "content": "This paper explores the ethical implications of AI in healthcare, including issues of bias, transparency, accountability, and the need for robust regulatory frameworks to ensure patient safety and data privacy.",
            "source_type": "academic paper"
        },
        {
            "title": "AI and the Future of Healthcare Employment: Opportunities and Challenges",
            "url": "https://example.com/ai-healthcare-jobs",
            "content": "An analysis of how AI is reshaping healthcare employment, examining both job displacement concerns and the creation of new roles requiring human-AI collaboration skills.",
            "source_type": "industry report"
        },
        {
            "title": "Regulatory Approaches to AI in Healthcare: A Global Perspective",
            "url": "https://example.com/ai-healthcare-regulation",
            "content": "A comparative analysis of regulatory approaches to AI in healthcare across different countries, examining the balance between innovation and patient safety.",
            "source_type": "policy paper"
        }
    ]
    
    # Generate the report
    generator = OutputGenerator()
    report_path = await generator.generate_report(
        topic="The Impact of Artificial Intelligence on Healthcare",
        synthesis=synthesis,
        sources=sources,
        format="html"  # Change to "markdown" for markdown format
    )
    
    print(f"✅ Sample report generated at: {report_path}")
    print("Open this file in a web browser to view the report.")

if __name__ == "__main__":
    asyncio.run(generate_sample_report())
