import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import logging
from datetime import datetime
from collections import defaultdict, Counter
import re
from .base_agent import BaseAgent, AgentMessage

@dataclass
class KeyFinding:
    """Data class to store key findings from synthesis."""
    finding: str
    confidence: float
    sources: List[str]
    category: str
    importance: str  # "high", "medium", "low"

@dataclass
class Trend:
    """Data class to store identified trends."""
    trend: str
    direction: str  # "increasing", "decreasing", "stable"
    evidence: List[str]
    confidence: float
    timeframe: str

@dataclass
class Agreement:
    """Data class to store areas of agreement."""
    topic: str
    consensus_level: float  # 0.0 to 1.0
    supporting_sources: List[str]
    key_points: List[str]

@dataclass
class Disagreement:
    """Data class to store areas of disagreement."""
    topic: str
    conflicting_views: List[Dict[str, Any]]
    confidence: float
    explanation: str

@dataclass
class KnowledgeGap:
    """Data class to store identified knowledge gaps."""
    gap: str
    importance: str  # "high", "medium", "low"
    suggested_research: List[str]
    related_topics: List[str]

@dataclass
class SynthesisResult:
    """Data class to store complete synthesis results."""
    topic: str
    executive_summary: str
    key_findings: List[KeyFinding]
    trends: List[Trend]
    agreements: List[Agreement]
    disagreements: List[Disagreement]
    knowledge_gaps: List[KnowledgeGap]
    source_count: int
    synthesis_date: str

