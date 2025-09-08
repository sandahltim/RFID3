"""
AI Agent Core - LangChain LLM Integration with Local Ollama
Minnesota Equipment Rental Business Intelligence Agent
"""

import logging
from typing import Dict, List, Optional, Any, Union, Callable
import json
import asyncio
from datetime import datetime
import os
from dataclasses import dataclass

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.agents.output_parsers import OpenAIToolsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_tool_messages
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

from ..tools.database_tool import DatabaseQueryTool
from ..tools.weather_tool import WeatherTool
from ..tools.events_tool import EventsTool
from ..tools.permits_tool import PermitsTool

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Structured agent response"""
    success: bool
    response: str
    confidence: float
    tools_used: List[str]
    execution_time_ms: int
    insights: List[str]
    recommendations: List[str]
    data_sources: List[str]
    error: Optional[str] = None


class MinnesotaEquipmentRentalAgent:
    """
    AI Agent for Minnesota Equipment Rental Business Intelligence
    
    Combines LangChain with local Ollama LLM for:
    - Natural language business query processing
    - Multi-tool orchestration (database, weather, events, permits)
    - Equipment rental demand analysis and forecasting
    - Business insight generation with Minnesota-specific context
    """
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model_name: str = "qwen2.5:7b-instruct",
        db_connection_string: str = None,
        api_keys: Dict[str, str] = None,
        **kwargs
    ):
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.db_connection_string = db_connection_string
        self.api_keys = api_keys or {}
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Create agent
        self.agent = self._create_agent()
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Business context
        self.business_context = self._load_business_context()
        
        logger.info(f"Minnesota Equipment Rental AI Agent initialized with model: {model_name}")
    
    def _initialize_llm(self) -> ChatOllama:
        """Initialize local Ollama LLM"""
        try:
            llm = ChatOllama(
                base_url=self.ollama_host,
                model=self.model_name,
                temperature=0.1,  # Low temperature for factual responses
                top_p=0.9,
                num_ctx=8192,  # Context window
                repeat_penalty=1.1,
                verbose=False
            )
            
            # Test connection
            test_response = llm.invoke("Test connection")
            logger.info("LLM connection successful")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all LangChain tools"""
        tools = []
        
        try:
            # Database query tool
            if self.db_connection_string:
                db_tool = DatabaseQueryTool(
                    connection_string=self.db_connection_string,
                    name="database_query",
                    description="Query equipment rental database for inventory, financial, and operational data"
                )
                tools.append(db_tool)
                logger.info("Database tool initialized")
            
            # Weather tool
            weather_tool = WeatherTool(
                openweather_api_key=self.api_keys.get('openweather'),
                noaa_api_key=self.api_keys.get('noaa'),
                name="weather_data",
                description="Get Minnesota weather data and analyze impact on equipment rental demand"
            )
            tools.append(weather_tool)
            
            # Events tool
            events_tool = EventsTool(
                name="events_data",
                description="Get Minnesota events and festivals data for rental demand forecasting"
            )
            tools.append(events_tool)
            
            # Permits tool
            permits_tool = PermitsTool(
                minneapolis_api_key=self.api_keys.get('minneapolis'),
                saint_paul_api_key=self.api_keys.get('saint_paul'),
                name="permits_data",
                description="Analyze building permits for construction equipment demand prediction"
            )
            tools.append(permits_tool)
            
            logger.info(f"Initialized {len(tools)} tools")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            return []
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools"""
        
        # Create prompt template
        system_prompt = self._create_system_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate",
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    def _create_system_prompt(self) -> str:
        """Create system prompt with business context"""
        return f"""You are an AI business intelligence agent for a Minnesota equipment rental company with two divisions:

**Company Profile:**
- A1 Rent It (70%): Construction equipment - excavators, skid steers, compressors, generators
- Broadway Tent & Event (30%): Event equipment - tents, tables, chairs, stages, lighting
- 4 Locations: Wayzata, Brooklyn Park, Fridley, Elk River
- Database: MariaDB with inventory, POS, and financial data

**Your Expertise:**
- Equipment rental demand analysis and forecasting
- Financial performance analysis and optimization
- Weather impact assessment on equipment needs
- Minnesota events and construction activity monitoring
- Inventory management and utilization optimization
- Seasonal demand patterns and planning

