import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import logging
from urllib.parse import urlparse
import tldextract
from datetime import datetime
from .base_agent import BaseAgent, AgentMessage

@dataclass
class SourceCredibility:
    """Data class to store source credibility information."""
    domain: str
    credibility_score: float  # 0.0 to 1.0
    authority_level: str  # "high", "medium", "low"
    bias_rating: str  # "left", "center", "right", "neutral"
    fact_check_rating: str  # "verified", "mixed", "unverified"
    last_updated: Optional[str] = None

@dataclass
class FactCheck:
    """Data class to store fact check results."""
    claim: str
    sources: List[str]
    verification_status: str  # "verified", "disputed", "unverified"
    confidence: float
    explanation: str
    conflicting_sources: List[str] = None

@dataclass
class VerificationResult:
    """Data class to store verification results."""
    original_content: str
    credibility_score: float
    fact_checks: List[FactCheck]
    source_analysis: Dict[str, Any]
    recommendations: List[str]
    warnings: List[str]

class VerificationAgent(BaseAgent):
    """
    Verification Agent responsible for:
    - Cross-referencing information across sources
    - Assessing source credibility
    - Fact-checking claims
    - Identifying potential biases
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the VerificationAgent with optional configuration."""
        super().__init__(
            name="VerificationAgent",
            description="Validates information and assesses source credibility"
        )
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Credibility thresholds
        self.high_credibility_threshold = self.config.get("high_credibility_threshold", 0.8)
        self.medium_credibility_threshold = self.config.get("medium_credibility_threshold", 0.5)
        
        # Known credible domains (can be expanded)
        self.credible_domains = {
            "nature.com": {"authority": "high", "bias": "neutral"},
            "science.org": {"authority": "high", "bias": "neutral"},
            "sciencedirect.com": {"authority": "high", "bias": "neutral"},
            "pubmed.ncbi.nlm.nih.gov": {"authority": "high", "bias": "neutral"},
            "scholar.google.com": {"authority": "high", "bias": "neutral"},
            "arxiv.org": {"authority": "high", "bias": "neutral"},
            "reuters.com": {"authority": "high", "bias": "center"},
            "ap.org": {"authority": "high", "bias": "center"},
            "bbc.com": {"authority": "high", "bias": "center"},
            "npr.org": {"authority": "high", "bias": "center"},
            "wikipedia.org": {"authority": "medium", "bias": "neutral"},
            "medium.com": {"authority": "medium", "bias": "mixed"},
            "forbes.com": {"authority": "medium", "bias": "center-right"},
            "nytimes.com": {"authority": "medium", "bias": "center-left"},
        }
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process verification request and return verification results.
        
        Args:
            message: AgentMessage containing content to verify
            
        Returns:
            AgentMessage with verification results
        """
        try:
            content = message.content_dict
            
            # Extract content and sources
            content_to_verify = content.get("content", "")
            sources = content.get("sources", [])
            
            if not content_to_verify:
                raise ValueError("No content provided for verification")
            
            self.logger.info(f"Processing verification request for {len(sources)} sources")
            
            # 1. Analyze source credibility
            source_analysis = await self.analyze_sources(sources)
            
            # 2. Perform fact-checking
            fact_checks = await self.fact_check_content(content_to_verify, sources)
            
            # 3. Calculate overall credibility score
            credibility_score = self.calculate_credibility_score(source_analysis, fact_checks)
            
            # 4. Generate recommendations and warnings
            recommendations, warnings = self.generate_recommendations(
                credibility_score, source_analysis, fact_checks
            )
            
            # 5. Create verification result
            verification_result = VerificationResult(
                original_content=content_to_verify,
                credibility_score=credibility_score,
                fact_checks=fact_checks,
                source_analysis=source_analysis,
                recommendations=recommendations,
                warnings=warnings
            )
            
            # Convert dataclasses to dictionaries for JSON serialization
            verification_dict = {
                "original_content": verification_result.original_content,
                "credibility_score": verification_result.credibility_score,
                "fact_checks": [fc.__dict__ for fc in verification_result.fact_checks],
                "source_analysis": verification_result.source_analysis,
                "recommendations": verification_result.recommendations,
                "warnings": verification_result.warnings
            }
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "verification": verification_dict
                },
                metadata={
                    "agent": self.name,
                    "sources_analyzed": len(sources),
                    "credibility_score": credibility_score
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in VerificationAgent: {str(e)}", exc_info=True)
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def analyze_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the credibility of provided sources.
        
        Args:
            sources: List of source dictionaries with url, title, etc.
            
        Returns:
            Dictionary with source credibility analysis
        """
        source_analysis = {
            "total_sources": len(sources),
            "high_credibility": 0,
            "medium_credibility": 0,
            "low_credibility": 0,
            "domains": {},
            "overall_score": 0.0
        }
        
        if not sources:
            return source_analysis
        
        total_score = 0
        
        for source in sources:
            url = source.get("url", "")
            domain = self.extract_domain(url)
            
            # Get credibility information
            credibility = self.assess_domain_credibility(domain)
            
            source_analysis["domains"][domain] = {
                "credibility_score": credibility.credibility_score,
                "authority_level": credibility.authority_level,
                "bias_rating": credibility.bias_rating,
                "fact_check_rating": credibility.fact_check_rating
            }
            
            # Count by credibility level
            if credibility.credibility_score >= self.high_credibility_threshold:
                source_analysis["high_credibility"] += 1
            elif credibility.credibility_score >= self.medium_credibility_threshold:
                source_analysis["medium_credibility"] += 1
            else:
                source_analysis["low_credibility"] += 1
            
            total_score += credibility.credibility_score
        
        # Calculate overall score
        source_analysis["overall_score"] = total_score / len(sources) if sources else 0
        
        return source_analysis
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            if not url:
                return "unknown"
            
            # Parse URL and extract domain
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
            
            return domain
        except Exception:
            return "unknown"
    
    def assess_domain_credibility(self, domain: str) -> SourceCredibility:
        """
        Assess the credibility of a domain.
        
        Args:
            domain: Domain name to assess
            
        Returns:
            SourceCredibility object with assessment results
        """
        # Check if domain is in known credible domains
        if domain in self.credible_domains:
            domain_info = self.credible_domains[domain]
            return SourceCredibility(
                domain=domain,
                credibility_score=0.9 if domain_info["authority"] == "high" else 0.6,
                authority_level=domain_info["authority"],
                bias_rating=domain_info["bias"],
                fact_check_rating="verified",
                last_updated=datetime.now().isoformat()
            )
        
        # Assess based on domain characteristics
        credibility_score = 0.5  # Default medium score
        
        # Educational and government domains get higher scores
        if domain.endswith(".edu") or domain.endswith(".gov"):
            credibility_score = 0.85
        elif domain.endswith(".org"):
            credibility_score = 0.7
        elif domain.endswith(".com"):
            credibility_score = 0.6
        
        # Check for common indicators of credibility
        if "wiki" in domain:
            credibility_score = min(credibility_score + 0.1, 1.0)
        elif "blog" in domain or "forum" in domain:
            credibility_score = max(credibility_score - 0.2, 0.0)
        
        return SourceCredibility(
            domain=domain,
            credibility_score=credibility_score,
            authority_level=(
                "high" if credibility_score >= 0.8 else
                "medium" if credibility_score >= 0.5 else "low"
            ),
            bias_rating="neutral",
            fact_check_rating="unverified",
            last_updated=datetime.now().isoformat()
        )
    
    async def fact_check_content(self, content: str, sources: List[Dict[str, Any]]) -> List[FactCheck]:
        """
        Perform fact-checking on the content against sources.
        
        Args:
            content: Content to fact-check
            sources: List of sources to verify against
            
        Returns:
            List of FactCheck objects
        """
        fact_checks = []
        
        # Extract key claims from content (simplified)
        claims = self.extract_claims(content)
        
        for claim in claims:
            # Check if claim is supported by sources
            verification_status, confidence, explanation = self.verify_claim(claim, sources)
            
            fact_check = FactCheck(
                claim=claim,
                sources=[s.get("url", "") for s in sources],
                verification_status=verification_status,
                confidence=confidence,
                explanation=explanation
            )
            
            fact_checks.append(fact_check)
        
        return fact_checks
    
    def extract_claims(self, content: str) -> List[str]:
        """
        Extract key claims from content.
        This is a simplified implementation - in practice, you might use NLP techniques.
        """
        # Split content into sentences and filter for potential claims
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        
        # Simple heuristic: sentences with numbers, percentages, or definitive statements
        claims = []
        for sentence in sentences:
            # Look for indicators of factual claims
            if any(indicator in sentence.lower() for indicator in [
                "according to", "research shows", "study found", "data indicates",
                "percent", "%", "increase", "decrease", "million", "billion"
            ]):
                claims.append(sentence)
        
        # Limit to top claims to avoid processing too many
        return claims[:5]
    
    def verify_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Tuple[str, float, str]:
        """
        Verify a claim against the provided sources.
        
        Args:
            claim: Claim to verify
            sources: Sources to verify against
            
        Returns:
            Tuple of (verification_status, confidence, explanation)
        """
        # This is a simplified implementation
        # In practice, you would use more sophisticated text matching
        
        supporting_sources = 0
        total_sources = len(sources)
        
        for source in sources:
            source_content = source.get("content", "").lower()
            claim_lower = claim.lower()
            
            # Simple keyword matching (can be improved)
            words_in_claim = set(claim_lower.split())
            words_in_source = set(source_content.split())
            
            # Calculate overlap
            overlap = len(words_in_claim.intersection(words_in_source))
            
            # If significant overlap, consider it supporting
            if overlap >= len(words_in_claim) * 0.3:
                supporting_sources += 1
        
        # Determine verification status
        if supporting_sources == 0:
            return "unverified", 0.2, "No supporting evidence found in sources"
        elif supporting_sources >= total_sources * 0.7:
            return "verified", 0.8, f"Supported by {supporting_sources} out of {total_sources} sources"
        else:
            return "disputed", 0.5, f"Partially supported by {supporting_sources} out of {total_sources} sources"
    
    def calculate_credibility_score(self, source_analysis: Dict[str, Any], fact_checks: List[FactCheck]) -> float:
        """
        Calculate overall credibility score based on source analysis and fact checks.
        
        Args:
            source_analysis: Results from source analysis
            fact_checks: Results from fact checking
            
        Returns:
            Overall credibility score (0.0 to 1.0)
        """
        # Weight source credibility at 60% and fact checks at 40%
        source_weight = 0.6
        fact_check_weight = 0.4
        
        # Source credibility score
        source_score = source_analysis.get("overall_score", 0.0)
        
        # Fact check score
        if not fact_checks:
            fact_check_score = 0.5  # Default medium if no fact checks
        else:
            verified_count = sum(1 for fc in fact_checks if fc.verification_status == "verified")
            fact_check_score = verified_count / len(fact_checks)
        
        # Calculate weighted average
        overall_score = (source_score * source_weight) + (fact_check_score * fact_check_weight)
        
        return round(overall_score, 2)
    
    def generate_recommendations(self, credibility_score: float, source_analysis: Dict[str, Any], fact_checks: List[FactCheck]) -> Tuple[List[str], List[str]]:
        """
        Generate recommendations and warnings based on verification results.
        
        Args:
            credibility_score: Overall credibility score
            source_analysis: Source analysis results
            fact_checks: Fact check results
            
        Returns:
            Tuple of (recommendations, warnings)
        """
        recommendations = []
        warnings = []
        
        # Recommendations based on credibility score
        if credibility_score >= 0.8:
            recommendations.append("Information appears highly credible and well-sourced")
        elif credibility_score >= 0.6:
            recommendations.append("Information is moderately credible but verify with additional sources")
        else:
            recommendations.append("Information has low credibility - seek more reliable sources")
        
        # Source-based recommendations
        if source_analysis.get("low_credibility", 0) > source_analysis.get("high_credibility", 0):
            recommendations.append("Consider finding more authoritative sources")
            warnings.append("Majority of sources have low credibility ratings")
        
        # Fact check-based recommendations
        disputed_claims = [fc for fc in fact_checks if fc.verification_status == "disputed"]
        if disputed_claims:
            warnings.append(f"{len(disputed_claims)} claims have conflicting evidence")
            recommendations.append("Review disputed claims carefully")
        
        # Domain-specific recommendations
        domains = source_analysis.get("domains", {})
        for domain, info in domains.items():
            if info.get("bias_rating") != "neutral":
                recommendations.append(f"Be aware of potential bias in {domain} ({info.get('bias_rating')})")
        
        return recommendations, warnings

