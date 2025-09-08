"""
FastAPI Endpoints for Minnesota Equipment Rental AI Agent
Provides RESTful API interface for Pi 5 integration
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

from ..core.llm_agent import MinnesotaEquipmentRentalAgent, AgentResponse
from ..services.feedback_service import FeedbackService
from ..services.cache_service import CacheService
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
router = APIRouter(prefix="/api/v1", tags=["ai-agent"])


class QueryRequest(BaseModel):
    """Query request schema"""
    question: str = Field(..., description="Natural language business question")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for the query"
    )
    user_id: Optional[str] = Field(
        default=None, description="User identifier for tracking"
    )
    session_id: Optional[str] = Field(
        default=None, description="Session identifier"
    )
    priority: str = Field(
        default="normal", description="Query priority: low, normal, high"
    )


class QueryResponse(BaseModel):
    """Query response schema"""
    success: bool
    query_id: str
    response: str
    confidence: float
    tools_used: List[str]
    execution_time_ms: int
    insights: List[str]
    recommendations: List[str]
    data_sources: List[str]
    timestamp: str
    error: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Feedback request schema"""
    query_id: str = Field(..., description="ID of the query being rated")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    helpful: bool = Field(..., description="Whether the response was helpful")
    correction: Optional[str] = Field(
        default=None, description="User correction or additional context"
    )
    user_id: Optional[str] = Field(default=None)


class InsightRequest(BaseModel):
    """Real-time insight request"""
    category: str = Field(..., description="Insight category")
    timeframe: str = Field(default="24h", description="Time range for insights")
    filters: Optional[Dict[str, Any]] = Field(default=None)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    model_status: str
    tools_available: List[str]
    uptime_seconds: int


# Global agent instance (will be initialized in main app)
agent: Optional[MinnesotaEquipmentRentalAgent] = None
feedback_service: Optional[FeedbackService] = None
cache_service: Optional[CacheService] = None
audit_service: Optional[AuditService] = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and extract user info"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            options={"verify_signature": False}  # For development
        )
        return payload.get("user_id", "anonymous")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/query", response_model=QueryResponse)