**Key Capabilities:**
- Query equipment inventory and financial databases
- Analyze Minnesota weather patterns for business impact
- Monitor construction permits for equipment demand
- Track events and festivals driving rental needs
- Generate actionable business insights and recommendations

**Response Guidelines:**
1. Always provide specific, actionable business insights
2. Include confidence levels for predictions and analyses
3. Reference data sources and methodology used
4. Consider Minnesota's seasonal patterns and climate
5. Focus on ROI and profitability implications
6. Suggest concrete next steps and recommendations

**Data Sources Available:**
- Equipment inventory and status (id_item_master)
- POS transactions and financial data
- Weather APIs (NOAA, OpenWeather)
- Minnesota events and festivals data
- Minneapolis/St. Paul building permits
- Equipment utilization and rental history

**Business Context:**
{self.business_context}

Respond in a professional, analytical tone with clear insights backed by data. Always aim to help optimize business operations and increase profitability.
"""
    
    def _load_business_context(self) -> str:
        """Load Minnesota-specific business context"""
        return """
**Minnesota Market Context:**
- Construction season: April-October (limited winter activity)
- Peak event season: May-September (State Fair, weddings, festivals)
- Winter challenges: Sub-zero temperatures, snow removal equipment demand
- Key markets: Twin Cities metro, construction, agriculture, events

**Seasonal Patterns:**
- Spring: Construction ramp-up, landscaping equipment peak
- Summer: Event equipment peak, State Fair (major revenue driver)
- Fall: Construction completion rush, harvest activity
- Winter: Indoor equipment focus, heating equipment demand

