"""
Command Line Interface (CLI) for the agent network.
"""

import sys
import argparse
import time
from typing import List, Dict, Optional

from .config import logger
from .network import AgentNetwork
from .agents import WeatherAgent, KnowledgeAgent
from .server import AgentServer
from .conversation import ConversationOrchestrator
from .utils import find_free_port
from .client import A2ANetworkClient
from python_a2a.models import Message, MessageRole, TextContent

def list_agents():
    """List all available agents in the network."""
    running_agents = AgentServer.list_running_agents()
    
    if not running_agents:
        print("No agents running.")
        return
    
    print("Running agents:")
    for agent_name in running_agents:
        info = AgentServer.get_agent_info(agent_name)
        if info:
            print(f"- {agent_name}: {info['endpoint']}")


def start_all_agents():
    """Start all available agent types."""
    # Start the weather agent
    agent, port = AgentServer.start_agent(WeatherAgent, "weather")
    print(f"Started Weather Agent on port {port}")
    
    # Start the knowledge agent
    agent, port = AgentServer.start_agent(KnowledgeAgent, "knowledge")
    print(f"Started Knowledge Agent on port {port}")
    
    # Wait a moment for agents to initialize
    time.sleep(1)
    
    # Keep the program running so the agents remain active
    print("Agents are running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agents...")
        # You could add cleanup logic here if needed


def query_agent(args):
    """Query a specific agent or let the network route the query."""
    if not args.query:
        print("Error: No query provided.")
        return
    
    # Create agent endpoints dictionary from agent_ports argument
    agent_ports = {}
    if args.agent_ports:
        for port_spec in args.agent_ports:
            if ':' not in port_spec:
                print(f"Error: Invalid port specification: {port_spec}. Format should be agent_name:port")
                return
            agent_name, port = port_spec.split(':', 1)
            try:
                agent_ports[agent_name] = int(port)
            except ValueError:
                print(f"Error: Port must be a number: {port}")
                return
    
    # Create the agent network client with specified ports
    client = A2ANetworkClient()
    client.discover_agents(known_ports=agent_ports if agent_ports else None)
    
    # Check if we have any agents to query
    if not client.agents:
        print("Error: No agents available. Use 'start' command first, or specify agent ports.")
        return
    
    # List the discovered agents
    agents_info = client.list_agents()
    print("Available agents:")
    for agent in agents_info:
        status = "Available" if agent["available"] else "Not available"
        print(f"- {agent['name']}: {agent['endpoint']} ({status})")
    
    # Create the message with proper TextContent
    message = Message(
        content=TextContent(text=args.query),
        role=MessageRole.USER
    )
    
    # Process the query
    if args.agent:
        print(f"Querying {args.agent} agent...")
        response = client.send_message(message, agent_name=args.agent)
    else:
        print("Routing query to the most appropriate agent...")
        response = client.send_message(message)
    
    print("\nResult:")
    if hasattr(response.content, 'text'):
        print(response.content.text)
    else:
        print(response.content)


def run_conversation(args):
    """Run a multi-agent conversation with a specified workflow."""
    if not args.query:
        print("Error: No query provided.")
        return
    
    if not args.workflow:
        print("Error: No workflow specified.")
        return
    
    # Parse the workflow
    workflow = args.workflow.split(",")
    
    # Create agent endpoints dictionary from agent_ports argument
    agent_ports = {}
    if args.agent_ports:
        for port_spec in args.agent_ports:
            if ':' not in port_spec:
                print(f"Error: Invalid port specification: {port_spec}. Format should be agent_name:port")
                return
            agent_name, port = port_spec.split(':', 1)
            try:
                agent_ports[agent_name] = int(port)
            except ValueError:
                print(f"Error: Port must be a number: {port}")
                return
    
    # Create the agent network client with specified ports
    client = A2ANetworkClient()
    client.discover_agents(known_ports=agent_ports if agent_ports else None)
    
    # List the discovered agents
    agents_info = client.list_agents()
    print("Available agents:")
    for agent in agents_info:
        status = "Available" if agent["available"] else "Not available"
        print(f"- {agent['name']}: {agent['endpoint']} ({status})")
    
    # Check if all workflow agents are available
    available_agents = set(client.agents.keys())
    for agent_name in workflow:
        if agent_name not in available_agents:
            print(f"Error: Agent '{agent_name}' not found in the network.")
            return
    
    # Create the initial message with proper TextContent
    initial_message = Message(
        content=TextContent(text=args.query),
        role=MessageRole.USER
    )
    
    try:
        print("Starting multi-agent conversation...")
        # Run the workflow
        conversation = client.run_workflow(initial_message, workflow)
        
        # Print the conversation history
        print("\nConversation History:")
        for i, message in enumerate(conversation.messages):
            print(f"[{message.role}]: ", end="")
            if hasattr(message.content, 'text'):
                print(message.content.text)
            else:
                print(message.content)
            print()
        
        # Get the final message
        if conversation.messages:
            final_message = conversation.messages[-1]
            print("\nFinal Result:")
            if hasattr(final_message.content, 'text'):
                print(final_message.content.text)
            else:
                print(final_message.content)
        else:
            print("\nNo result produced.")
    
    except Exception as e:
        print(f"Error in conversation: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Agent Network CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start agent servers")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available agents")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the agent network")
    query_parser.add_argument("--agent", help="Specific agent to query (weather, knowledge)")
    query_parser.add_argument("--router-type", default="keyword", choices=["keyword", "ai"], 
                              help="Type of routing to use (default: keyword)")
    query_parser.add_argument("--agent-ports", nargs="+", 
                              help="Custom agent ports in format 'agent_name:port' (e.g., 'weather:59983')")
    query_parser.add_argument("query", nargs="?", help="The query text")
    
    # Conversation command
    conv_parser = subparsers.add_parser("conversation", help="Run a multi-agent conversation")
    conv_parser.add_argument("--workflow", help="Comma-separated list of agent names in workflow order")
    conv_parser.add_argument("--agent-ports", nargs="+", 
                             help="Custom agent ports in format 'agent_name:port' (e.g., 'weather:59983')")
    conv_parser.add_argument("query", nargs="?", help="The initial query text")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_all_agents()
    elif args.command == "list":
        list_agents()
    elif args.command == "query":
        query_agent(args)
    elif args.command == "conversation":
        run_conversation(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 