#!/usr/bin/env python3
"""
Autonomous Research Assistant - Complete System Demo

This script demonstrates the full capabilities of the ARA system
by running a complete research workflow from start to finish.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents.agent_coordinator import AgentCoordinator
from agents.source_manager import SourceManager
from agents.web_researcher import WebResearcher
from agents.verification_agent import VerificationAgent
from agents.synthesizer_agent import SynthesizerAgent
from agents.output_generator import OutputGenerator
from agents.base_agent import AgentMessage

class ARADemo:
    """Complete demonstration of the Autonomous Research Assistant."""
    
    def __init__(self):
        self.start_time = time.time()
        self.demo_results = []
        
    async def run_complete_demo(self):
        """Run a complete demonstration of the ARA system."""
        print("=" * 80)
        print("🤖 AUTONOMOUS RESEARCH ASSISTANT - COMPLETE DEMO")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Demo topics
        demo_topics = [
            {
                "topic": "Artificial Intelligence in Healthcare",
                "query": "AI applications in medical diagnosis and treatment",
                "description": "Exploring how AI is transforming healthcare"
            },
            {
                "topic": "Renewable Energy Trends",
                "query": "latest developments in solar and wind energy",
                "description": "Current state and future of renewable energy"
            },
            {
                "topic": "Climate Change Impacts",
                "query": "effects of climate change on global agriculture",
                "description": "Understanding climate change effects on food production"
            }
        ]
        
        for i, topic_data in enumerate(demo_topics, 1):
            print(f"🔍 Demo {i}/{len(demo_topics)}: {topic_data['topic']}")
            print(f"   Query: {topic_data['query']}")
            print(f"   Description: {topic_data['description']}")
            print()
            
            await self.run_research_demo(topic_data)
            
            if i < len(demo_topics):
                print("\n" + "-" * 80)
                print()
        
        await self.show_final_summary()
    
    async def run_research_demo(self, topic_data):
        """Run research for a single topic."""
        topic = topic_data["topic"]
        query = topic_data["query"]
        
        # Initialize coordinator
        config = {
            "output_dir": "demo_reports",
            "db_path": "demo_data/sources.db",
            "storage_dir": "demo_data/sources"
        }
        
        coordinator = AgentCoordinator(config)
        
        try:
            # Create research request
            message = AgentMessage.create(
                role="user",
                content={
                    "topic": topic,
                    "query": query,
                    "max_sources": 3,
                    "format": "html"
                }
            )
            
            print("🚀 Starting research workflow...")
            
            # Run the complete workflow
            result = await coordinator.process(message)
            
            # Process results
            await self.process_workflow_results(result, topic_data)
            
        except Exception as e:
            print(f"❌ Error in research demo: {str(e)}")
            self.demo_results.append({
                "topic": topic,
                "status": "error",
                "error": str(e)
            })
        
        finally:
            await coordinator.cleanup()
    
    async def process_workflow_results(self, result, topic_data):
        """Process and display workflow results."""
        topic = topic_data["topic"]
        
        if result.content_dict.get("status") == "success":
            workflow_results = result.content_dict.get("results", [])
            
            print("\n📊 Workflow Results:")
            print("-" * 40)
            
            sources_collected = 0
            report_generated = False
            
            for step in workflow_results:
                step_name = step.get("step", "unknown")
                status = step.get("status", "unknown")
                duration = step.get("duration", 0)
                agent = step.get("agent", "unknown")
                
                # Status icon
                if status == "completed":
                    icon = "✅"
                elif status == "error":
                    icon = "❌"
                else:
                    icon = "⏳"
                
                print(f"{icon} {step_name.title().replace('_', ' ')} ({agent})")
                print(f"   Status: {status.upper()}")
                print(f"   Duration: {duration:.2f}s")
                
                # Extract specific information
                if status == "completed" and step.get("result"):
                    step_result = step["result"]
                    
                    if step_name == "web_research":
                        sources = step_result.get("results", [])
                        sources_collected = len(sources)
                        print(f"   Sources found: {sources_collected}")
                        
                        # Show sample sources
                        for i, source in enumerate(sources[:2], 1):
                            print(f"     {i}. {source.get('title', 'No title')[:50]}...")
                    
                    elif step_name == "verification":
                        verification = step_result.get("verification", {})
                        credibility = verification.get("credibility_score", 0)
                        print(f"   Overall credibility: {credibility:.2f}")
                        
                        source_analysis = verification.get("source_analysis", {})
                        high_cred = source_analysis.get("high_credibility", 0)
                        print(f"   High credibility sources: {high_cred}")
                    
                    elif step_name == "synthesis":
                        synthesis = step_result.get("synthesis", {})
                        findings = len(synthesis.get("key_findings", []))
                        trends = len(synthesis.get("trends", []))
                        agreements = len(synthesis.get("agreements", []))
                        
                        print(f"   Key findings: {findings}")
                        print(f"   Trends identified: {trends}")
                        print(f"   Areas of agreement: {agreements}")
                        
                        # Show executive summary
                        exec_summary = synthesis.get("executive_summary", "")
                        if exec_summary:
                            print(f"   Summary: {exec_summary[:100]}...")
                    
                    elif step_name == "output_generation":
                        report = step_result.get("report", {})
                        report_generated = True
                        print(f"   Report: {report.get('filename', 'Unknown')}")
                        print(f"   Format: {report.get('format', 'Unknown')}")
                        print(f"   Size: {report.get('size', 0)} bytes")
                
                print()
            
            # Store results
            self.demo_results.append({
                "topic": topic,
                "status": "success",
                "sources_collected": sources_collected,
                "report_generated": report_generated,
                "workflow_steps": len(workflow_results)
            })
            
            if report_generated:
                print("🎉 Research completed successfully!")
                print("📄 Report generated and saved to demo_reports/")
            else:
                print("⚠️ Research completed but no report generated")
        
        else:
            error = result.content_dict.get("error", "Unknown error")
            print(f"❌ Research failed: {error}")
            self.demo_results.append({
                "topic": topic,
                "status": "error",
                "error": error
            })
    
    async def show_final_summary(self):
        """Show final summary of all demos."""
        total_time = time.time() - self.start_time
        
        print("=" * 80)
        print("📈 FINAL DEMO SUMMARY")
        print("=" * 80)
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Demos completed: {len(self.demo_results)}")
        print()
        
        successful = sum(1 for r in self.demo_results if r["status"] == "success")
        failed = sum(1 for r in self.demo_results if r["status"] == "error")
        
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print()
        
        if successful > 0:
            total_sources = sum(r.get("sources_collected", 0) for r in self.demo_results if r["status"] == "success")
            total_reports = sum(1 for r in self.demo_results if r.get("report_generated", False))
            
            print(f"📚 Total sources collected: {total_sources}")
            print(f"📄 Reports generated: {total_reports}")
            print()
        
        print("📋 Detailed Results:")
        print("-" * 40)
        
        for i, result in enumerate(self.demo_results, 1):
            topic = result["topic"]
            status = result["status"]
            
            if status == "success":
                sources = result.get("sources_collected", 0)
                report = "✅" if result.get("report_generated", False) else "⚠️"
                print(f"{i}. {topic}")
                print(f"   Status: ✅ SUCCESS")
                print(f"   Sources: {sources}")
                print(f"   Report: {report}")
            else:
                error = result.get("error", "Unknown error")
                print(f"{i}. {topic}")
                print(f"   Status: ❌ ERROR")
                print(f"   Error: {error}")
            print()
        
        print("=" * 80)
        print("🎉 DEMO COMPLETED!")
        print("=" * 80)
        
        if successful == len(self.demo_results):
            print("🌟 All demos completed successfully!")
            print("📁 Check the 'demo_reports' directory for generated reports")
        else:
            print("⚠️ Some demos had issues - check the logs above")
        
        print("\nNext steps:")
        print("1. Open the generated HTML reports in your browser")
        print("2. Explore the source database in demo_data/")
        print("3. Try your own research topics")
        print("4. Customize the agents and templates")
        print("5. Read the full documentation for advanced features")

async def run_individual_agent_demo():
    """Demonstrate individual agent capabilities."""
    print("\n" + "=" * 80)
    print("🔧 INDIVIDUAL AGENT DEMOS")
    print("=" * 80)
    
    # Demo 1: Source Manager
    print("\n1. 📚 Source Manager Demo")
    print("-" * 40)
    
    manager = SourceManager({
        "db_path": "demo_data/individual_demo.db"
    })
    
    try:
        # Add test sources
        test_sources = [
            {
                "url": "https://example.com/ai-healthcare",
                "title": "AI in Healthcare: Revolution",
                "content": "Artificial intelligence is transforming healthcare with diagnostic applications.",
                "credibility_score": 0.85,
                "tags": ["AI", "healthcare", "diagnosis"]
            },
            {
                "url": "https://example.com/renewable-energy",
                "title": "Renewable Energy Future",
                "content": "Solar and wind energy are becoming increasingly cost-effective.",
                "credibility_score": 0.9,
                "tags": ["renewable", "energy", "solar"]
            }
        ]
        
        add_result = await manager.process(AgentMessage.create(
            role="user",
            content={
                "command": "add_sources",
                "sources": test_sources
            }
        ))
        
        if add_result.content_dict["status"] == "success":
            print(f"✅ Added {add_result.content_dict['added']} sources")
            
            # Search sources
            search_result = await manager.process(AgentMessage.create(
                role="user",
                content={
                    "command": "search_sources",
                    "query": {"tags": ["AI"]}
                }
            ))
            
            if search_result.content_dict["status"] == "success":
                found = search_result.content_dict["count"]
                print(f"✅ Found {found} sources with 'AI' tag")
            
            # Get statistics
            stats_result = await manager.process(AgentMessage.create(
                role="user",
                content={"command": "get_statistics"}
            ))
            
            if stats_result.content_dict["status"] == "success":
                stats = stats_result.content_dict["statistics"]
                print(f"📊 Database stats: {stats['total_sources']} sources, {stats['unique_domains']} domains")
    
    finally:
        if manager.db_connection:
            manager.db_connection.close()
    
    # Demo 2: Web Researcher
    print("\n2. 🔍 Web Researcher Demo")
    print("-" * 40)
    
    researcher = WebResearcher({"search_provider": "mock"})
    
    try:
        search_result = await researcher.process(AgentMessage.create(
            role="user",
            content={
                "query": "quantum computing applications",
                "max_results": 2
            }
        ))
        
        if search_result.content_dict["status"] == "success":
            results = search_result.content_dict["results"]
            print(f"✅ Found {len(results)} search results")
            
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['title']}")
                print(f"      URL: {result['url']}")
                print(f"      Confidence: {result['confidence']:.2f}")
    
    finally:
        await researcher.cleanup()
    
    # Demo 3: Output Generator
    print("\n3. 📄 Output Generator Demo")
    print("-" * 40)
    
    generator = OutputGenerator({"output_dir": "demo_reports"})
    
    # Create sample synthesis data
    sample_synthesis = {
        "topic": "Sample Research Topic",
        "executive_summary": "This is a sample executive summary demonstrating the output generation capabilities.",
        "key_findings": [
            {
                "finding": "Sample finding 1: Important discovery",
                "confidence": 0.9,
                "sources": ["source1"],
                "importance": "high"
            },
            {
                "finding": "Sample finding 2: Secondary observation",
                "confidence": 0.7,
                "sources": ["source2"],
                "importance": "medium"
            }
        ],
        "trends": [],
        "agreements": [],
        "disagreements": [],
        "knowledge_gaps": [],
        "source_count": 2
    }
    
    try:
        # Generate HTML report
        html_result = await generator.process(AgentMessage.create(
            role="user",
            content={
                "synthesis": sample_synthesis,
                "format": "html",
                "include_toc": True
            }
        ))
        
        if html_result.content_dict["status"] == "success":
            report = html_result.content_dict["report"]
            print(f"✅ HTML report generated: {report['filename']}")
        
        # Generate Markdown report
        md_result = await generator.process(AgentMessage.create(
            role="user",
            content={
                "synthesis": sample_synthesis,
                "format": "markdown",
                "include_toc": True
            }
        ))
        
        if md_result.content_dict["status"] == "success":
            report = md_result.content_dict["report"]
            print(f"✅ Markdown report generated: {report['filename']}")
    
    except Exception as e:
        print(f"❌ Output generator error: {str(e)}")

async def main():
    """Main demo function."""
    print("🚀 Starting Autonomous Research Assistant Demo")
    print("This demo showcases the complete capabilities of the ARA system")
    print()
    
    # Create demo directories
    os.makedirs("demo_reports", exist_ok=True)
    os.makedirs("demo_data", exist_ok=True)
    
    # Run complete workflow demo
    demo = ARADemo()
    await demo.run_complete_demo()
    
    # Run individual agent demos
    await run_individual_agent_demo()
    
    print("\n" + "=" * 80)
    print("🎊 DEMO COMPLETE!")
    print("=" * 80)
    print("\nThank you for trying the Autonomous Research Assistant!")
    print("Check out the documentation for more features and customization options.")
    print("\n📚 Documentation:")
    print("  - QUICK_START.md: Get started in 5 minutes")
    print("  - DOCUMENTATION.md: Complete system documentation")
    print("  - API_REFERENCE.md: Detailed API reference")
    print("\n🔧 Next Steps:")
    print("  1. Open generated reports in demo_reports/")
    print("  2. Try your own research topics")
    print("  3. Customize agents and templates")
    print("  4. Integrate with your applications")

if __name__ == "__main__":
    asyncio.run(main())