**Competitive Advantages:**
- Geographic coverage across metro area
- Dual market focus (construction + events)
- Established customer relationships
- Comprehensive equipment inventory
"""
    
    async def query(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process natural language query and return structured response
        
        Args:
            user_input: Natural language business question
            context: Optional context information
            
        Returns:
            AgentResponse with insights and recommendations
        """
        start_time = datetime.now()
        
        try:
            # Enhance input with context
            enhanced_input = self._enhance_input(user_input, context)
            
            # Execute agent
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.agent.invoke({
                    "input": enhanced_input,
                    "chat_history": self.memory.chat_memory.messages
                })
            )
            
            # Process response
            response = self._process_agent_response(result)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract insights and recommendations
            insights, recommendations = self._extract_insights_and_recommendations(
                response, result.get('intermediate_steps', [])
            )
            
            # Identify data sources used
            data_sources = self._identify_data_sources(result.get('intermediate_steps', []))
            
            # Identify tools used
            tools_used = self._identify_tools_used(result.get('intermediate_steps', []))
            
            return AgentResponse(
                success=True,
                response=response,
                confidence=self._calculate_confidence(result),
                tools_used=tools_used,
                execution_time_ms=int(execution_time),
                insights=insights,
                recommendations=recommendations,
                data_sources=data_sources
            )
            
        except Exception as e:
            logger.error(f"Agent query error: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AgentResponse(
                success=False,
                response=f"I encountered an error processing your request: {str(e)}",
                confidence=0.0,
                tools_used=[],
                execution_time_ms=int(execution_time),
                insights=[],
                recommendations=["Please try rephrasing your question or contact support"],
                data_sources=[],
                error=str(e)
            )
    
    def _enhance_input(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance user input with business context"""
        
        enhanced = user_input
        
        if context:
            # Add temporal context
            if 'timeframe' in context:
                enhanced += f" (Timeframe: {context['timeframe']})"
            
            # Add location context
            if 'location' in context:
                enhanced += f" (Focus on {context['location']} area)"
            
            # Add business unit context
            if 'business_unit' in context:
                unit = context['business_unit']
                if unit.lower() in ['a1', 'construction']:
                    enhanced += " (Focus on A1 Rent It construction equipment)"
                elif unit.lower() in ['broadway', 'event', 'tent']:
                    enhanced += " (Focus on Broadway Tent & Event equipment)"
        
        # Add current date context
        current_date = datetime.now().strftime("%B %Y")
        enhanced += f" (Current date: {current_date})"
        
        return enhanced
    
    def _process_agent_response(self, result: Dict[str, Any]) -> str:
        """Process and clean agent response"""
        response = result.get('output', 'No response generated')
        
        # Clean up response formatting
        response = response.strip()
        
        # Ensure response ends properly
        if not response.endswith(('.', '!', '?', ':')):
            response += '.'
        
        return response
    
    def _extract_insights_and_recommendations(
        self,
        response: str,
        intermediate_steps: List[Any]
    ) -> tuple[List[str], List[str]]:
        """Extract key insights and actionable recommendations"""
        
        insights = []
        recommendations = []
        
        # Look for insights in response
        response_lower = response.lower()
        
        # Common insight indicators
        if 'trend' in response_lower or 'pattern' in response_lower:
            insights.append("Trend analysis performed")
        
        if 'correlation' in response_lower or 'relationship' in response_lower:
            insights.append("Data correlation identified")
        
        if 'seasonal' in response_lower:
            insights.append("Seasonal patterns considered")
        
        # Common recommendation indicators  
        if 'recommend' in response_lower or 'suggest' in response_lower:
            recommendations.append("Specific recommendations provided")
        
        if 'increase' in response_lower or 'expand' in response_lower:
            recommendations.append("Growth opportunities identified")
        
        if 'optimize' in response_lower or 'improve' in response_lower:
            recommendations.append("Optimization opportunities found")
        
        # Extract from intermediate steps
        for step in intermediate_steps:
            if len(step) >= 2:
                tool_output = str(step[1])
                if 'recommendation' in tool_output.lower():
                    recommendations.append("Tool-based recommendations available")
                if 'insight' in tool_output.lower():
                    insights.append("Data-driven insights generated")
        
        return insights, recommendations
    
    def _identify_data_sources(self, intermediate_steps: List[Any]) -> List[str]:
        """Identify data sources used in response"""
        sources = []
        
        for step in intermediate_steps:
            if len(step) >= 2:
                tool_name = step[0].tool if hasattr(step[0], 'tool') else 'unknown'
                tool_output = str(step[1])
                
                if 'database' in tool_name.lower():
                    sources.append("Equipment Rental Database")
                elif 'weather' in tool_name.lower():
                    sources.append("Weather Data APIs")
                elif 'events' in tool_name.lower():
                    sources.append("Minnesota Events Data")
                elif 'permits' in tool_name.lower():
                    sources.append("Building Permits Data")
        
        return list(set(sources))  # Remove duplicates
    
    def _identify_tools_used(self, intermediate_steps: List[Any]) -> List[str]:
        """Identify tools used in processing"""
        tools = []
        
        for step in intermediate_steps:
            if len(step) >= 1:
                tool_name = step[0].tool if hasattr(step[0], 'tool') else 'unknown'
                tools.append(tool_name)
        
        return list(set(tools))  # Remove duplicates
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score for response"""
        
        base_confidence = 0.8  # Base confidence for successful execution
        
        # Reduce confidence if no tools were used
        intermediate_steps = result.get('intermediate_steps', [])
        if not intermediate_steps:
            base_confidence -= 0.2
        
        # Increase confidence with more data sources
        num_tools = len(intermediate_steps)
        if num_tools >= 3:
            base_confidence += 0.1
        elif num_tools >= 2:
            base_confidence += 0.05
        
        # Check for error indicators
        output = result.get('output', '').lower()
        if 'error' in output or 'failed' in output or 'unable' in output:
            base_confidence -= 0.3
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, base_confidence))
    
    def get_available_capabilities(self) -> Dict[str, Any]:
        """Get list of agent capabilities"""
        return {
            'tools': [tool.name for tool in self.tools],
            'business_focus': [
                'Equipment rental demand analysis',
                'Financial performance optimization',
                'Weather impact assessment',
                'Event and construction monitoring',
                'Seasonal planning and forecasting'
            ],
            'data_sources': [
                'Equipment inventory database',
                'POS and financial transactions',
                'Minnesota weather data',
                'State and local events',
                'Construction permits'
            ],
            'geographic_coverage': [
                'Twin Cities Metro',
                'Wayzata', 'Brooklyn Park', 'Fridley', 'Elk River'
            ],
            'model_info': {
                'llm_model': self.model_name,
                'host': self.ollama_host,
                'context_window': 8192
            }
        }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Agent memory cleared")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of conversation memory"""
        messages = self.memory.chat_memory.messages
        return {
            'message_count': len(messages),
            'recent_topics': [
                msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                for msg in messages[-5:]  # Last 5 messages
            ]
        }