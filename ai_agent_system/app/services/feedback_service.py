"""
Feedback Service for AI Agent Continuous Learning
Collects user feedback and implements learning mechanisms
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass, asdict
import sqlite3
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Feedback:
    """Feedback data structure"""
    feedback_id: str
    query_id: str
    user_id: str
    rating: int  # 1-5 scale
    helpful: bool
    correction: Optional[str]
    timestamp: datetime
    processed: bool = False


@dataclass
class LearningInsight:
    """Learning insight from feedback analysis"""
    insight_type: str
    description: str
    confidence: float
    examples: List[str]
    recommendation: str


class FeedbackService:
    """
    Service for collecting and processing user feedback to improve AI agent performance
    
    Features:
    - Feedback collection and storage
    - Pattern analysis and insight generation
    - Model performance tracking
    - Continuous improvement recommendations
    """
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.performance_metrics = {
            'total_queries': 0,
            'positive_feedback_rate': 0.0,
            'average_rating': 0.0,
            'improvement_rate': 0.0
        }
        
        # Learning patterns
        self.learning_patterns = {
            'common_failures': [],
            'successful_patterns': [],
            'user_corrections': [],
            'topic_performance': {}
        }
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize SQLite database for feedback storage"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Feedback table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        query_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                        helpful BOOLEAN NOT NULL,
                        correction TEXT,
                        timestamp DATETIME NOT NULL,
                        processed BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Query performance table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS query_performance (
                        query_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        question TEXT NOT NULL,
                        response TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        tools_used TEXT,  -- JSON array
                        execution_time_ms INTEGER,
                        success BOOLEAN,
                        timestamp DATETIME NOT NULL
                    )
                """)
                
                # Learning insights table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS learning_insights (
                        insight_id TEXT PRIMARY KEY,
                        insight_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        examples TEXT,  -- JSON array
                        recommendation TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        applied BOOLEAN DEFAULT FALSE
                    )
                """)
                
                await db.commit()
                logger.info("Feedback database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize feedback database: {e}")
    
    async def submit_feedback(
        self,
        query_id: str,
        user_id: str,
        rating: int,
        helpful: bool,
        correction: Optional[str] = None
    ) -> str:
        """Submit user feedback for a query"""
        
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(query_id):x}"
        
        feedback = Feedback(
            feedback_id=feedback_id,
            query_id=query_id,
            user_id=user_id,
            rating=rating,
            helpful=helpful,
            correction=correction,
            timestamp=datetime.now()
        )
        
        try:
            # Store feedback
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO feedback 
                    (feedback_id, query_id, user_id, rating, helpful, correction, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback.feedback_id,
                    feedback.query_id,
                    feedback.user_id,
                    feedback.rating,
                    feedback.helpful,
                    feedback.correction,
                    feedback.timestamp
                ))
                await db.commit()
            
            # Update performance metrics
            await self._update_performance_metrics()
            
            # Trigger learning analysis if enough feedback collected
            await self._trigger_learning_analysis()
            
            logger.info(f"Feedback submitted: {feedback_id} for query {query_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            raise
    
    async def log_query_performance(
        self,
        query_id: str,
        user_id: str,
        question: str,
        response: str,
        confidence: float,
        tools_used: List[str],
        execution_time_ms: int,
        success: bool
    ):
        """Log query performance for analysis"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO query_performance 
                    (query_id, user_id, question, response, confidence, tools_used, 
                     execution_time_ms, success, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    query_id,
                    user_id,
                    question,
                    response,
                    confidence,
                    json.dumps(tools_used),
                    execution_time_ms,
                    success,
                    datetime.now()
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to log query performance: {e}")
    
    async def _update_performance_metrics(self):
        """Update overall performance metrics"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get feedback statistics
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_feedback,
                        AVG(rating) as avg_rating,
                        SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                        SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_count
                    FROM feedback
                    WHERE timestamp >= datetime('now', '-30 days')
                """)
                
                row = await cursor.fetchone()
                
                if row and row[0] > 0:
                    total_feedback = row[0]
                    self.performance_metrics['average_rating'] = round(row[1] or 0, 2)
                    self.performance_metrics['positive_feedback_rate'] = round(
                        (row[3] or 0) / total_feedback * 100, 1
                    )
                
                # Get query success rate
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_queries
                    FROM query_performance
                    WHERE timestamp >= datetime('now', '-30 days')
                """)
                
                row = await cursor.fetchone()
                
                if row and row[0] > 0:
                    self.performance_metrics['total_queries'] = row[0]
                    success_rate = (row[1] or 0) / row[0] * 100
                    # Calculate improvement rate (simplified)
                    self.performance_metrics['improvement_rate'] = round(success_rate, 1)
                
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")
    
    async def _trigger_learning_analysis(self):
        """Trigger learning analysis when enough feedback is collected"""
        
        try:
            # Check if we have enough recent feedback to analyze
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM feedback 
                    WHERE timestamp >= datetime('now', '-7 days') AND processed = FALSE
                """)
                unprocessed_count = (await cursor.fetchone())[0]
                
                if unprocessed_count >= 10:  # Threshold for analysis
                    await self._analyze_feedback_patterns()
                    
        except Exception as e:
            logger.error(f"Failed to trigger learning analysis: {e}")
    
    async def _analyze_feedback_patterns(self):
        """Analyze feedback patterns to generate learning insights"""
        
        try:
            insights = []
            
            # Analyze low-rated queries
            low_rated_insights = await self._analyze_low_rated_queries()
            insights.extend(low_rated_insights)
            
            # Analyze user corrections
            correction_insights = await self._analyze_user_corrections()
            insights.extend(correction_insights)
            
            # Analyze tool performance
            tool_insights = await self._analyze_tool_performance()
            insights.extend(tool_insights)
            
            # Store insights
            for insight in insights:
                await self._store_learning_insight(insight)
            
            # Mark feedback as processed
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE feedback SET processed = TRUE 
                    WHERE timestamp >= datetime('now', '-7 days')
                """)
                await db.commit()
            
            logger.info(f"Generated {len(insights)} learning insights from feedback analysis")
            
        except Exception as e:
            logger.error(f"Failed to analyze feedback patterns: {e}")
    
    async def _analyze_low_rated_queries(self) -> List[LearningInsight]:
        """Analyze queries with low ratings to identify failure patterns"""
        
        insights = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT qp.question, qp.response, qp.confidence, qp.tools_used, f.rating, f.correction
                    FROM query_performance qp
                    JOIN feedback f ON qp.query_id = f.query_id
                    WHERE f.rating <= 2 AND f.timestamp >= datetime('now', '-7 days')
                    ORDER BY f.timestamp DESC
                    LIMIT 20
                """)
                
                low_rated_queries = await cursor.fetchall()
                
                if low_rated_queries:
                    # Analyze common patterns
                    question_patterns = {}
                    
                    for row in low_rated_queries:
                        question = row[0].lower()
                        
                        # Identify common question types
                        if 'weather' in question:
                            question_patterns['weather'] = question_patterns.get('weather', 0) + 1
                        elif 'financial' in question or 'revenue' in question:
                            question_patterns['financial'] = question_patterns.get('financial', 0) + 1
                        elif 'equipment' in question:
                            question_patterns['equipment'] = question_patterns.get('equipment', 0) + 1
                    
                    # Generate insights for common failure patterns
                    for pattern, count in question_patterns.items():
                        if count >= 3:  # Significant pattern
                            insights.append(LearningInsight(
                                insight_type="low_performance_pattern",
                                description=f"Queries about {pattern} have lower user satisfaction rates",
                                confidence=min(0.9, count / len(low_rated_queries)),
                                examples=[q[0] for q in low_rated_queries if pattern in q[0].lower()][:3],
                                recommendation=f"Improve {pattern}-related query processing and response quality"
                            ))
                
        except Exception as e:
            logger.error(f"Failed to analyze low-rated queries: {e}")
        
        return insights
    
    async def _analyze_user_corrections(self) -> List[LearningInsight]:
        """Analyze user corrections to identify improvement opportunities"""
        
        insights = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT qp.question, qp.response, f.correction
                    FROM query_performance qp
                    JOIN feedback f ON qp.query_id = f.query_id
                    WHERE f.correction IS NOT NULL AND f.correction != ''
                    AND f.timestamp >= datetime('now', '-14 days')
                    LIMIT 50
                """)
                
                corrections = await cursor.fetchall()
                
                if corrections:
                    # Analyze correction patterns
                    correction_themes = {
                        'factual_errors': [],
                        'missing_context': [],
                        'interpretation_errors': []
                    }
                    
                    for question, response, correction in corrections:
                        correction_lower = correction.lower()
                        
                        # Categorize corrections
                        if any(word in correction_lower for word in ['wrong', 'incorrect', 'error', 'false']):
                            correction_themes['factual_errors'].append((question, correction))
                        elif any(word in correction_lower for word in ['missing', 'forgot', 'also', 'additionally']):
                            correction_themes['missing_context'].append((question, correction))
                        else:
                            correction_themes['interpretation_errors'].append((question, correction))
                    
                    # Generate insights for each theme
                    for theme, examples in correction_themes.items():
                        if len(examples) >= 2:
                            insights.append(LearningInsight(
                                insight_type="user_correction_pattern",
                                description=f"Users frequently provide corrections related to {theme.replace('_', ' ')}",
                                confidence=min(0.8, len(examples) / len(corrections)),
                                examples=[ex[1] for ex in examples[:3]],
                                recommendation=f"Focus on improving accuracy and completeness in {theme.replace('_', ' ')}"
                            ))
                
        except Exception as e:
            logger.error(f"Failed to analyze user corrections: {e}")
        
        return insights
    
    async def _analyze_tool_performance(self) -> List[LearningInsight]:
        """Analyze tool usage and performance patterns"""
        
        insights = []
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT qp.tools_used, AVG(f.rating) as avg_rating, COUNT(*) as usage_count
                    FROM query_performance qp
                    JOIN feedback f ON qp.query_id = f.query_id
                    WHERE qp.timestamp >= datetime('now', '-14 days')
                    GROUP BY qp.tools_used
                    HAVING COUNT(*) >= 3
                    ORDER BY avg_rating DESC
                """)
                
                tool_performance = await cursor.fetchall()
                
                if tool_performance:
                    best_tools = []
                    worst_tools = []
                    
                    for tools_used, avg_rating, count in tool_performance:
                        if avg_rating >= 4.0:
                            best_tools.append((tools_used, avg_rating))
                        elif avg_rating <= 2.5:
                            worst_tools.append((tools_used, avg_rating))
                    
                    if best_tools:
                        insights.append(LearningInsight(
                            insight_type="high_performing_tools",
                            description="Certain tool combinations consistently produce high user satisfaction",
                            confidence=0.85,
                            examples=[tools for tools, _ in best_tools[:3]],
                            recommendation="Prioritize and optimize these tool combinations for similar queries"
                        ))
                    
                    if worst_tools:
                        insights.append(LearningInsight(
                            insight_type="low_performing_tools",
                            description="Some tool combinations result in lower user satisfaction",
                            confidence=0.8,
                            examples=[tools for tools, _ in worst_tools[:3]],
                            recommendation="Review and improve these tool combinations or consider alternatives"
                        ))
                
        except Exception as e:
            logger.error(f"Failed to analyze tool performance: {e}")
        
        return insights
    
    async def _store_learning_insight(self, insight: LearningInsight):
        """Store a learning insight in the database"""
        
        try:
            insight_id = f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(insight):x}"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO learning_insights 
                    (insight_id, insight_type, description, confidence, examples, recommendation, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    insight_id,
                    insight.insight_type,
                    insight.description,
                    insight.confidence,
                    json.dumps(insight.examples),
                    insight.recommendation,
                    datetime.now()
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store learning insight: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        await self._update_performance_metrics()
        return self.performance_metrics.copy()
    
    async def get_recent_insights(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent learning insights"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT insight_type, description, confidence, examples, recommendation, created_at, applied
                    FROM learning_insights
                    WHERE created_at >= datetime('now', '-{} days')
                    ORDER BY created_at DESC, confidence DESC
                    LIMIT 20
                """.format(days))
                
                insights = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    insights.append({
                        'insight_type': row[0],
                        'description': row[1],
                        'confidence': row[2],
                        'examples': json.loads(row[3] or '[]'),
                        'recommendation': row[4],
                        'created_at': row[5],
                        'applied': bool(row[6])
                    })
                
                return insights
                
        except Exception as e:
            logger.error(f"Failed to get recent insights: {e}")
            return []
    
    async def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get feedback summary for specified period"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Overall stats
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_feedback,
                        AVG(rating) as avg_rating,
                        SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                        SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_count,
                        COUNT(CASE WHEN correction IS NOT NULL AND correction != '' THEN 1 END) as corrections_count
                    FROM feedback
                    WHERE timestamp >= datetime('now', '-{} days')
                """.format(days))
                
                stats = await cursor.fetchone()
                
                # Rating distribution
                cursor = await db.execute("""
                    SELECT rating, COUNT(*) as count
                    FROM feedback
                    WHERE timestamp >= datetime('now', '-{} days')
                    GROUP BY rating
                    ORDER BY rating
                """.format(days))
                
                rating_distribution = {str(row[0]): row[1] for row in await cursor.fetchall()}
                
                if stats and stats[0] > 0:
                    total_feedback = stats[0]
                    return {
                        'period_days': days,
                        'total_feedback': total_feedback,
                        'average_rating': round(stats[1] or 0, 2),
                        'helpful_percentage': round((stats[2] or 0) / total_feedback * 100, 1),
                        'positive_percentage': round((stats[3] or 0) / total_feedback * 100, 1),
                        'corrections_count': stats[4] or 0,
                        'rating_distribution': rating_distribution
                    }
                else:
                    return {
                        'period_days': days,
                        'total_feedback': 0,
                        'message': 'No feedback data available for this period'
                    }
                
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {'error': str(e)}
    
    async def apply_learning_insight(self, insight_id: str) -> bool:
        """Mark a learning insight as applied"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE learning_insights SET applied = TRUE 
                    WHERE insight_id = ?
                """, (insight_id,))
                await db.commit()
                
                logger.info(f"Marked learning insight {insight_id} as applied")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply learning insight: {e}")
            return False