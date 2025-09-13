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
from comprehensive_hospitals import COMPREHENSIVE_HOSPITALS_DATABASE, BANGALORE_PEDIATRIC_HOSPITALS

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
    type: str = "Hospital"

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Development Milestones Data with Age-Appropriate Indian Children Images
MILESTONES_DATA = {
    "0-6_months": {
        "title": "0-6 Months",
        "image": "https://images.unsplash.com/photo-1630304565858-642d53fa18ff?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHw0fHxpbmRpYW4lMjBiYWJ5fGVufDB8fHZ8MTc1Nzc1NTE1M3ww&ixlib=rb-4.1.0&q=85",
        "milestones": [
            "Follows objects with eyes",
            "Responds to loud sounds",
            "Smiles at people",
            "Holds head steady when upright",
            "Brings hands to mouth",
            "Pushes up when lying on tummy",
            "Makes cooing sounds",
            "Recognizes familiar faces"
        ]
    },
    "6-12_months": {
        "title": "6-12 Months",
        "image": "https://images.unsplash.com/photo-1630304565761-d6f8d5a0facd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwyfHxpbmRpYW4lMjBiYWJ5fGVufDB8fHZ8MTc1Nzc1NTE1M3ww&ixlib=rb-4.1.0&q=85",
        "milestones": [
            "Sits without support",
            "Crawls or scoots",
            "Pulls to stand",
            "Says 'mama' and 'dada'",
            "Plays peek-a-boo",
            "Uses pincer grasp",
            "Responds to own name",
            "Shows stranger anxiety"
        ]
    },
    "1-2_years": {
        "title": "1-2 Years",
        "image": "https://images.unsplash.com/photo-1581841899040-8b5e38bae033?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxpbmRpYW4lMjBiYWJ5fGVufDB8fHZ8MTc1Nzc1NTE1M3ww&ixlib=rb-4.1.0&q=85",
        "milestones": [
            "Walks independently",
            "Says 2-3 words clearly",
            "Points to things when named",
            "Follows simple instructions",
            "Drinks from a cup",
            "Shows affection to familiar people",
            "Builds tower of 2-3 blocks",
            "Imitates actions and words"
        ]
    },
    "2-3_years": {
        "title": "2-3 Years",
        "image": "https://images.unsplash.com/photo-1581841899040-8b5e38bae033?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwzfHxpbmRpYW4lMjBjaGlsZCUwfHx8fDE3NTc3NTY0Mzd8MA&ixlib=rb-4.1.0&q=85",
        "milestones": [
            "Runs and jumps",
            "Uses 2-word phrases",
            "Sorts objects by shape and color",
            "Shows independence",
            "Plays alongside other children",
            "Uses toilet with help",
            "Climbs stairs alternating feet",
            "Shows defiant behavior (normal)"
        ]
    },
    "3-5_years": {
        "title": "3-5 Years",
        "image": "https://images.unsplash.com/photo-1578897367107-2828e351c8a8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxpbmRpYW4lMjBjaGlsZHxlbnwwfHx8fDE3NTc3NTY0Mzd8MA&ixlib=rb-4.1.0&q=85",
        "milestones": [
            "Speaks in complete sentences",
            "Tells stories and asks lots of questions",
            "Counts to 10 or higher",
            "Draws recognizable pictures",
            "Uses scissors and colors within lines",
            "Plays cooperatively with other children",
            "Shows empathy and understands feelings",
            "Follows multi-step instructions",
            "Rides a tricycle or bicycle with training wheels",
            "Shows interest in letters and reading"
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

# Comprehensive Hospital Database by Location (India-focused)
HOSPITALS_DATABASE = {
    "mumbai": [
        {
            "name": "Jaslok Hospital & Research Centre",
            "address": "15, Dr. Deshmukh Marg, Pedder Road, Mumbai, Maharashtra 400026",
            "phone": "+91 22 6657 3333",
            "type": "Multi-specialty Hospital with Pediatric Care",
            "distance": "1.2 km"
        },
        {
            "name": "Kokilaben Dhirubhai Ambani Hospital",
            "address": "Rao Saheb, Achutrao Patwardhan Marg, Four Bunglows, Andheri West, Mumbai 400053",
            "phone": "+91 22 4269 6969",
            "type": "Super Specialty Hospital",
            "distance": "2.8 km"
        },
        {
            "name": "Rainbow Children's Hospital",
            "address": "Bhakti Vedant Swami Marg, Malad West, Mumbai, Maharashtra 400064",
            "phone": "+91 22 6751 8888",
            "type": "Dedicated Pediatric Hospital",
            "distance": "3.5 km"
        }
    ],
    "delhi": [
        {
            "name": "All India Institute of Medical Sciences (AIIMS)",
            "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
            "phone": "+91 11 2658 8500",
            "type": "Government Medical Institute",
            "distance": "0.8 km"
        },
        {
            "name": "Apollo Hospital",
            "address": "Mathura Road, Sarita Vihar, New Delhi 110076",
            "phone": "+91 11 2692 5858",
            "type": "Multi-specialty Hospital",
            "distance": "2.1 km"
        },
        {
            "name": "Fortis Hospital",
            "address": "B-22, Sector 62, Noida, Uttar Pradesh 201301",
            "phone": "+91 120 247 4444",
            "type": "Super Specialty Hospital",
            "distance": "4.3 km"
        }
    ],
    "bangalore": [
        {
            "name": "Manipal Hospital",
            "address": "98, Rustum Bagh, Airport Road, Bangalore, Karnataka 560017",
            "phone": "+91 80 2502 4444",
            "type": "Multi-specialty Hospital",
            "distance": "1.5 km"
        },
        {
            "name": "Rainbow Children's Hospital",
            "address": "1533, 9th Main, 3rd Block, Jayanagar, Bangalore 560011",
            "phone": "+91 80 4092 4092",
            "type": "Dedicated Pediatric Hospital",
            "distance": "2.2 km"
        },
        {
            "name": "Apollo Hospital",
            "address": "154/11, Bannerghatta Rd, Opposite IIM-B, Bangalore 560076",
            "phone": "+91 80 2630 0300",
            "type": "Super Specialty Hospital",
            "distance": "3.7 km"
        }
    ],
    "hyderabad": [
        {
            "name": "Apollo Hospital",
            "address": "Road No 72, Opp. Bharatiya Vidya Bhavan, Film Nagar, Hyderabad 500033",
            "phone": "+91 40 2335 0000",
            "type": "Super Specialty Hospital",
            "distance": "1.8 km"
        },
        {
            "name": "Rainbow Children's Hospital",
            "address": "Road No 2, Banjara Hills, Hyderabad, Telangana 500034",
            "phone": "+91 40 2420 2020",
            "type": "Dedicated Pediatric Hospital",
            "distance": "2.4 km"
        },
        {
            "name": "Care Hospital",
            "address": "Road No. 1, Banjara Hills, Hyderabad, Telangana 500034",
            "phone": "+91 40 6163 6363",
            "type": "Multi-specialty Hospital",
            "distance": "3.1 km"
        }
    ],
    "chennai": [
        {
            "name": "Apollo Hospital",
            "address": "21, Greams Lane, Off Greams Road, Chennai, Tamil Nadu 600006",
            "phone": "+91 44 2829 3333",
            "type": "Multi-specialty Hospital",
            "distance": "1.3 km"
        },
        {
            "name": "Rainbow Children's Hospital",
            "address": "Vadapalani, Chennai, Tamil Nadu 600026",
            "phone": "+91 44 4289 8989",
            "type": "Dedicated Pediatric Hospital",
            "distance": "2.6 km"
        },
        {
            "name": "Fortis Malar Hospital",
            "address": "52, 1st Main Rd, Gandhi Nagar, Adyar, Chennai 600020",
            "phone": "+91 44 4289 2222",
            "type": "Super Specialty Hospital",
            "distance": "3.9 km"
        }
    ],
    "kolkata": [
        {
            "name": "Apollo Gleneagles Hospital",
            "address": "58, Canal Circular Road, Kadapara, Phool Bagan, Kolkata 700054",
            "phone": "+91 33 2320 3040",
            "type": "Super Specialty Hospital",
            "distance": "1.7 km"
        },
        {
            "name": "Fortis Hospital",
            "address": "730, Anandapur, E M Bypass Rd, Anandapur, Kolkata 700107",
            "phone": "+91 33 6628 4444",
            "type": "Multi-specialty Hospital",
            "distance": "2.9 km"
        },
        {
            "name": "AMRI Hospital",
            "address": "P-4 & 5, CIT Scheme XLVII, Kestopur, Kolkata 700101",
            "phone": "+91 33 6606 3800",
            "type": "Multi-specialty Hospital",
            "distance": "4.2 km"
        }
    ],
    "pune": [
        {
            "name": "Ruby Hall Clinic",
            "address": "40, Sassoon Road, Pune, Maharashtra 411001",
            "phone": "+91 20 2612 1234",
            "type": "Multi-specialty Hospital",
            "distance": "1.4 km"
        },
        {
            "name": "Manipal Hospital",
            "address": "#57/1, Baner Balewadi Road, Pune, Maharashtra 411045",
            "phone": "+91 20 6112 8888",
            "type": "Super Specialty Hospital",
            "distance": "2.8 km"
        },
        {
            "name": "Bharati Vidyapeeth Medical College",
            "address": "Dhankawadi, Pune, Maharashtra 411043",
            "phone": "+91 20 2443 2001",
            "type": "Medical College Hospital",
            "distance": "3.3 km"
        }
    ],
    "ahmedabad": [
        {
            "name": "Apollo Hospital",
            "address": "Plot No 1A, Bhat GIDC Estate, Gandhinagar, Gujarat 382428",
            "phone": "+91 79 2676 7676",
            "type": "Super Specialty Hospital",
            "distance": "2.1 km"
        },
        {
            "name": "Sterling Hospital",
            "address": "Near Gurukul, Memnagar, Ahmedabad, Gujarat 380052",
            "phone": "+91 79 6677 0000",
            "type": "Multi-specialty Hospital",
            "distance": "1.6 km"
        },
        {
            "name": "Zydus Hospital",
            "address": "Nr. Sola Bridge, S.G. Highway, Ahmedabad, Gujarat 380054",
            "phone": "+91 79 6196 0000",
            "type": "Super Specialty Hospital",
            "distance": "3.4 km"
        }
    ],
    "gujarat": [
        {
            "name": "Apollo Hospital",
            "address": "Plot No 1A, Bhat GIDC Estate, Gandhinagar, Gujarat 382428",
            "phone": "+91 79 2676 7676",
            "type": "Super Specialty Hospital",
            "distance": "2.1 km"
        },
        {
            "name": "Sterling Hospital",
            "address": "Near Gurukul, Memnagar, Ahmedabad, Gujarat 380052",
            "phone": "+91 79 6677 0000",
            "type": "Multi-specialty Hospital",
            "distance": "1.6 km"
        },
        {
            "name": "Surat Children's Hospital",
            "address": "Ring Road, Surat, Gujarat 395002",
            "phone": "+91 261 2470000",
            "type": "Pediatric Hospital",
            "distance": "2.8 km"
        }
    ],
    "rajasthan": [
        {
            "name": "Fortis Escorts Hospital",
            "address": "Jawahar Lal Nehru Marg, Malviya Nagar, Jaipur, Rajasthan 302017",
            "phone": "+91 141 2547000",
            "type": "Super Specialty Hospital",
            "distance": "1.9 km"
        },
        {
            "name": "SMS Hospital",
            "address": "JLN Marg, Jaipur, Rajasthan 302004",
            "phone": "+91 141 2518211",
            "type": "Government Hospital",
            "distance": "2.4 km"
        },
        {
            "name": "Manipal Hospital",
            "address": "Sector 5, Vidyadhar Nagar, Jaipur, Rajasthan 302039",
            "phone": "+91 141 3999999",
            "type": "Multi-specialty Hospital",
            "distance": "3.2 km"
        }
    ],
    "uttar_pradesh": [
        {
            "name": "KGMU Hospital",
            "address": "Chowk, Lucknow, Uttar Pradesh 226003",
            "phone": "+91 522 2257450",
            "type": "Government Medical College",
            "distance": "1.5 km"
        },
        {
            "name": "Apollo Hospital",
            "address": "Sector B, Bargawan, LDA Colony, Lucknow 226012",
            "phone": "+91 522 4141414",
            "type": "Super Specialty Hospital",
            "distance": "2.7 km"
        },
        {
            "name": "Sahara Hospital",
            "address": "Viraj Khand, Gomti Nagar, Lucknow 226010",
            "phone": "+91 522 4040404",
            "type": "Multi-specialty Hospital",
            "distance": "3.3 km"
        }
    ],
    "kerala": [
        {
            "name": "Amrita Institute of Medical Sciences",
            "address": "AIMS Ponekkara P O, Kochi, Kerala 682041",
            "phone": "+91 484 2851234",
            "type": "Super Specialty Hospital",
            "distance": "1.8 km"
        },
        {
            "name": "Lisie Hospital",
            "address": "Kaloor, Kochi, Kerala 682017",
            "phone": "+91 484 2403040",
            "type": "Multi-specialty Hospital",
            "distance": "2.5 km"
        },
        {
            "name": "Baby Memorial Hospital",
            "address": "Indira Gandhi Road, Kozhikode, Kerala 673004",
            "phone": "+91 495 2356001",
            "type": "Pediatric Hospital",
            "distance": "1.2 km"
        }
    ]
}

# Function to search hospitals by location using comprehensive database
def search_hospitals_by_location(location: str):
    # Convert location to lowercase for matching
    location_key = location.lower().strip()
    
    # Special handling for Bangalore pediatric hospitals
    if location_key in ["bangalore", "bengaluru"] and "pediatric" in location_key.lower():
        return BANGALORE_PEDIATRIC_HOSPITALS
    
    # Check comprehensive database first
    if location_key in COMPREHENSIVE_HOSPITALS_DATABASE:
        return COMPREHENSIVE_HOSPITALS_DATABASE[location_key]
    
    # Enhanced location matching with more cities and better coverage
    location_mappings = {
        "new delhi": "delhi",
        "navi mumbai": "mumbai", 
        "thane": "mumbai",
        "gurgaon": "delhi",
        "gurugram": "delhi",
        "noida": "delhi",
        "faridabad": "delhi",
        "ghaziabad": "delhi",
        "bengaluru": "bangalore",
        "whitefield": "bangalore",
        "electronic city": "bangalore",
        "koramangala": "bangalore",
        "indiranagar": "bangalore",
        "secunderabad": "hyderabad",
        "cyberabad": "hyderabad",
        "gachibowli": "hyderabad",
        "madras": "chennai",
        "t nagar": "chennai",
        "anna nagar": "chennai",
        "velachery": "chennai",
        "salt lake": "kolkata",
        "howrah": "kolkata",
        "park street": "kolkata",
        "ballygunge": "kolkata",
        "pcmc": "pune",
        "pimpri chinchwad": "pune",
        "kothrud": "pune",
        "gandhinagar": "ahmedabad",
        "vadodara": "gujarat",
        "surat": "gujarat",
        "rajkot": "gujarat",
        "jaipur": "rajasthan",
        "jodhpur": "rajasthan",
        "udaipur": "rajasthan",
        "lucknow": "uttar_pradesh",
        "kanpur": "uttar_pradesh",
        "agra": "uttar_pradesh",
        "varanasi": "uttar_pradesh",
        "indore": "madhya_pradesh",
        "bhopal": "madhya_pradesh",
        "nagpur": "maharashtra",
        "nashik": "maharashtra",
        "aurangabad": "maharashtra",
        "kochi": "kerala",
        "thiruvananthapuram": "kerala",
        "kozhikode": "kerala",
        "bhubaneswar": "odisha",
        "cuttack": "odisha",
        "chandigarh": "punjab",
        "ludhiana": "punjab",
        "amritsar": "punjab",
        "dehradun": "uttarakhand",
        "haridwar": "uttarakhand"
    }
    
    # Check mappings
    for key, mapped_city in location_mappings.items():
        if key in location_key or location_key in key:
            return COMPREHENSIVE_HOSPITALS_DATABASE.get(mapped_city, [])
    
    # If no match found, return a default set
    return [
        {
            "name": f"City Hospital - {location.title()}",
            "address": f"Main Medical District, {location.title()}",
            "phone": "+91 XXX XXX XXXX",
            "type": "General Hospital"
        },
        {
            "name": f"Children's Care Center - {location.title()}",
            "address": f"Healthcare Complex, {location.title()}",
            "phone": "+91 XXX XXX XXXX", 
            "type": "Pediatric Care Center"
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
    # Location-based hospital search using comprehensive Indian hospital database
    hospitals = []
    hospital_data_list = search_hospitals_by_location(request.location)
    
    for hospital_data in hospital_data_list:
        hospital = Hospital(
            id=str(uuid.uuid4()),
            name=hospital_data["name"],
            address=hospital_data["address"],
            phone=hospital_data.get("phone"),
            type=hospital_data["type"]
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