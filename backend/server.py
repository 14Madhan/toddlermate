from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class HospitalSearchRequest(BaseModel):
    location: str

class Hospital(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    phone: Optional[str] = None
    type: str = "Pediatric Hospital"
    distance: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Development Milestones Data
MILESTONES_DATA = {
    "0-6_months": {
        "title": "0-6 Months",
        "milestones": [
            "Follows objects with eyes",
            "Responds to loud sounds",
            "Smiles at people",
            "Holds head steady when upright",
            "Brings hands to mouth",
            "Pushes up when lying on tummy"
        ]
    },
    "6-12_months": {
        "title": "6-12 Months", 
        "milestones": [
            "Sits without support",
            "Crawls or scoots",
            "Pulls to stand",
            "Says 'mama' and 'dada'",
            "Plays peek-a-boo",
            "Uses pincer grasp"
        ]
    },
    "1-2_years": {
        "title": "1-2 Years",
        "milestones": [
            "Walks independently",
            "Says 2-3 words clearly",
            "Points to things when named",
            "Follows simple instructions",
            "Drinks from a cup",
            "Shows affection to familiar people"
        ]
    },
    "2-3_years": {
        "title": "2-3 Years",
        "milestones": [
            "Runs and jumps",
            "Uses 2-word phrases",
            "Sorts objects by shape and color",
            "Shows independence",
            "Plays alongside other children",
            "Uses toilet with help"
        ]
    }
}

# Health Symptoms Data with Indian Cultural Remedies
SYMPTOMS_DATA = {
    "fever": {
        "title": "Fever & High Temperature",
        "description": "When your child feels warm and restless",
        "home_remedies": [
            "Give honey mixed with warm water (for children over 1 year)",
            "Apply cold compress with damp cloth on forehead",
            "Offer plenty of fluids like coconut water or ORS",
            "Use tulsi (holy basil) leaves boiled in water as tea",
            "Light cotton clothing and keep room well-ventilated",
            "Gentle massage with lukewarm mustard oil on chest and back"
        ],
        "when_to_see_doctor": "If fever persists over 3 days, reaches 104°F, or child shows signs of dehydration"
    },
    "cough": {
        "title": "Persistent Cough",
        "description": "Dry or wet cough that concerns you",
        "home_remedies": [
            "Honey with warm water or milk (for children over 1 year)",
            "Steam inhalation with eucalyptus oil or ajwain (carom seeds)",
            "Ginger juice with honey (small amounts for older toddlers)",
            "Turmeric powder in warm milk before bedtime",
            "Warm mustard oil massage on chest and back",
            "Keep child hydrated with warm fluids and soups"
        ],
        "when_to_see_doctor": "If cough persists over 2 weeks, difficulty breathing, or coughing up blood"
    },
    "stomach": {
        "title": "Stomach Issues",
        "description": "Vomiting, diarrhea, or tummy troubles",
        "home_remedies": [
            "ORS (Oral Rehydration Solution) or homemade salt-sugar water",
            "Rice water or thin khichdi for easy digestion",
            "Banana and yogurt for probiotics and potassium",
            "Jeera (cumin) water boiled and cooled",
            "Ginger tea with honey for nausea (older toddlers)",
            "Avoid dairy temporarily, focus on BRAT diet (banana, rice, apple, toast)"
        ],
        "when_to_see_doctor": "If symptoms persist over 24 hours, signs of dehydration, or severe pain"
    },
    "sleep": {
        "title": "Sleep Problems",
        "description": "Difficulty falling or staying asleep",
        "home_remedies": [
            "Warm oil massage with coconut or mustard oil before bedtime",
            "Warm milk with a pinch of turmeric and nutmeg",
            "Create consistent bedtime routine with soft devotional music",
            "Gentle head massage with warm oil",
            "Keep room cool and comfortable, use cotton clothing",
            "Avoid screen time 1 hour before sleep, dim lights in evening"
        ],
        "when_to_see_doctor": "If sleep problems persist for weeks or affect daily functioning"
    }
}

# Sample Hospital Data (simplified version)
SAMPLE_HOSPITALS = [
    {
        "name": "Children's Hospital of Philadelphia",
        "address": "3401 Civic Center Blvd, Philadelphia, PA 19104",
        "phone": "(215) 590-1000",
        "type": "Pediatric Hospital",
        "distance": "2.3 miles"
    },
    {
        "name": "Boston Children's Hospital",
        "address": "300 Longwood Ave, Boston, MA 02115",
        "phone": "(617) 355-6000",
        "type": "Pediatric Hospital", 
        "distance": "1.8 miles"
    },
    {
        "name": "Cincinnati Children's Hospital",
        "address": "3333 Burnet Ave, Cincinnati, OH 45229",
        "phone": "(513) 636-4200",
        "type": "Pediatric Hospital",
        "distance": "3.1 miles"
    },
    {
        "name": "Texas Children's Hospital",
        "address": "6621 Fannin St, Houston, TX 77030",
        "phone": "(832) 824-1000",
        "type": "Pediatric Hospital",
        "distance": "4.2 miles"
    }
]

# Helper function to prepare data for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

# API Routes
@api_router.get("/")
async def root():
    return {"message": "ToddlerMate API - Your Parenting Companion"}

@api_router.get("/milestones")
async def get_milestones():
    return MILESTONES_DATA

@api_router.get("/symptoms")
async def get_symptoms():
    return SYMPTOMS_DATA

@api_router.post("/hospitals", response_model=List[Hospital])
async def search_hospitals(request: HospitalSearchRequest):
    # Simple hospital search - returns sample data
    # In a real implementation, this would integrate with Google Places API
    hospitals = []
    for hospital_data in SAMPLE_HOSPITALS:
        hospital = Hospital(
            id=str(uuid.uuid4()),
            name=hospital_data["name"],
            address=hospital_data["address"],
            phone=hospital_data.get("phone"),
            type=hospital_data["type"],
            distance=hospital_data.get("distance")
        )
        hospitals.append(hospital)
    
    return hospitals

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize Gemini chat
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=session_id,
            system_message="You are a helpful and caring pediatric health assistant specializing in toddler care and development. Provide helpful, accurate information about child health, development milestones, and parenting advice. Always recommend consulting healthcare professionals for serious concerns. Keep responses warm, supportive, and easy to understand for parents."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Get response from Gemini
        response = await chat.send_message(user_message)
        
        # Save chat to database
        chat_record = ChatMessage(
            session_id=session_id,
            message=request.message,
            response=response
        )
        
        chat_dict = prepare_for_mongo(chat_record.dict())
        await db.chat_history.insert_one(chat_dict)
        
        return ChatResponse(response=response, session_id=session_id)
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        chat_history = await db.chat_history.find({"session_id": session_id}).to_list(100)
        return chat_history
    except Exception as e:
        logging.error(f"Failed to retrieve chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    status_dict = prepare_for_mongo(status_obj.dict())
    await db.status_checks.insert_one(status_dict)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

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