# Example usage
async def test_verification_agent():
    """Test function for the VerificationAgent."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    verifier = VerificationAgent()
    
    try:
        # Create test message with content and sources
        message = AgentMessage.create(
            role="user",
            content={
                "content": "According to recent studies, renewable energy adoption has increased by 45% in 2023. Research shows that solar power costs have decreased by 89% since 2010. Data indicates that wind energy now powers 10% of global electricity.",
                "sources": [
                    {
                        "url": "https://nature.com/articles/renewable-energy-2023",
                        "title": "Renewable Energy Trends 2023",
                        "content": "Recent studies show renewable energy adoption increased significantly in 2023."
                    },
                    {
                        "url": "https://example.com/blog/energy-stats",
                        "title": "Energy Statistics Blog",
                        "content": "Solar power costs have decreased dramatically since 2010."
                    },
                    {
                        "url": "https://sciencedirect.com/science/article/wind-energy",
                        "title": "Wind Energy Global Impact",
                        "content": "Wind energy now provides approximately 10% of global electricity."
                    }
                ]
            }
        )
        
        result = await verifier.process(message)
        
        # Get content as dictionary
        result_content = result.content_dict
        
        print("\nVerification Results:")
        print("-" * 50)
        
        if result_content.get("status") == "success":
            verification = result_content.get("verification", {})
            
            print(f"\nOverall Credibility Score: {verification.get('credibility_score', 0):.2f}")
            
            print("\nSource Analysis:")
            source_analysis = verification.get("source_analysis", {})
            print(f"  Total Sources: {source_analysis.get('total_sources', 0)}")
            print(f"  High Credibility: {source_analysis.get('high_credibility', 0)}")
            print(f"  Medium Credibility: {source_analysis.get('medium_credibility', 0)}")
            print(f"  Low Credibility: {source_analysis.get('low_credibility', 0)}")
            
            print("\nFact Checks:")
            fact_checks = verification.get("fact_checks", [])
            for i, fc in enumerate(fact_checks, 1):
                print(f"\n  Claim {i}: {fc.get('claim', '')[:100]}...")
                print(f"  Status: {fc.get('verification_status', 'unknown')}")
                print(f"  Confidence: {fc.get('confidence', 0):.2f}")
                print(f"  Explanation: {fc.get('explanation', '')}")
            
            print("\nRecommendations:")
            for rec in verification.get("recommendations", []):
                print(f"  ✓ {rec}")
            
            print("\nWarnings:")
            for warn in verification.get("warnings", []):
                print(f"  ⚠ {warn}")
        else:
            print(f"Error: {result_content.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_verification_agent())
