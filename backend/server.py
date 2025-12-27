from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

# Import agent service: support running from project root (package) or from backend/ (local package)
try:
    from services.agent_service import AgentService
except ModuleNotFoundError:
    # When running as `python -m uvicorn backend.server:app` the package is `backend`
    from backend.services.agent_service import AgentService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Shopify AI Analytics API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize Agent Service
agent_service = AgentService()

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class QuestionRequest(BaseModel):
    """Request model for analytics questions"""
    store_id: str = Field(..., description="Shopify store ID (e.g., example-store.myshopify.com)")
    question: str = Field(..., description="Natural language question about store analytics")

class QuestionResponse(BaseModel):
    """Response model for analytics answers"""
    answer: str
    confidence: str
    recommendation: Optional[str] = None
    metadata: dict

class QuestionLog(BaseModel):
    """Model for storing question history"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_id: str
    question: str
    answer: str
    confidence: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Shopify AI Analytics API", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Main Analytics Endpoint
@api_router.post("/v1/questions", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a natural language question about your Shopify store.
    
    Examples:
    - "How many units of Product X will I need next month?"
    - "Which products are likely to go out of stock in 7 days?"
    - "What were my top 5 selling products last week?"
    - "How much inventory should I reorder based on last 30 days sales?"
    - "Which customers placed repeat orders in the last 90 days?"
    """
    try:
        # Process question through AI agent
        response = await agent_service.process_question(
            store_id=request.store_id,
            question=request.question
        )
        
        # Log the question and response
        log_entry = QuestionLog(
            store_id=request.store_id,
            question=request.question,
            answer=response['answer'],
            confidence=response['confidence'],
            metadata=response.get('metadata', {})
        )
        
        # Store in database
        log_dict = log_entry.model_dump()
        log_dict['timestamp'] = log_dict['timestamp'].isoformat()
        await db.question_logs.insert_one(log_dict)
        
        return QuestionResponse(**response)
        
    except Exception as e:
        logging.error(f"Error in ask_question endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/v1/questions/history")
async def get_question_history(store_id: Optional[str] = None, limit: int = 50):
    """
    Get history of questions asked (optionally filtered by store_id)
    """
    try:
        query = {"store_id": store_id} if store_id else {}
        history = await db.question_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
        
        # Convert timestamps
        for entry in history:
            if isinstance(entry.get('timestamp'), str):
                entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
        
        return {"history": history, "count": len(history)}
    except Exception as e:
        logging.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/v1/example-questions")
async def get_example_questions():
    """Get example questions users can ask"""
    return {
        "examples": [
            {
                "category": "Inventory Management",
                "questions": [
                    "How many units of Product X will I need next month?",
                    "Which products are likely to go out of stock in 7 days?",
                    "Show me products with low inventory levels",
                    "How much inventory should I reorder based on last 30 days sales?"
                ]
            },
            {
                "category": "Sales Analytics",
                "questions": [
                    "What were my top 5 selling products last week?",
                    "What was my total revenue in the last 30 days?",
                    "Which products generated the most revenue this month?",
                    "Show me sales trends for the past week"
                ]
            },
            {
                "category": "Customer Insights",
                "questions": [
                    "Which customers placed repeat orders in the last 90 days?",
                    "Who are my top spending customers?",
                    "How many repeat customers do I have?"
                ]
            }
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
