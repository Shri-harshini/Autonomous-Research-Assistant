import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
import logging
from datetime import datetime
from enum import Enum
from .base_agent import BaseAgent, AgentMessage
from .web_researcher import WebResearcher
from .verification_agent import VerificationAgent
from .synthesizer_agent import SynthesizerAgent
from .output_generator import OutputGenerator

class AgentStatus(Enum):
    """Enumeration for agent status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"

@dataclass
class AgentTask:
    """Data class to represent a task for an agent."""
    id: str
    agent_name: str
    message: AgentMessage
    dependencies: List[str] = None
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowStep:
    """Data class to represent a workflow step."""
    name: str
    agent: str
    description: str
    required: bool = True
    parallel: bool = False
    timeout: int = 300  # 5 minutes default

class AgentCoordinator(BaseAgent):
    """
    Agent Coordinator responsible for:
    - Managing agent workflow and execution order
    - Handling inter-agent communication
    - Monitoring task progress
    - Error handling and recovery
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the AgentCoordinator with optional configuration."""
        super().__init__(
            name="AgentCoordinator",
            description="Coordinates and manages the execution of multiple research agents"
        )
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Task management
        self.tasks = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        
        # Workflow definition
        self.workflow = self._define_workflow()
        
        # Event tracking
        self.events = []
        self.current_workflow_id = None
        
        # Configuration
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 3)
        self.default_timeout = self.config.get("default_timeout", 300)
        self.retry_attempts = self.config.get("retry_attempts", 2)
    
    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all available agents."""
        agents = {}
        
        try:
            # Web Researcher
            agents["web_researcher"] = WebResearcher(
                self.config.get("web_researcher", {})
            )
            
            # Verification Agent
            agents["verification_agent"] = VerificationAgent(
                self.config.get("verification_agent", {})
            )
            
            # Synthesizer Agent
            agents["synthesizer_agent"] = SynthesizerAgent(
                self.config.get("synthesizer_agent", {})
            )
            
            # Output Generator
            agents["output_generator"] = OutputGenerator(
                self.config.get("output_generator", {})
            )
            
            self.logger.info(f"Initialized {len(agents)} agents")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {str(e)}")
            
        return agents
    
    def _define_workflow(self) -> List[WorkflowStep]:
        """Define the standard research workflow."""
        return [
            WorkflowStep(
                name="web_research",
                agent="web_researcher",
                description="Conduct web research and gather sources",
                required=True,
                parallel=False,
                timeout=300
            ),
            WorkflowStep(
                name="verification",
                agent="verification_agent",
                description="Verify sources and assess credibility",
                required=True,
                parallel=False,
                timeout=180
            ),
            WorkflowStep(
                name="synthesis",
                agent="synthesizer_agent",
                description="Synthesize information from verified sources",
                required=True,
                parallel=False,
                timeout=240
            ),
            WorkflowStep(
                name="output_generation",
                agent="output_generator",
                description="Generate final report",
                required=True,
                parallel=False,
                timeout=120
            )
        ]
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process a research request through the coordinated workflow.
        
        Args:
            message: AgentMessage containing research request
            
        Returns:
            AgentMessage with workflow results
        """
        try:
            content = message.content_dict
            
            # Extract research parameters
            topic = content.get("topic", "")
            query = content.get("query", topic)
            max_sources = content.get("max_sources", 5)
            output_format = content.get("format", "html")
            
            if not topic and not query:
                raise ValueError("No topic or query provided for research")
            
            # Generate unique workflow ID
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_workflow_id = workflow_id
            
            self.logger.info(f"Starting workflow {workflow_id} for topic: {topic}")
            
            # Execute workflow
            workflow_results = await self.execute_workflow(
                topic=topic,
                query=query,
                max_sources=max_sources,
                output_format=output_format
            )
            
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "success",
                    "workflow_id": workflow_id,
                    "results": workflow_results
                },
                metadata={
                    "agent": self.name,
                    "workflow_id": workflow_id,
                    "steps_completed": len([r for r in workflow_results if r.get("status") == "completed"])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in AgentCoordinator: {str(e)}", exc_info=True)
            return AgentMessage.create(
                role="assistant",
                content={
                    "status": "error",
                    "error": str(e)
                },
                metadata={"agent": self.name}
            )
    
    async def execute_workflow(self, topic: str, query: str, max_sources: int, output_format: str) -> List[Dict[str, Any]]:
        """
        Execute the complete research workflow.
        
        Args:
            topic: Research topic
            query: Search query
            max_sources: Maximum number of sources to collect
            output_format: Output format for the report
            
        Returns:
            List of workflow step results
        """
        results = []
        context = {
            "topic": topic,
            "query": query,
            "max_sources": max_sources,
            "output_format": output_format,
            "sources": [],
            "verified_sources": [],
            "synthesis": None
        }
        
        try:
            # Step 1: Web Research
            self.logger.info("Step 1: Conducting web research...")
            research_result = await self.execute_step(
                step_name="web_research",
                context=context
            )
            results.append(research_result)
            
            if research_result.get("status") == "completed":
                context["sources"] = research_result.get("result", {}).get("results", [])
                self.logger.info(f"Collected {len(context['sources'])} sources")
            else:
                self.logger.error("Web research failed. Stopping workflow.")
                return results
            
            # Step 2: Verification
            self.logger.info("Step 2: Verifying sources...")
            verification_result = await self.execute_step(
                step_name="verification",
                context=context
            )
            results.append(verification_result)
            
            if verification_result.get("status") == "completed":
                # Filter sources based on verification
                verification_data = verification_result.get("result", {}).get("verification", {})
                credibility_score = verification_data.get("credibility_score", 0)
                
                # Keep sources with reasonable credibility
                context["verified_sources"] = [
                    source for source in context["sources"]
                    if self._get_source_credibility(source, verification_data) > 0.3
                ]
                self.logger.info(f"Verified {len(context['verified_sources'])} sources")
            else:
                self.logger.warning("Verification failed. Proceeding with unverified sources.")
                context["verified_sources"] = context["sources"]
            
            # Step 3: Synthesis
            self.logger.info("Step 3: Synthesizing information...")
            synthesis_result = await self.execute_step(
                step_name="synthesis",
                context=context
            )
            results.append(synthesis_result)
            
            if synthesis_result.get("status") == "completed":
                context["synthesis"] = synthesis_result.get("result", {}).get("synthesis", {})
                self.logger.info("Synthesis completed successfully")
            else:
                self.logger.error("Synthesis failed. Stopping workflow.")
                return results
            
            # Step 4: Output Generation
            self.logger.info("Step 4: Generating report...")
            output_result = await self.execute_step(
                step_name="output_generation",
                context=context
            )
            results.append(output_result)
            
            if output_result.get("status") == "completed":
                self.logger.info("Report generated successfully")
            else:
                self.logger.error("Report generation failed")
            
        except Exception as e:
            self.logger.error(f"Workflow execution error: {str(e)}")
            results.append({
                "step": "workflow_error",
                "status": "error",
                "error": str(e)
            })
        
        return results
    
    async def execute_step(self, step_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step_name: Name of the workflow step
            context: Current workflow context
            
        Returns:
            Step execution result
        """
        # Find the workflow step
        step = next((s for s in self.workflow if s.name == step_name), None)
        if not step:
            return {
                "step": step_name,
                "status": "error",
                "error": f"Unknown workflow step: {step_name}"
            }
        
        # Get the agent
        agent = self.agents.get(step.agent)
        if not agent:
            return {
                "step": step_name,
                "status": "error",
                "error": f"Agent not found: {step.agent}"
            }
        
        # Prepare message for the agent
        message = self._prepare_agent_message(step_name, context)
        
        # Execute the step with timeout
        try:
            start_time = datetime.now()
            
            self.logger.info(f"Executing step {step_name} with agent {step.agent}")
            
            # Run with timeout
            result = await asyncio.wait_for(
                agent.process(message),
                timeout=step.timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Parse result
            result_content = result.content_dict
            
            return {
                "step": step_name,
                "agent": step.agent,
                "status": "completed" if result_content.get("status") == "success" else "error",
                "result": result_content if result_content.get("status") == "success" else None,
                "error": result_content.get("error") if result_content.get("status") == "error" else None,
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
            
        except asyncio.TimeoutError:
            return {
                "step": step_name,
                "agent": step.agent,
                "status": "error",
                "error": f"Step timed out after {step.timeout} seconds",
                "duration": step.timeout
            }
        except Exception as e:
            return {
                "step": step_name,
                "agent": step.agent,
                "status": "error",
                "error": str(e),
                "duration": 0
            }
    
    def _prepare_agent_message(self, step_name: str, context: Dict[str, Any]) -> AgentMessage:
        """
        Prepare a message for an agent based on the workflow step.
        
        Args:
            step_name: Name of the workflow step
            context: Current workflow context
            
        Returns:
            AgentMessage for the agent
        """
        if step_name == "web_research":
            return AgentMessage.create(
                role="user",
                content={
                    "query": context.get("query", context.get("topic", "")),
                    "max_results": context.get("max_sources", 5)
                }
            )
        
        elif step_name == "verification":
            return AgentMessage.create(
                role="user",
                content={
                    "content": f"Research on {context.get('topic', '')}",
                    "sources": context.get("sources", [])
                }
            )
        
        elif step_name == "synthesis":
            return AgentMessage.create(
                role="user",
                content={
                    "topic": context.get("topic", ""),
                    "sources": context.get("verified_sources", [])
                }
            )
        
        elif step_name == "output_generation":
            return AgentMessage.create(
                role="user",
                content={
                    "synthesis": context.get("synthesis", {}),
                    "format": context.get("output_format", "html"),
                    "include_toc": True
                }
            )
        
        else:
            raise ValueError(f"Unknown step: {step_name}")
    
    def _get_source_credibility(self, source: Dict[str, Any], verification_data: Dict[str, Any]) -> float:
        """
        Get credibility score for a source.
        
        Args:
            source: Source dictionary
            verification_data: Verification results
            
        Returns:
            Credibility score (0.0 to 1.0)
        """
        # Simple implementation - can be enhanced
        domain = source.get("domain", "")
        
        # Check domain credibility from verification
        source_analysis = verification_data.get("source_analysis", {})
        domains = source_analysis.get("domains", {})
        
        if domain in domains:
            return domains[domain].get("credibility_score", 0.5)
        
        # Default credibility
        return 0.5
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        # This would typically be stored in a database
        # For now, return current status
        return {
            "workflow_id": workflow_id,
            "status": "completed" if workflow_id == self.current_workflow_id else "not_found",
            "agents_available": list(self.agents.keys()),
            "workflow_steps": len(self.workflow)
        }
    
    async def cleanup(self):
        """Clean up resources."""
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'cleanup'):
                try:
                    await agent.cleanup()
                except Exception as e:
                    self.logger.warning(f"Error cleaning up agent {agent_name}: {str(e)}")

# Example usage
async def test_agent_coordinator():
    """Test function for the AgentCoordinator."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    coordinator = AgentCoordinator({
        "max_concurrent_tasks": 2,
        "default_timeout": 300
    })
    
    try:
        # Create test research request
        message = AgentMessage.create(
            role="user",
            content={
                "topic": "artificial intelligence in healthcare",
                "query": "AI applications in medical diagnosis",
                "max_sources": 3,
                "format": "html"
            }
        )
        
        print("\nStarting coordinated research workflow...")
        print("=" * 60)
        
        result = await coordinator.process(message)
        
        # Get content as dictionary
        result_content = result.content_dict
        
        print("\nWorkflow Results:")
        print("-" * 60)
        
        if result_content.get("status") == "success":
            workflow_id = result_content.get("workflow_id", "")
            results = result_content.get("results", [])
            
            print(f"✅ Workflow {workflow_id} completed successfully!")
            print(f"\nSteps executed: {len(results)}")
            
            for i, step_result in enumerate(results, 1):
                step_name = step_result.get("step", "unknown")
                status = step_result.get("status", "unknown")
                duration = step_result.get("duration", 0)
                agent = step_result.get("agent", "unknown")
                
                print(f"\n{i}. {step_name.title()} ({agent})")
                print(f"   Status: {status.upper()}")
                print(f"   Duration: {duration:.2f} seconds")
                
                if status == "error":
                    print(f"   Error: {step_result.get('error', 'Unknown error')}")
                elif step_result.get("result"):
                    if step_name == "web_research":
                        sources = step_result["result"].get("results", [])
                        print(f"   Sources found: {len(sources)}")
                    elif step_name == "verification":
                        verification = step_result["result"].get("verification", {})
                        credibility = verification.get("credibility_score", 0)
                        print(f"   Overall credibility: {credibility:.2f}")
                    elif step_name == "synthesis":
                        synthesis = step_result["result"].get("synthesis", {})
                        findings = len(synthesis.get("key_findings", []))
                        print(f"   Key findings: {findings}")
                    elif step_name == "output_generation":
                        report = step_result["result"].get("report", {})
                        print(f"   Report: {report.get('filename', 'Unknown')}")
            
            print("\n" + "=" * 60)
            print("✅ Research workflow completed successfully!")
            
        else:
            print(f"❌ Workflow failed: {result_content.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await coordinator.cleanup()

if __name__ == "__main__":
    asyncio.run(test_agent_coordinator())