class SynthesizerAgent(BaseAgent):
    """
    Synthesizer Agent responsible for:
    - Combining information from multiple sources
    - Identifying key findings and trends
    - Detecting agreements and disagreements
    - Highlighting knowledge gaps
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the SynthesizerAgent with optional configuration."""
        super().__init__(
            name="SynthesizerAgent",
            description="Synthesizes information from multiple sources into coherent insights"
        )
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.min_sources_for_consensus = self.config.get("min_sources_for_consensus", 2)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.6)
        self.max_findings = self.config.get("max_findings", 10)
        self.max_trends = self.config.get("max_trends", 5)
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process synthesis request and return synthesized results.
        
        Args:
            message: AgentMessage containing sources to synthesize
            
        Returns:
            AgentMessage with synthesis results
        """
        try:
            content = message.content_dict
            
            # Extract topic and sources
            topic = content.get("topic", "")
            sources = content.get("sources", [])
            
            if not sources:
                raise ValueError("No sources provided for synthesis")
            
            self.logger.info(f"Processing synthesis for topic: {topic} with {len(sources)} sources")
            
            # 1. Extract and preprocess content
            processed_sources = await self.preprocess_sources(sources)
            
            # 2. Identify key findings
            key_findings = await self.extract_key_findings(processed_sources, topic)
            
            # 3. Identify trends
            trends = await self.identify_trends(processed_sources)
            
            # 4. Find areas of agreement
            agreements = await self.find_agreements(processed_sources)
            
            # 5. Find areas of disagreement
            disagreements = await self.find_disagreements(processed_sources)
            
            # 6. Identify knowledge gaps
            knowledge_gaps = await self.identify_knowledge_gaps(processed_sources, topic)
            
            # 7. Generate executive summary
            executive_summary = await self.generate_executive_summary(
                topic, key_findings, trends, agreements, disagreements
            )
            
            # 8. Create synthesis result
            synthesis_result = SynthesisResult(
                topic=topic,
                executive_summary=executive_summary,
                key_findings=key_findings,
                trends=trends,
                agreements=agreements,
                disagreements=disagreements,
                knowledge_gaps=knowledge_gaps,
                source_count=len(sources),
                synthesis_date=datetime.now().isoformat()
            )
            
            # Convert to dictionary for JSON serialization
            synthesis_dict = {
                "topic": synthesis_result.topic,
                "executive_summary": synthesis_result.executive_summary,
                "key_findings": [kf.__dict__ for kf in synthesis_result.key_findings],
                "trends": [t.__dict__ for t in synthesis_result.trends],
                "agreements": [a.__dict__ for a in synthesis_result.agreements],
                "disagreements": [d.__dict__ for d in synthesis_result.disagreements],
                "knowledge_gaps": [kg.__dict__ for kg in synthesis_result.knowledge_gaps],
                "source_count": synthesis_result.source_count,
                "synthesis_date": synthesis_result.synthesis_date
            }
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "synthesis": synthesis_dict
                },
                metadata={
                    "agent": self.name,
                    "sources_processed": len(sources),
                    "key_findings": len(key_findings),
                    "trends": len(trends)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in SynthesizerAgent: {str(e)}", exc_info=True)
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def preprocess_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess sources for synthesis.
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            List of preprocessed sources
        """
        processed = []
        
        for source in sources:
            # Extract relevant information
            processed_source = {
                "url": source.get("url", ""),
                "title": source.get("title", ""),
                "content": source.get("content", ""),
                "domain": self.extract_domain(source.get("url", "")),
                "sentences": self.split_into_sentences(source.get("content", "")),
                "key_phrases": self.extract_key_phrases(source.get("content", "")),
                "numbers": self.extract_numbers(source.get("content", "")),
                "dates": self.extract_dates(source.get("content", ""))
            }
            
            processed.append(processed_source)
        
        return processed
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be improved with NLP
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple key phrase extraction
        # Look for capitalized phrases and technical terms
        words = text.split()
        key_phrases = []
        
        # Extract multi-word phrases (2-3 words)
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 10 and any(c.isupper() for c in phrase):
                key_phrases.append(phrase)
        
        return list(set(key_phrases))
    
    def extract_numbers(self, text: str) -> List[str]:
        """Extract numbers and percentages from text."""
        # Find numbers, percentages, and quantities
        patterns = [
            r'\d+\.?\d*%',  # Percentages
            r'\$\d+\.?\d*',  # Money
            r'\d+\.?\d*\s*(?:million|billion|thousand)',  # Large numbers
            r'\d+\.?\d*'  # Regular numbers
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        
        return numbers
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Simple date extraction
        patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Full dates
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'  # MM/DD/YYYY
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates
    
    async def extract_key_findings(self, sources: List[Dict[str, Any]], topic: str) -> List[KeyFinding]:
        """
        Extract key findings from sources.
        
        Args:
            sources: Preprocessed sources
            topic: Research topic
            
        Returns:
            List of key findings
        """
        findings = []
        
        # Collect sentences with key indicators
        indicator_words = [
            "found that", "shows that", "indicates", "suggests", "concludes",
            "demonstrates", "reveals", "according to", "research shows"
        ]
        
        for source in sources:
            for sentence in source["sentences"]:
                # Check if sentence contains key indicators
                if any(indicator in sentence.lower() for indicator in indicator_words):
                    # Calculate confidence based on source authority
                    confidence = self.calculate_source_confidence(source)
                    
                    # Categorize the finding
                    category = self.categorize_finding(sentence, topic)
                    
                    # Determine importance
                    importance = self.determine_importance(sentence)
                    
                    finding = KeyFinding(
                        finding=sentence,
                        confidence=confidence,
                        sources=[source["url"]],
                        category=category,
                        importance=importance
                    )
                    
                    findings.append(finding)
        
        # Remove duplicates and limit results
        unique_findings = self.deduplicate_findings(findings)
        return unique_findings[:self.max_findings]
    
    def calculate_source_confidence(self, source: Dict[str, Any]) -> float:
        """Calculate confidence score for a source."""
        # Simple confidence calculation based on domain
        domain = source["domain"]
        
        # High confidence domains
        high_confidence = [
            "nature.com", "science.org", "sciencedirect.com", "pubmed.ncbi.nlm.nih.gov",
            "scholar.google.com", "arxiv.org", "reuters.com", "ap.org", "bbc.com"
        ]
        
        # Medium confidence domains
        medium_confidence = [
            "wikipedia.org", "forbes.com", "nytimes.com", "npr.org", "medium.com"
        ]
        
        if domain in high_confidence:
            return 0.9
        elif domain in medium_confidence:
            return 0.7
        elif domain.endswith(".edu") or domain.endswith(".gov"):
            return 0.85
        else:
            return 0.5
    
    def categorize_finding(self, sentence: str, topic: str) -> str:
        """Categorize a finding based on content."""
        sentence_lower = sentence.lower()
        
        # Simple categorization based on keywords
        if any(word in sentence_lower for word in ["increase", "rise", "grow", "growth"]):
            return "growth_trend"
        elif any(word in sentence_lower for word in ["decrease", "decline", "fall", "drop"]):
            return "decline_trend"
        elif any(word in sentence_lower for word in ["cost", "price", "expense", "budget"]):
            return "economic"
        elif any(word in sentence_lower for word in ["impact", "effect", "influence"]):
            return "impact"
        elif any(word in sentence_lower for word in ["research", "study", "analysis"]):
            return "research"
        else:
            return "general"
    
    def determine_importance(self, sentence: str) -> str:
        """Determine the importance level of a finding."""
        sentence_lower = sentence.lower()
        
        # High importance indicators
        if any(word in sentence_lower for word in ["significant", "major", "critical", "important"]):
            return "high"
        # Medium importance indicators
        elif any(word in sentence_lower for word in ["notable", "considerable", "substantial"]):
            return "medium"
        else:
            return "low"
    
    def deduplicate_findings(self, findings: List[KeyFinding]) -> List[KeyFinding]:
        """Remove duplicate findings."""
        unique = []
        seen = set()
        
        for finding in findings:
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', finding.finding.lower().strip())
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(finding)
        
        return unique
    
    async def identify_trends(self, sources: List[Dict[str, Any]]) -> List[Trend]:
        """
        Identify trends from sources.
        
        Args:
            sources: Preprocessed sources
            
        Returns:
            List of identified trends
        """
        trends = []
        
        # Look for trend indicators
        trend_indicators = {
            "increasing": ["increase", "rise", "grow", "growth", "upward", "surge"],
            "decreasing": ["decrease", "decline", "fall", "drop", "downward", "reduce"],
            "stable": ["stable", "steady", "consistent", "unchanged", "constant"]
        }
        
        for direction, indicators in trend_indicators.items():
            for source in sources:
                for sentence in source["sentences"]:
                    if any(indicator in sentence.lower() for indicator in indicators):
                        # Extract the trend description
                        trend_desc = self.extract_trend_description(sentence, direction)
                        
                        if trend_desc:
                            trend = Trend(
                                trend=trend_desc,
                                direction=direction,
                                evidence=[sentence],
                                confidence=self.calculate_source_confidence(source),
                                timeframe=self.extract_timeframe(sentence)
                            )
                            trends.append(trend)
        
        # Remove duplicates and limit results
        unique_trends = self.deduplicate_trends(trends)
        return unique_trends[:self.max_trends]
    
    def extract_trend_description(self, sentence: str, direction: str) -> Optional[str]:
        """Extract trend description from sentence."""
        # Simple extraction - can be improved with NLP
        words = sentence.split()
        
        for i, word in enumerate(words):
            if word.lower() in ["increase", "rise", "grow", "growth", "decrease", "decline", "fall", "drop"]:
                # Extract surrounding context
                start = max(0, i - 3)
                end = min(len(words), i + 4)
                return " ".join(words[start:end])
        
        return None
    
    def extract_timeframe(self, sentence: str) -> str:
        """Extract timeframe from sentence."""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ["2023", "2024", "2025"]):
            return "recent"
        elif any(word in sentence_lower for word in ["2020", "2021", "2022"]):
            return "2020-2022"
        elif any(word in sentence_lower for word in ["last year", "past year"]):
            return "last_year"
        else:
            return "unknown"
    
    def deduplicate_trends(self, trends: List[Trend]) -> List[Trend]:
        """Remove duplicate trends."""
        unique = []
        seen = set()
        
        for trend in trends:
            normalized = re.sub(r'\s+', ' ', trend.trend.lower().strip())
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(trend)
        
        return unique
    
    async def find_agreements(self, sources: List[Dict[str, Any]]) -> List[Agreement]:
        """
        Find areas of agreement between sources.
        
        Args:
            sources: Preprocessed sources
            
        Returns:
            List of agreements
        """
        agreements = []
        
        # Group sources by key phrases
        phrase_groups = defaultdict(list)
        
        for source in sources:
            for phrase in source["key_phrases"]:
                phrase_groups[phrase].append(source)
        
        # Find phrases mentioned by multiple sources
        for phrase, sources_mentioning in phrase_groups.items():
            if len(sources_mentioning) >= self.min_sources_for_consensus:
                # Calculate consensus level
                consensus_level = min(len(sources_mentioning) / len(sources), 1.0)
                
                # Extract key points about this phrase
                key_points = self.extract_key_points_for_phrase(sources_mentioning, phrase)
                
                agreement = Agreement(
                    topic=phrase,
                    consensus_level=consensus_level,
                    supporting_sources=[s["url"] for s in sources_mentioning],
                    key_points=key_points
                )
                
                agreements.append(agreement)
        
        # Sort by consensus level
        agreements.sort(key=lambda x: x.consensus_level, reverse=True)
        
        return agreements[:5]  # Limit to top 5 agreements
    
    def extract_key_points_for_phrase(self, sources: List[Dict[str, Any]], phrase: str) -> List[str]:
        """Extract key points about a specific phrase from sources."""
        key_points = []
        
        for source in sources:
            for sentence in source["sentences"]:
                if phrase.lower() in sentence.lower():
                    # Extract a concise version of the sentence
                    if len(sentence) < 200:
                        key_points.append(sentence)
                    else:
                        # Truncate long sentences
                        key_points.append(sentence[:197] + "...")
        
        # Remove duplicates
        return list(set(key_points))[:3]  # Limit to 3 key points
    
    async def find_disagreements(self, sources: List[Dict[str, Any]]) -> List[Disagreement]:
        """
        Find areas of disagreement between sources.
        
        Args:
            sources: Preprocessed sources
            
        Returns:
            List of disagreements
        """
        disagreements = []
        
        # Look for contradictory statements
        contradiction_pairs = [
            (["increase", "rise", "grow"], ["decrease", "decline", "fall"]),
            (["effective", "successful"], ["ineffective", "unsuccessful"]),
            (["beneficial", "positive"], ["harmful", "negative"]),
            (["support", "agree"], ["oppose", "disagree"])
        ]
        
        for positive_words, negative_words in contradiction_pairs:
            positive_sentences = []
            negative_sentences = []
            
            for source in sources:
                for sentence in source["sentences"]:
                    if any(word in sentence.lower() for word in positive_words):
                        positive_sentences.append((sentence, source["url"]))
                    elif any(word in sentence.lower() for word in negative_words):
                        negative_sentences.append((sentence, source["url"]))
            
            # If we have both positive and negative statements about similar topics
            if positive_sentences and negative_sentences:
                disagreement = Disagreement(
                    topic=f"Conflicting views on effectiveness/impact",
                    conflicting_views=[
                        {"view": "positive", "sentences": positive_sentences[:3]},
                        {"view": "negative", "sentences": negative_sentences[:3]}
                    ],
                    confidence=0.7,
                    explanation="Sources present contradictory information on this topic"
                )
                
                disagreements.append(disagreement)
        
        return disagreements[:3]  # Limit to top 3 disagreements
    
    async def identify_knowledge_gaps(self, sources: List[Dict[str, Any]], topic: str) -> List[KnowledgeGap]:
        """
        Identify knowledge gaps in the research.
        
        Args:
            sources: Preprocessed sources
            topic: Research topic
            
        Returns:
            List of knowledge gaps
        """
        gaps = []
        
        # Common knowledge gap indicators
        gap_indicators = [
            "further research needed", "more studies required", "unknown",
            "unclear", "not well understood", "limited data", "insufficient evidence"
        ]
        
        for source in sources:
            for sentence in source["sentences"]:
                if any(indicator in sentence.lower() for indicator in gap_indicators):
                    # Extract the gap description
                    gap_desc = self.extract_gap_description(sentence)
                    
                    if gap_desc:
                        gap = KnowledgeGap(
                            gap=gap_desc,
                            importance=self.determine_gap_importance(sentence),
                            suggested_research=self.suggest_research_for_gap(gap_desc),
                            related_topics=self.find_related_topics(sentence, topic)
                        )
                        
                        gaps.append(gap)
        
        # Remove duplicates
        unique_gaps = self.deduplicate_gaps(gaps)
        
        return unique_gaps[:5]  # Limit to top 5 gaps
    
    def extract_gap_description(self, sentence: str) -> Optional[str]:
        """Extract knowledge gap description from sentence."""
        # Simple extraction - can be improved
        if any(indicator in sentence.lower() for indicator in ["further research", "more studies"]):
            return sentence
        elif "unknown" in sentence.lower() or "unclear" in sentence.lower():
            return sentence
        return None
    
    def determine_gap_importance(self, sentence: str) -> str:
        """Determine the importance of a knowledge gap."""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ["critical", "essential", "important"]):
            return "high"
        elif any(word in sentence_lower for word in ["useful", "helpful", "valuable"]):
            return "medium"
        else:
            return "low"
    
    def suggest_research_for_gap(self, gap_desc: str) -> List[str]:
        """Suggest research directions for a knowledge gap."""
        suggestions = []
        
        if "cost" in gap_desc.lower():
            suggestions.append("Conduct cost-benefit analysis")
        if "impact" in gap_desc.lower():
            suggestions.append("Perform longitudinal impact studies")
        if "effectiveness" in gap_desc.lower():
            suggestions.append("Run controlled experiments")
        if "long-term" in gap_desc.lower():
            suggestions.append("Initiate long-term observational studies")
        
        if not suggestions:
            suggestions.append("Conduct comprehensive research on this topic")
        
        return suggestions
    
    def find_related_topics(self, sentence: str, main_topic: str) -> List[str]:
        """Find topics related to the knowledge gap."""
        # Simple related topic extraction
        words = sentence.split()
        related = []
        
        for word in words:
            if len(word) > 5 and word.lower() != main_topic.lower():
                related.append(word)
        
        return related[:3]  # Limit to 3 related topics
    
    def deduplicate_gaps(self, gaps: List[KnowledgeGap]) -> List[KnowledgeGap]:
        """Remove duplicate knowledge gaps."""
        unique = []
        seen = set()
        
        for gap in gaps:
            normalized = re.sub(r'\s+', ' ', gap.gap.lower().strip())
            
            if normalized not in seen:
                seen.add(normalized)
                unique.append(gap)
        
        return unique
    
    async def generate_executive_summary(self, topic: str, key_findings: List[KeyFinding], 
                                       trends: List[Trend], agreements: List[Agreement],
                                       disagreements: List[Disagreement]) -> str:
        """
        Generate an executive summary of the synthesis.
        
        Args:
            topic: Research topic
            key_findings: List of key findings
            trends: List of trends
            agreements: List of agreements
            disagreements: List of disagreements
            
        Returns:
            Executive summary string
        """
        summary_parts = []
        
        # Introduction
        summary_parts.append(f"This synthesis analyzes {topic} based on multiple sources.")
        
        # Key findings summary
        if key_findings:
            high_importance = [kf for kf in key_findings if kf.importance == "high"]
            if high_importance:
                summary_parts.append(f"Key findings include {len(high_importance)} high-importance discoveries.")
        
        # Trends summary
        if trends:
            increasing_trends = [t for t in trends if t.direction == "increasing"]
            decreasing_trends = [t for t in trends if t.direction == "decreasing"]
            
            if increasing_trends:
                summary_parts.append(f"{len(increasing_trends)} increasing trends were identified.")
            if decreasing_trends:
                summary_parts.append(f"{len(decreasing_trends)} decreasing trends were identified.")
        
        # Agreement summary
        if agreements:
            strong_agreements = [a for a in agreements if a.consensus_level > 0.7]
            if strong_agreements:
                summary_parts.append(f"There is strong consensus on {len(strong_agreements)} key topics.")
        
        # Disagreement summary
        if disagreements:
            summary_parts.append(f"{len(disagreements)} areas of disagreement were identified, requiring further investigation.")
        
        # Conclusion
        summary_parts.append("Overall, the analysis provides a comprehensive overview of the current state of knowledge on this topic.")
        
        return " ".join(summary_parts)

