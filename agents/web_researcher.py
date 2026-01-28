import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging
from urllib.parse import urlparse
from trafilatura import extract
import tldextract
from .base_agent import BaseAgent, AgentMessage

@dataclass
class WebSearchResult:
    """Data class to store web search results."""
    title: str
    url: str
    snippet: str
    domain: str
    content: Optional[str] = None
    confidence: float = 0.0
    last_updated: Optional[str] = None

class WebResearcher(BaseAgent):
    """
    Web Research Agent responsible for:
    - Conducting web searches
    - Extracting and processing web content
    - Filtering and validating sources
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the WebResearcher with optional configuration."""
        super().__init__(
            name="WebResearcher",
            description="Conducts web searches and extracts relevant content"
        )
        self.config = config or {}
        self.session = None
        self.search_provider = self.config.get("search_provider", "mock")  # 'mock', 'serpapi', 'google'
        self.max_results = self.config.get("max_results", 5)
        self.min_content_length = self.config.get("min_content_length", 500)
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize the HTTP session."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process a research request and return search results.
        
        Args:
            message: AgentMessage containing the research query and parameters
            
        Returns:
            AgentMessage with search results or error information
        """
        try:
            await self.initialize()
            
            # Get content as dictionary
            content = message.content_dict
            
            # Extract parameters
            query = content.get("query")
            max_results = content.get("max_results", self.max_results)
            preferred_domains = content.get("domains", [])
            
            if not query:
                raise ValueError("No query provided for web research")
            
            self.logger.info(f"Processing web research query: {query}")
            
            # 1. Perform web search
            search_results = await self.web_search(query, max_results)
            
            # 2. Extract and process content
            enriched_results = await self.process_search_results(search_results, preferred_domains)
            
            # 3. Filter and rank results
            filtered_results = self.filter_results(enriched_results)
            
            return AgentMessage(
                role="assistant",
                content={
                    "status": "success",
                    "query": query,
                    "results": [r.__dict__ for r in filtered_results]
                },
                metadata={
                    "agent": self.name,
                    "result_count": len(filtered_results)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in WebResearcher: {str(e)}", exc_info=True)
            return AgentMessage(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e),
                    "query": message.content.get("query", ""),
                    "results": []
                },
                metadata={"agent": self.name}
            )
    
    async def web_search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """
        Perform a web search using the configured search provider.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of WebSearchResult objects
        """
        if self.search_provider == "mock":
            return self._mock_web_search(query, max_results)
        elif self.search_provider == "serpapi":
            return await self._serpapi_search(query, max_results)
        else:
            self.logger.warning(f"Unsupported search provider: {self.search_provider}. Using mock results.")
            return self._mock_web_search(query, max_results)
    
    def _mock_web_search(self, query: str, max_results: int) -> List[WebSearchResult]:
        """Generate mock search results for testing."""
        self.logger.warning("Using mock search results - implement actual search API")
        return [
            WebSearchResult(
                title=f"{query.capitalize()} - Result {i+1}",
                url=f"https://example.com/{query.replace(' ', '-')}-{i+1}",
                snippet=f"This is a sample result for query: {query}. "
                       f"Result {i+1} contains relevant information about {query}.",
                domain=f"example{i+1}.com",
                confidence=0.9 - (i * 0.1),  # Decreasing confidence for demo
                last_updated="2025-01-01"
            ) for i in range(max_results)
        ]
    
    async def _serpapi_search(self, query: str, max_results: int) -> List[WebSearchResult]:
        """Perform search using SerpAPI."""
        # Implementation for SerpAPI will go here
        self.logger.warning("SerpAPI integration not implemented. Using mock results.")
        return self._mock_web_search(query, max_results)
    
    async def process_search_results(self, results: List[WebSearchResult], 
                                  preferred_domains: List[str] = None) -> List[WebSearchResult]:
        """
        Process search results by fetching and extracting content.
        
        Args:
            results: List of search results to process
            preferred_domains: Optional list of preferred domains to prioritize
            
        Returns:
            List of processed WebSearchResult objects with extracted content
        """
        if not results:
            return []
            
        processed = []
        tasks = []
        
        # Create tasks for concurrent processing
        for result in results:
            # Skip if domain is not in preferred domains (if specified)
            if preferred_domains and result.domain.lower() not in [d.lower() for d in preferred_domains]:
                self.logger.debug(f"Skipping non-preferred domain: {result.domain}")
                continue
                
            tasks.append(self._process_single_result(result))
        
        # Run tasks concurrently
        processed = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any exceptions and None results
        return [r for r in processed if isinstance(r, WebSearchResult) and r.content]
    
    async def _process_single_result(self, result: WebSearchResult) -> Optional[WebSearchResult]:
        """Process a single search result."""
        try:
            # Fetch and extract content
            content = await self.extract_web_content(result.url)
            if content and len(content) >= self.min_content_length:
                result.content = content
                return result
            return None
        except Exception as e:
            self.logger.warning(f"Error processing {result.url}: {str(e)}")
            return None
    
    async def extract_web_content(self, url: str) -> Optional[str]:
        """
        Extract main content from a web page.
        
        Args:
            url: URL of the web page to extract content from
            
        Returns:
            Extracted content as string, or None if extraction fails
        """
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
                
                # Check content type to ensure it's HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.warning(f"Skipping non-HTML content at {url}")
                    return None
                
                html = await response.text()
                
                # Use trafilatura to extract main content
                content = extract(
                    html,
                    include_links=False,
                    include_tables=False,
                    include_images=False,
                    include_formatting=False
                )
                
                if not content or len(content.strip()) < self.min_content_length:
                    self.logger.debug(f"Insufficient content extracted from {url}")
                    return None
                    
                return content.strip()
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout while fetching {url}")
            return None
        except Exception as e:
            self.logger.warning(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def filter_results(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """
        Filter and rank search results.
        
        Args:
            results: List of WebSearchResult objects to filter
            
        Returns:
            Filtered and ranked list of WebSearchResult objects
        """
        if not results:
            return []
            
        # Simple filtering - can be enhanced with more sophisticated ranking
        return sorted(
            results,
            key=lambda x: (
                -x.confidence,  # Higher confidence first
                -len(x.content) if x.content else 0,  # Then longer content
                -len(x.snippet)  # Then longer snippets
            )
        )[:self.max_results]

# Example usage
async def test_web_researcher():
    """Test function for the WebResearcher."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    researcher = WebResearcher({
        "search_provider": "mock",  # Change to 'serpapi' when ready
        "max_results": 3
    })
    
    try:
        # Create message using the create method
        message = AgentMessage.create(
            role="user",
            content={
                "query": "latest advancements in renewable energy",
                "max_results": 3,
                "domains": ["example.com", "sciencedirect.com"]
            }
        )
        
        result = await researcher.process(message)
        
        # Get content as dictionary
        result_content = result.content_dict
        
        print("\nSearch Results:")
        print("-" * 50)
        for i, r in enumerate(result_content.get("results", []), 1):
            print(f"\nResult {i}:")
            print(f"Title: {r.get('title', 'No title')}")
            print(f"URL: {r.get('url', 'No URL')}")
            print(f"Domain: {r.get('domain', 'No domain')}")
            print(f"Confidence: {r.get('confidence', 0):.2f}")
            print(f"Snippet: {r.get('snippet', '')[:150]}...")
            if r.get('content'):
                print(f"Content length: {len(r.get('content', ''))} characters")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await researcher.cleanup()

if __name__ == "__main__":
    asyncio.run(test_web_researcher())