async def query_agent(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """
    Process natural language query with AI agent
    
    Supports business intelligence queries such as:
    - Equipment availability and utilization
    - Financial performance analysis
    - Weather impact on rental demand
    - Event and construction forecasting
    - Seasonal planning recommendations
    """
    if not agent:
        raise HTTPException(status_code=503, detail="AI agent not available")
    
    query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(request):x}"
    
    try:
        # Log query for audit
        if audit_service:
            background_tasks.add_task(
                audit_service.log_query,
                query_id=query_id,
                user_id=user_id,
                question=request.question,
                context=request.context
            )
        
        # Check cache first
        cache_key = None
        if cache_service:
            cache_key = cache_service.generate_cache_key(
                request.question, request.context
            )
            cached_response = await cache_service.get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Serving cached response for query {query_id}")
                return QueryResponse(
                    **cached_response,
                    query_id=query_id,
                    timestamp=datetime.now().isoformat()
                )
        
        # Process query with agent
        agent_response = await agent.query(
            user_input=request.question,
            context=request.context
        )
        
        # Prepare API response
        api_response = QueryResponse(
            success=agent_response.success,
            query_id=query_id,
            response=agent_response.response,
            confidence=agent_response.confidence,
            tools_used=agent_response.tools_used,
            execution_time_ms=agent_response.execution_time_ms,
            insights=agent_response.insights,
            recommendations=agent_response.recommendations,
            data_sources=agent_response.data_sources,
            timestamp=datetime.now().isoformat(),
            error=agent_response.error
        )
        
        # Cache successful responses
        if cache_service and agent_response.success and cache_key:
            background_tasks.add_task(
                cache_service.cache_response,
                cache_key,
                api_response.dict()
            )
        
        # Log successful completion
        if audit_service:
            background_tasks.add_task(
                audit_service.log_completion,
                query_id=query_id,
                success=agent_response.success,
                confidence=agent_response.confidence,
                tools_used=agent_response.tools_used
            )
        
        return api_response
        
    except Exception as e:
        logger.error(f"Query processing error for {query_id}: {e}", exc_info=True)
        
        # Log error
        if audit_service:
            background_tasks.add_task(
                audit_service.log_error,
                query_id=query_id,
                error=str(e)
            )
        
        return QueryResponse(
            success=False,
            query_id=query_id,
            response=f"I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
            confidence=0.0,
            tools_used=[],
            execution_time_ms=0,
            insights=[],
            recommendations=["Please try rephrasing your question"],
            data_sources=[],
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Submit feedback for query response to improve agent performance"""
    
    if not feedback_service:
        raise HTTPException(status_code=503, detail="Feedback service not available")
    
    try:
        # Process feedback
        feedback_id = await feedback_service.submit_feedback(
            query_id=request.query_id,
            user_id=user_id,
            rating=request.rating,
            helpful=request.helpful,
            correction=request.correction
        )
        
        # Log feedback for audit
        if audit_service:
            background_tasks.add_task(
                audit_service.log_feedback,
                feedback_id=feedback_id,
                query_id=request.query_id,
                rating=request.rating
            )
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback! It helps improve our AI agent.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/insights/live")
async def get_live_insights(
    category: str = "general",
    timeframe: str = "24h",
    user_id: str = Depends(get_current_user)
):
    """Get real-time business insights and alerts"""
    
    if not agent:
        raise HTTPException(status_code=503, detail="AI agent not available")
    
    try:
        # Generate insights based on category
        insights_query = f"Provide live business insights for {category} over the past {timeframe}"
        
        agent_response = await agent.query(
            user_input=insights_query,
            context={"category": category, "timeframe": timeframe}
        )
        
        return {
            "success": True,
            "category": category,
            "timeframe": timeframe,
            "insights": agent_response.insights,
            "recommendations": agent_response.recommendations,
            "confidence": agent_response.confidence,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Live insights error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights")


@router.get("/capabilities")
async def get_capabilities():
    """Get AI agent capabilities and available tools"""
    
    if not agent:
        return {
            "status": "unavailable",
            "message": "AI agent is not currently available"
        }
    
    try:
        capabilities = agent.get_available_capabilities()
        return {
            "success": True,
            "capabilities": capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Capabilities query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get capabilities")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    
    try:
        # Check agent status
        agent_status = "healthy" if agent else "unavailable"
        
        # Check model connectivity
        model_status = "unknown"
        if agent:
            try:
                # Quick test query
                test_response = await agent.query("test", context={"test": True})
                model_status = "healthy" if test_response.success else "degraded"
            except:
                model_status = "unhealthy"
        
        # Get available tools
        tools_available = []
        if agent:
            tools_available = [tool.name for tool in agent.tools]
        
        return HealthResponse(
            status=agent_status,
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            model_status=model_status,
            tools_available=tools_available,
            uptime_seconds=0  # Would track actual uptime
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return HealthResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            version="1.0.0", 
            model_status="error",
            tools_available=[],
            uptime_seconds=0
        )


@router.post("/memory/clear")
async def clear_memory(user_id: str = Depends(get_current_user)):
    """Clear agent conversation memory"""
    
    if not agent:
        raise HTTPException(status_code=503, detail="AI agent not available")
    
    try:
        agent.clear_memory()
        
        if audit_service:
            await audit_service.log_memory_clear(user_id=user_id)
        
        return {
            "success": True,
            "message": "Agent memory cleared",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Memory clear error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to clear memory")


@router.get("/memory/summary")
async def get_memory_summary(user_id: str = Depends(get_current_user)):
    """Get summary of agent memory"""
    
    if not agent:
        raise HTTPException(status_code=503, detail="AI agent not available")
    
    try:
        memory_summary = agent.get_memory_summary()
        return {
            "success": True,
            "memory_summary": memory_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Memory summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get memory summary")


@router.get("/analytics/performance")
async def get_performance_analytics(
    timeframe: str = "7d",
    user_id: str = Depends(get_current_user)
):
    """Get agent performance analytics"""
    
    if not audit_service:
        raise HTTPException(status_code=503, detail="Analytics not available")
    
    try:
        analytics = await audit_service.get_performance_analytics(timeframe)
        return {
            "success": True,
            "timeframe": timeframe,
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance analytics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get analytics")


# Initialize services (called from main app)
def initialize_services(
    agent_instance: MinnesotaEquipmentRentalAgent,
    feedback_service_instance: FeedbackService = None,
    cache_service_instance: CacheService = None,
    audit_service_instance: AuditService = None
):
    """Initialize global services"""
    global agent, feedback_service, cache_service, audit_service
    
    agent = agent_instance
    feedback_service = feedback_service_instance
    cache_service = cache_service_instance
    audit_service = audit_service_instance
    
    logger.info("API endpoints initialized with services")