# Example usage
async def test_synthesizer_agent():
    """Test function for the SynthesizerAgent."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    synthesizer = SynthesizerAgent()
    
    try:
        # Create test message with sources
        message = AgentMessage.create(
            role="user",
            content={
                "topic": "renewable energy adoption",
                "sources": [
                    {
                        "url": "https://nature.com/articles/renewable-2023",
                        "title": "Renewable Energy Trends 2023",
                        "content": "Research shows that renewable energy adoption has increased significantly in 2023. Solar power costs have decreased by 89% since 2010. Wind energy now provides 10% of global electricity. Studies indicate that further research is needed on storage solutions."
                    },
                    {
                        "url": "https://sciencedirect.com/science/article/wind-energy",
                        "title": "Wind Energy Global Impact",
                        "content": "Wind energy capacity has grown substantially over the past decade. The cost of wind power has decreased by 70% since 2010. However, the impact on wildlife remains unclear. More studies are required to understand long-term ecological effects."
                    },
                    {
                        "url": "https://example.com/blog/energy-stats",
                        "title": "Energy Statistics Blog",
                        "content": "Recent data indicates that renewable energy sources now account for 30% of global electricity generation. Solar panel efficiency has improved by 25% in the last five years. The effectiveness of battery storage systems has increased dramatically."
                    }
                ]
            }
        )
        
        result = await synthesizer.process(message)
        
        # Get content as dictionary
        result_content = result.content_dict
        
        print("\nSynthesis Results:")
        print("-" * 50)
        
        if result_content.get("status") == "success":
            synthesis = result_content.get("synthesis", {})
            
            print(f"\nTopic: {synthesis.get('topic', '')}")
            print(f"Sources Analyzed: {synthesis.get('source_count', 0)}")
            
            print(f"\nExecutive Summary:")
            print(f"  {synthesis.get('executive_summary', '')}")
            
            print(f"\nKey Findings ({len(synthesis.get('key_findings', []))}):")
            for i, kf in enumerate(synthesis.get('key_findings', [])[:3], 1):
                print(f"\n  Finding {i}:")
                print(f"    {kf.get('finding', '')[:100]}...")
                print(f"    Confidence: {kf.get('confidence', 0):.2f}")
                print(f"    Importance: {kf.get('importance', '')}")
            
            print(f"\nTrends ({len(synthesis.get('trends', []))}):")
            for i, trend in enumerate(synthesis.get('trends', []), 1):
                print(f"\n  Trend {i}:")
                print(f"    {trend.get('trend', '')}")
                print(f"    Direction: {trend.get('direction', '')}")
                print(f"    Confidence: {trend.get('confidence', 0):.2f}")
            
            print(f"\nAgreements ({len(synthesis.get('agreements', []))}):")
            for i, agreement in enumerate(synthesis.get('agreements', []), 1):
                print(f"\n  Agreement {i}:")
                print(f"    Topic: {agreement.get('topic', '')}")
                print(f"    Consensus: {agreement.get('consensus_level', 0):.2f}")
            
            print(f"\nDisagreements ({len(synthesis.get('disagreements', []))}):")
            for i, disagreement in enumerate(synthesis.get('disagreements', []), 1):
                print(f"\n  Disagreement {i}:")
                print(f"    Topic: {disagreement.get('topic', '')}")
            
            print(f"\nKnowledge Gaps ({len(synthesis.get('knowledge_gaps', []))}):")
            for i, gap in enumerate(synthesis.get('knowledge_gaps', []), 1):
                print(f"\n  Gap {i}:")
                print(f"    {gap.get('gap', '')}")
                print(f"    Importance: {gap.get('importance', '')}")
        else:
            print(f"Error: {result_content.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_synthesizer_agent())
