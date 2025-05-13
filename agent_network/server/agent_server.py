"""
Agent server management module.
"""

import threading
import time
from typing import Dict, List, Optional, Any

from ..config import logger, running_agents
from ..utils import find_free_port

class AgentServer:
    """
    Manages the lifecycle of agent server processes.
    """
    
    @staticmethod
    def start_agent(agent_class, name: str):
        """
        Start an agent server process.
        
        Args:
            agent_class: The agent class to instantiate
            name: The name for the agent
            
        Returns:
            Tuple of (agent instance, server port)
        """
        # Find an available port
        port = find_free_port()
        
        # Create the agent instance
        agent = agent_class()
        
        # Update the agent card URL with the actual port
        if hasattr(agent, "agent_card") and hasattr(agent.agent_card, "url"):
            agent.agent_card.url = f"http://localhost:{port}"
        
        # Start the server in a separate thread
        def run_server():
            try:
                logger.info(f"Starting {name} agent server on port {port}")
                agent.run(host="0.0.0.0", port=port)
            except Exception as e:
                logger.error(f"Error in {name} agent server: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for a moment to let the server start
        time.sleep(1)
        
        # Store the agent in the running agents registry
        running_agents[name] = {
            "instance": agent,
            "thread": server_thread,
            "port": port
        }
        
        return agent, port
    
    @staticmethod
    def stop_agent(name: str) -> bool:
        """
        Stop a running agent server.
        
        Args:
            name: The name of the agent to stop
            
        Returns:
            True if the agent was stopped, False otherwise
        """
        if name not in running_agents:
            logger.warning(f"Agent {name} not found in running agents")
            return False
        
        try:
            # Get the agent
            agent_info = running_agents[name]
            agent = agent_info["instance"]
            
            # Stop the server
            if hasattr(agent, "server") and agent.server:
                logger.info(f"Stopping {name} agent server")
                agent.server.shutdown()
                agent.server.server_close()
            
            # Remove from running agents
            del running_agents[name]
            
            return True
        except Exception as e:
            logger.error(f"Error stopping agent {name}: {e}")
            return False
    
    @staticmethod
    def list_running_agents() -> List[str]:
        """
        List all running agent names.
        
        Returns:
            List of running agent names
        """
        return list(running_agents.keys())
    
    @staticmethod
    def get_agent_info(name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a running agent.
        
        Args:
            name: The name of the agent
            
        Returns:
            Dictionary with agent information or None if not found
        """
        if name not in running_agents:
            return None
        
        agent_info = running_agents[name]
        return {
            "name": name,
            "port": agent_info["port"],
            "endpoint": f"http://localhost:{agent_info['port']}"
        } 