"""
Weather agent implementation.
"""

import time
from python_a2a import AgentCard, AgentSkill, Message, TextContent, MessageRole, Task, TaskStatus, TaskState
from ..config import logger
from .base_agent import BaseAgent

class WeatherAgent(BaseAgent):
    """Agent that provides weather information for cities."""
    
    def __init__(self):
        """Initialize the weather agent with its capabilities."""
        agent_card = AgentCard(
            name="Weather Agent",
            description="Provides current weather information and forecasts for locations worldwide",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Weather",
                    description="Get current weather conditions for a location",
                    tags=["weather", "current", "temperature", "conditions", "forecast"],
                    examples=["What's the weather in London?", "Is it raining in Tokyo?"]
                ),
                AgentSkill(
                    name="Weather Forecast",
                    description="Get weather forecast for the coming days",
                    tags=["weather", "forecast", "prediction", "upcoming", "future"],
                    examples=["What's the forecast for Paris?", "Will it rain in New York tomorrow?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a weather request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        city = self._extract_city(query)
        
        # Add a small delay to simulate processing
        logger.info(f"[Weather Agent] Processing weather request for {city}...")
        time.sleep(0.5)
        
        if "forecast" in query.lower():
            weather_data = self._get_forecast(city)
        else:
            weather_data = self._get_current_weather(city)
        
        logger.info(f"[Weather Agent] Completed processing for {city}")
        
        return Message(
            content=TextContent(text=weather_data),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based weather request."""
        query = self._extract_query_from_task(task)
        city = self._extract_city(query)
        
        # Add a small delay to simulate processing
        logger.info(f"[Weather Agent] Processing weather request for {city}...")
        time.sleep(0.5)
        
        if "forecast" in query.lower():
            weather_data = self._get_forecast(city)
        else:
            weather_data = self._get_current_weather(city)
        
        logger.info(f"[Weather Agent] Completed processing for {city}")
        
        # Update task with the weather information
        task.artifacts = [{
            "parts": [{"type": "text", "text": weather_data}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_city(self, query: str) -> str:
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for city names in the query
        cities = ["london", "paris", "new york", "tokyo", "sydney", 
                 "berlin", "rome", "madrid", "cairo", "mumbai"]
        
        for city in cities:
            if city in query:
                return city.title()
        
        # Default city if none found
        return "London"
    
    def _get_current_weather(self, city: str) -> str:
        """Get current weather for a city (simulated data)."""
        weather_data = {
            "London": {
                "condition": "Rainy",
                "temperature": "15°C (59°F)",
                "humidity": "85%",
                "wind": "18 km/h"
            },
            "Paris": {
                "condition": "Sunny",
                "temperature": "22°C (72°F)",
                "humidity": "60%",
                "wind": "10 km/h"
            },
            "New York": {
                "condition": "Partly Cloudy",
                "temperature": "18°C (64°F)",
                "humidity": "65%",
                "wind": "15 km/h"
            },
            "Tokyo": {
                "condition": "Clear",
                "temperature": "24°C (75°F)",
                "humidity": "70%",
                "wind": "8 km/h"
            },
            "Sydney": {
                "condition": "Mild",
                "temperature": "20°C (68°F)",
                "humidity": "75%",
                "wind": "12 km/h"
            }
        }
        
        city_data = weather_data.get(city, {"condition": "Unknown", "temperature": "N/A", "humidity": "N/A", "wind": "N/A"})
        
        return f"""Current Weather in {city}:
Condition: {city_data['condition']}
Temperature: {city_data['temperature']}
Humidity: {city_data['humidity']}
Wind Speed: {city_data['wind']}"""
    
    def _get_forecast(self, city: str) -> str:
        """Get a 3-day forecast for a city (simulated data)."""
        # Generate some simulated forecast data
        forecasts = {
            "London": [
                {"day": "Today", "condition": "Rainy", "high": "15°C", "low": "10°C"},
                {"day": "Tomorrow", "condition": "Cloudy", "high": "17°C", "low": "12°C"},
                {"day": "Day 3", "condition": "Partly Cloudy", "high": "18°C", "low": "11°C"}
            ],
            "Paris": [
                {"day": "Today", "condition": "Sunny", "high": "22°C", "low": "14°C"},
                {"day": "Tomorrow", "condition": "Clear", "high": "24°C", "low": "16°C"},
                {"day": "Day 3", "condition": "Partly Cloudy", "high": "21°C", "low": "15°C"}
            ]
        }
        
        # Use default forecast if city not found
        city_forecast = forecasts.get(city, [
            {"day": "Today", "condition": "Unknown", "high": "N/A", "low": "N/A"},
            {"day": "Tomorrow", "condition": "Unknown", "high": "N/A", "low": "N/A"},
            {"day": "Day 3", "condition": "Unknown", "high": "N/A", "low": "N/A"}
        ])
        
        # Format the forecast as text
        result = f"3-Day Weather Forecast for {city}:\n\n"
        for day in city_forecast:
            result += f"{day['day']}: {day['condition']}, High: {day['high']}, Low: {day['low']}\n"
        
        return result 