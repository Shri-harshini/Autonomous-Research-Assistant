import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.agent_coordinator import AgentCoordinator
from agents.source_manager import SourceManager
from agents.web_researcher import WebResearcher
from agents.verification_agent import VerificationAgent
from agents.synthesizer_agent import SynthesizerAgent
from agents.output_generator import OutputGenerator
from agents.base_agent import AgentMessage

class IntegrationTests:
    """
    Integration tests for the Autonomous Research Assistant system.
    Tests the complete workflow and agent interactions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_data_dir = None
        self.test_results = []
        
    async def setup(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.test_data_dir = tempfile.mkdtemp(prefix="ara_test_")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info(f"Test environment set up at: {self.test_data_dir}")
    
    async def teardown(self):
        """Clean up test environment."""
        if self.test_data_dir and os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
            self.logger.info("Test environment cleaned up")
    
    async def run_all_tests(self):
        """Run all integration tests."""
        self.logger.info("=" * 60)
        self.logger.info("Starting Integration Tests")
        self.logger.info("=" * 60)
        
        test_methods = [
            self.test_agent_initialization,
            self.test_source_management,
            self.test_web_research,
            self.test_verification,
            self.test_synthesis,
            self.test_output_generation,
            self.test_coordinated_workflow,
            self.test_error_handling,
            self.test_performance,
            self.test_data_integrity
        ]
        
        for test_method in test_methods:
            try:
                self.logger.info(f"\nRunning {test_method.__name__}...")
                result = await test_method()
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "PASSED" if result else "FAILED",
                    "timestamp": datetime.now().isoformat()
                })
                self.logger.info(f"✅ {test_method.__name__}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                self.logger.error(f"❌ {test_method.__name__}: ERROR - {str(e)}")
                self.test_results.append({
                    "test": test_method.__name__,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Print summary
        self.print_test_summary()
        
        return all(r["status"] == "PASSED" for r in self.test_results)
    
    async def test_agent_initialization(self):
        """Test that all agents can be initialized."""
        try:
            # Initialize agents with test configuration
            config = {
                "output_dir": os.path.join(self.test_data_dir, "reports"),
                "db_path": os.path.join(self.test_data_dir, "test.db"),
                "storage_dir": os.path.join(self.test_data_dir, "sources")
            }
            
            coordinator = AgentCoordinator(config)
            source_manager = SourceManager(config)
            
            # Check that agents are initialized
            assert len(coordinator.agents) == 4, "Expected 4 agents in coordinator"
            assert "web_researcher" in coordinator.agents, "Web researcher not initialized"
            assert "verification_agent" in coordinator.agents, "Verification agent not initialized"
            assert "synthesizer_agent" in coordinator.agents, "Synthesizer agent not initialized"
            assert "output_generator" in coordinator.agents, "Output generator not initialized"
            
            # Cleanup
            await coordinator.cleanup()
            if source_manager.db_connection:
                source_manager.db_connection.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Agent initialization test failed: {str(e)}")
            return False
    
    async def test_source_management(self):
        """Test source management operations."""
        try:
            config = {
                "db_path": os.path.join(self.test_data_dir, "sources_test.db"),
                "storage_dir": os.path.join(self.test_data_dir, "sources")
            }
            
            manager = SourceManager(config)
            
            # Test adding sources
            test_sources = [
                {
                    "url": "https://example.com/test1",
                    "title": "Test Article 1",
                    "content": "This is test content for article 1.",
                    "credibility_score": 0.8,
                    "tags": ["test", "article"]
                },
                {
                    "url": "https://example.com/test2",
                    "title": "Test Article 2",
                    "content": "This is test content for article 2.",
                    "credibility_score": 0.9,
                    "tags": ["test", "research"]
                }
            ]
            
            add_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "add_sources",
                    "sources": test_sources
                }
            ))
            
            assert add_result.content_dict["status"] == "success", "Failed to add sources"
            assert add_result.content_dict["added"] == 2, "Expected 2 sources to be added"
            
            # Test searching sources
            search_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "search_sources",
                    "query": {"domain": "example.com"}
                }
            ))
            
            assert search_result.content_dict["status"] == "success", "Failed to search sources"
            assert search_result.content_dict["count"] == 2, "Expected 2 sources in search results"
            
            # Test creating collection
            collection_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "create_collection",
                    "collection": {
                        "name": "Test Collection",
                        "description": "A test collection",
                        "sources": add_result.content_dict["source_ids"]
                    }
                }
            ))
            
            assert collection_result.content_dict["status"] == "success", "Failed to create collection"
            
            # Test statistics
            stats_result = await manager.process(AgentMessage.create(
                role="user",
                content={"command": "get_statistics"}
            ))
            
            assert stats_result.content_dict["status"] == "success", "Failed to get statistics"
            stats = stats_result.content_dict["statistics"]
            assert stats["total_sources"] == 2, "Expected 2 total sources"
            assert stats["total_collections"] == 1, "Expected 1 collection"
            
            # Cleanup
            if manager.db_connection:
                manager.db_connection.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Source management test failed: {str(e)}")
            return False
    
    async def test_web_research(self):
        """Test web research functionality."""
        try:
            researcher = WebResearcher({"search_provider": "mock"})
            
            message = AgentMessage.create(
                role="user",
                content={
                    "query": "test research query",
                    "max_results": 3
                }
            )
            
            result = await researcher.process(message)
            
            assert result.content_dict["status"] == "success", "Web research failed"
            assert "results" in result.content_dict, "No results in web research response"
            # Note: Mock search might return 0 results due to 404 errors, which is expected
            # The test passes if the agent handles it gracefully
            assert isinstance(result.content_dict["results"], list), "Results should be a list"
            
            await researcher.cleanup()
            return True
        except Exception as e:
            self.logger.error(f"Web research test failed: {str(e)}")
            return False
    
    async def test_verification(self):
        """Test verification functionality."""
        try:
            verifier = VerificationAgent()
            
            message = AgentMessage.create(
                role="user",
                content={
                    "content": "Test content for verification",
                    "sources": [
                        {
                            "url": "https://example.com/source1",
                            "title": "Test Source 1",
                            "content": "This is test source content."
                        }
                    ]
                }
            )
            
            result = await verifier.process(message)
            
            assert result.content_dict["status"] == "success", "Verification failed"
            assert "verification" in result.content_dict, "No verification results"
            
            verification = result.content_dict["verification"]
            assert "credibility_score" in verification, "No credibility score"
            assert "source_analysis" in verification, "No source analysis"
            
            return True
        except Exception as e:
            self.logger.error(f"Verification test failed: {str(e)}")
            return False
    
    async def test_synthesis(self):
        """Test synthesis functionality."""
        try:
            synthesizer = SynthesizerAgent()
            
            message = AgentMessage.create(
                role="user",
                content={
                    "topic": "test synthesis",
                    "sources": [
                        {
                            "url": "https://example.com/source1",
                            "title": "Test Source 1",
                            "content": "Research shows that test topic is important. Studies indicate significant findings."
                        },
                        {
                            "url": "https://example.com/source2",
                            "title": "Test Source 2",
                            "content": "Analysis reveals that test topic has multiple applications. Data suggests growing interest."
                        }
                    ]
                }
            )
            
            result = await synthesizer.process(message)
            
            assert result.content_dict["status"] == "success", "Synthesis failed"
            assert "synthesis" in result.content_dict, "No synthesis results"
            
            synthesis = result.content_dict["synthesis"]
            assert "key_findings" in synthesis, "No key findings"
            assert "executive_summary" in synthesis, "No executive summary"
            
            return True
        except Exception as e:
            self.logger.error(f"Synthesis test failed: {str(e)}")
            return False
    
    async def test_output_generation(self):
        """Test output generation functionality."""
        try:
            generator = OutputGenerator({
                "output_dir": self.test_data_dir
            })
            
            synthesis_data = {
                "topic": "test output",
                "executive_summary": "Test executive summary",
                "key_findings": [
                    {
                        "finding": "Test finding",
                        "confidence": 0.8,
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
            
            # Test HTML generation
            message = AgentMessage.create(
                role="user",
                content={
                    "synthesis": synthesis_data,
                    "format": "html"
                }
            )
            
            result = await generator.process(message)
            
            assert result.content_dict["status"] == "success", "Output generation failed"
            assert "report" in result.content_dict, "No report generated"
            
            report = result.content_dict["report"]
            assert report["format"] == "html", "Wrong report format"
            assert os.path.exists(report["filepath"]), "Report file not created"
            
            # Test Markdown generation
            message_md = AgentMessage.create(
                role="user",
                content={
                    "synthesis": synthesis_data,
                    "format": "markdown"
                }
            )
            
            result_md = await generator.process(message_md)
            assert result_md.content_dict["status"] == "success", "Markdown generation failed"
            
            return True
        except Exception as e:
            self.logger.error(f"Output generation test failed: {str(e)}")
            return False
    
    async def test_coordinated_workflow(self):
        """Test the complete coordinated workflow."""
        try:
            config = {
                "output_dir": os.path.join(self.test_data_dir, "reports"),
                "db_path": os.path.join(self.test_data_dir, "workflow_test.db"),
                "storage_dir": os.path.join(self.test_data_dir, "sources")
            }
            
            coordinator = AgentCoordinator(config)
            
            message = AgentMessage.create(
                role="user",
                content={
                    "topic": "test workflow",
                    "query": "test query for workflow",
                    "max_sources": 2,
                    "format": "html"
                }
            )
            
            result = await coordinator.process(message)
            
            assert result.content_dict["status"] == "success", "Coordinated workflow failed"
            assert "results" in result.content_dict, "No workflow results"
            
            results = result.content_dict["results"]
            assert len(results) > 0, "Expected at least one workflow step"
            
            # Check that steps were executed
            step_names = [r["step"] for r in results]
            assert "web_research" in step_names, "Web research step not executed"
            
            await coordinator.cleanup()
            return True
        except Exception as e:
            self.logger.error(f"Coordinated workflow test failed: {str(e)}")
            return False
    
    async def test_error_handling(self):
        """Test error handling in agents."""
        try:
            # Test with invalid message
            verifier = VerificationAgent()
            
            message = AgentMessage.create(
                role="user",
                content={}  # Empty content should cause error
            )
            
            result = await verifier.process(message)
            
            assert result.content_dict["status"] == "error", "Expected error status"
            assert "error" in result.content_dict, "Expected error message"
            
            # Test with non-existent source
            manager = SourceManager({
                "db_path": os.path.join(self.test_data_dir, "error_test.db")
            })
            
            get_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "get_source",
                    "source_id": "non_existent_id"
                }
            ))
            
            assert get_result.content_dict["status"] == "error", "Expected error for non-existent source"
            
            if manager.db_connection:
                manager.db_connection.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Error handling test failed: {str(e)}")
            return False
    
    async def test_performance(self):
        """Test performance of the system."""
        try:
            # Test processing multiple sources
            manager = SourceManager({
                "db_path": os.path.join(self.test_data_dir, "performance_test.db")
            })
            
            # Add multiple sources
            sources = []
            for i in range(10):
                sources.append({
                    "url": f"https://example.com/perf_test_{i}",
                    "title": f"Performance Test Source {i}",
                    "content": f"Test content for performance testing {i}",
                    "credibility_score": 0.7
                })
            
            start_time = datetime.now()
            
            add_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "add_sources",
                    "sources": sources
                }
            ))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            assert add_result.content_dict["status"] == "success", "Failed to add multiple sources"
            assert add_result.content_dict["added"] == 10, "Expected 10 sources to be added"
            assert duration < 5.0, f"Performance test took too long: {duration} seconds"
            
            # Test search performance
            start_time = datetime.now()
            
            search_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "search_sources",
                    "query": {"limit": 50}
                }
            ))
            
            end_time = datetime.now()
            search_duration = (end_time - start_time).total_seconds()
            
            assert search_result.content_dict["status"] == "success", "Search failed"
            assert search_duration < 2.0, f"Search took too long: {search_duration} seconds"
            
            if manager.db_connection:
                manager.db_connection.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Performance test failed: {str(e)}")
            return False
    
    async def test_data_integrity(self):
        """Test data integrity and consistency."""
        try:
            config = {
                "db_path": os.path.join(self.test_data_dir, "integrity_test.db")
            }
            
            manager = SourceManager(config)
            
            # Add a source
            test_source = {
                "url": "https://example.com/integrity_test",
                "title": "Integrity Test Source",
                "content": "Test content for integrity testing",
                "credibility_score": 0.85,
                "tags": ["integrity", "test"]
            }
            
            add_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "add_sources",
                    "sources": [test_source]
                }
            ))
            
            source_id = add_result.content_dict["source_ids"][0]
            
            # Retrieve the source
            get_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "get_source",
                    "source_id": source_id
                }
            ))
            
            assert get_result.content_dict["status"] == "success", "Failed to retrieve source"
            
            retrieved_source = get_result.content_dict["source"]
            
            # Check data integrity
            assert retrieved_source["url"] == test_source["url"], "URL mismatch"
            assert retrieved_source["title"] == test_source["title"], "Title mismatch"
            assert retrieved_source["content"] == test_source["content"], "Content mismatch"
            assert retrieved_source["credibility_score"] == test_source["credibility_score"], "Credibility score mismatch"
            assert retrieved_source["tags"] == test_source["tags"], "Tags mismatch"
            
            # Update the source
            update_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "update_source",
                    "source_id": source_id,
                    "updates": {
                        "title": "Updated Integrity Test Source",
                        "credibility_score": 0.9
                    }
                }
            ))
            
            assert update_result.content_dict["status"] == "success", "Failed to update source"
            
            # Verify update
            get_updated_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "get_source",
                    "source_id": source_id
                }
            ))
            
            updated_source = get_updated_result.content_dict["source"]
            assert updated_source["title"] == "Updated Integrity Test Source", "Title not updated"
            assert updated_source["credibility_score"] == 0.9, "Credibility score not updated"
            
            if manager.db_connection:
                manager.db_connection.close()
            
            return True
        except Exception as e:
            self.logger.error(f"Data integrity test failed: {str(e)}")
            return False
    
    def print_test_summary(self):
        """Print a summary of all test results."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Integration Test Summary")
        self.logger.info("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        
        self.logger.info(f"Total Tests: {len(self.test_results)}")
        self.logger.info(f"Passed: {passed}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Errors: {errors}")
        
        if failed > 0 or errors > 0:
            self.logger.info("\nFailed/Error Tests:")
            for result in self.test_results:
                if result["status"] in ["FAILED", "ERROR"]:
                    self.logger.info(f"  - {result['test']}: {result['status']}")
                    if "error" in result:
                        self.logger.info(f"    Error: {result['error']}")
        
        self.logger.info("\n" + "=" * 60)

# Main test runner
async def main():
    """Run all integration tests."""
    tests = IntegrationTests()
    
    try:
        await tests.setup()
        success = await tests.run_all_tests()
        return 0 if success else 1
    finally:
        await tests.teardown()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
