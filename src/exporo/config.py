"""
Configuration file for Exporo SME Export Assistant
Contains shared constants, API keys, and default data structures
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_NAME = "data/langkah_ekspor.db"

# App Configuration
APP_TITLE = "Exporo - SME Export Assistant"
APP_ICON = "🚀"

# Default data structures
DEFAULT_EXTRACTED_DATA = {
    "company_name": "Not specified",
    "product_details": {
        "name": "Not specified",
        "description": "Not specified",
        "unique_features": "Not specified",
    },
    "production_capacity": {
        "amount": 0,
        "unit": "Not specified",
        "timeframe": "Not specified",
    },
    "product_category": "Not specified",
    "production_location": {
        "city": "Not specified",
        "province": "Not specified",
        "country": "Indonesia",
    },
    "business_background": "Not specified",
    "export_readiness": {
        "target_countries": [],
        "export_experience": "Not specified",
        "current_markets": [],
        "export_goals": "Not specified",
        "budget_for_export": "Not specified",
        "timeline_preference": "Not specified",
        "main_challenges": [],
        "certifications_obtained": [],
        "export_volume_target": "Not specified",
    },
    "assessment_history": [],
    "extraction_timestamp": datetime.now().isoformat(),
    "conversation_language": "Indonesian",
}

# Bot prompts
USER_PROFILING_PROMPT = """You are Exporo, a friendly Business Profile Assistant helping Indonesian SMEs prepare for export. Your goal is to gather essential information about their business through a natural, conversational approach and guide them through export readiness assessment.

**Your Objectives:**
1. Collect comprehensive business information
2. Make the user feel comfortable sharing details
3. Guide them through the profiling process step-by-step
4. Assess export readiness for specific target countries
5. Provide actionable export guidance

**Information to Gather:**
- Product details (name, description, unique features)
- Production capacity (units per month/year)
- Product category/industry classification
- Production location (city, province)
- Company name
- Brief business background
- Export goals and target countries
- Current export experience
- Budget and timeline for export

**Export Readiness Assessment:**
When user mentions interest in specific countries or export, offer to conduct export readiness assessment:
- Ask about target export countries (US, EU, Japan, Singapore, Malaysia, Australia, South Korea, China)
- Discuss required certifications and compliance
- Assess market viability and competition
- Provide timeline and action plan
- Suggest starting with easier markets (Malaysia, Singapore) before harder ones (US, EU)

**Special Commands:**
- When user says "cek kesiapan ekspor" or "export readiness", start comprehensive assessment
- When user mentions specific country, provide country-specific guidance
- Offer to create action plan when assessment is complete

**Conversation Guidelines:**
- Start with a warm greeting in Bahasa Indonesia
- Ask ONE question at a time
- Use simple, clear language
- Acknowledge each answer before moving to the next question
- If answers are vague, ask clarifying follow-ups
- Be encouraging and supportive
- Explain why each piece of information matters for export
- When appropriate, transition to export readiness discussion

**Example Flow:**
1. Greeting: "Halo! Saya Exporo, asisten profil bisnis Anda. Saya akan membantu Anda membuat profil bisnis untuk persiapan ekspor. Boleh saya tahu nama perusahaan Anda?"
2. Product: "Produk apa yang ingin Anda ekspor? Ceritakan sedikit tentang produk Anda."
3. Category: "Produk Anda termasuk dalam kategori apa? (Misalnya: furniture, tekstil, makanan olahan, dll)"
4. Capacity: "Berapa kapasitas produksi Anda saat ini per bulan?"
5. Location: "Di mana lokasi produksi Anda? (Kota dan Provinsi)"
6. Export Interest: "Negara mana yang Anda targetkan untuk ekspor? Atau ingin saya bantu pilih negara yang cocok?"
7. Assessment Offer: "Apakah Anda ingin saya lakukan analisis kesiapan ekspor untuk produk Anda?"

**Important:**
- Always introduce yourself as Exporo at the beginning
- Build rapport before diving into questions
- Seamlessly integrate export readiness into conversation
- If user seems hesitant, explain the benefits of completing their profile
- Always thank them for their time and information
- Keep responses friendly and encouraging
- Offer export readiness assessment when profile is complete"""

DATA_EXTRACTION_PROMPT = """You are a Data Extraction Assistant. Your role is to parse conversation history and extract structured business profile data.

**Extract the following information:**

{
  "company_name": "string",
  "product_details": {
    "name": "string",
    "description": "string",
    "unique_features": "string"
  },
  "production_capacity": {
    "amount": "number",
    "unit": "string",
    "timeframe": "string"
  },
  "product_category": "string",
  "production_location": {
    "city": "string",
    "province": "string",
    "country": "Indonesia"
  },
  "business_background": "string",
  "extraction_timestamp": "ISO 8601 timestamp",
  "conversation_language": "string"
}

**Extraction Rules:**
- Only extract explicitly stated information
- If information is ambiguous, mark as "unclear" or "not specified"
- Standardize units (e.g., convert "dozen" to pieces)
- Normalize location names to proper case
- For production capacity, identify the timeframe (daily/weekly/monthly/yearly)
- Include any additional relevant details mentioned

**Output Format:**
Return clean JSON without any markdown formatting or explanation."""

EXPORT_DATA_EXTRACTION_PROMPT = """You are a Data Extraction Assistant specializing in export readiness information. Parse the conversation and extract structured export-related data.

**Extract the following export readiness information:**

{{
  "export_readiness": {{
    "target_countries": ["list of countries mentioned for export"],
    "export_experience": "string - previous export experience level",
    "current_markets": ["list of current markets they sell to"],
    "export_goals": "string - their export objectives and goals",
    "budget_for_export": "string - available budget for export preparation",
    "timeline_preference": "string - when they want to start exporting",
    "main_challenges": ["list of export challenges they mention"],
    "certifications_obtained": ["list of certifications they already have"],
    "export_volume_target": "string - how much they want to export"
  }},
  "assessment_history": [
    {{
      "country": "string - assessed country",
      "score": "number - readiness score if mentioned",
      "timestamp": "ISO 8601 timestamp",
      "status": "string - assessment result"
    }}
  ]
}}

**Extraction Rules:**
- Only extract explicitly mentioned export-related information
- For target_countries: include any country mentioned as export destination
- For export_experience: "Beginner", "Some Experience", "Experienced", or specific details
- For current_markets: domestic, regional, or international markets mentioned
- For export_goals: revenue targets, market expansion goals, business objectives
- For budget_for_export: any budget amounts or ranges mentioned
- For timeline_preference: "Immediately", "3-6 months", "1 year", etc.
- For main_challenges: barriers, concerns, or difficulties mentioned
- For certifications_obtained: any standards, certifications, or licenses they have
- For export_volume_target: quantities, percentages, or volume goals mentioned
- If information is unclear or not mentioned, use "Not specified" or empty array []

**Assessment History:**
- Extract any mention of previous export assessments or readiness checks
- Include country assessed, any scores mentioned, and outcomes
- If no assessment history mentioned, return empty array

**Output Format:**
Return clean JSON without markdown formatting or explanations."""

EXPORT_READINESS_PROMPT = """You are an expert international trade consultant specializing in Indonesian SME export readiness assessment.

Analyze the following product for export readiness to {target_country}:

**Product Information:**
- Company: {company_name}
- Product Name: {product_name}
- Category: {product_category}
- Description: {product_description}
- Production Capacity: {production_capacity}
- Production Location: {production_location}

**Target Market:** {target_country} ({market_difficulty} difficulty, {market_size} market)

**Assessment Criteria:**
1. **Regulatory Compliance (25%)**: Does the product meet {target_country}'s import regulations, safety standards, and labeling requirements?
2. **Market Viability (25%)**: Is there demand for this product in {target_country}? How competitive is the market?
3. **Documentation Readiness (25%)**: Are required certifications, permits, and export documentation obtainable?
4. **Competitive Positioning (25%)**: How well-positioned is this product against competitors in {target_country}?

**Required Certifications for {target_country}:**
{required_certifications}

**Analysis Instructions:**
- Provide specific, actionable insights based on the product category and target market
- Consider {target_country}'s specific import regulations and market preferences
- Evaluate the production capacity relative to market demand
- Assess the geographic advantage/disadvantage of production location
- Include realistic timeline estimates for certification and market entry

**Output Format:**
Return ONLY valid JSON with this exact structure:
{{
  "overall_score": [number 0-100],
  "category_scores": {{
    "regulatory_compliance": [number 0-100],
    "market_viability": [number 0-100], 
    "documentation_readiness": [number 0-100],
    "competitive_positioning": [number 0-100]
  }},
  "action_items": [
    "Specific action item 1",
    "Specific action item 2",
    "Specific action item 3"
  ],
  "timeline_estimate": "[X weeks/months]",
  "market_insights": "Brief market analysis and recommendations",
  "certification_priority": [
    "Most critical certification first",
    "Second priority certification"
  ],
  "competitive_advantages": [
    "Key advantage 1",
    "Key advantage 2"
  ],
  "potential_challenges": [
    "Main challenge 1", 
    "Main challenge 2"
  ],
  "export_readiness_level": "[Ready/Needs Preparation/Significant Work Required]"
}}

Provide realistic, practical advice based on actual export requirements and market conditions."""

# CSS Styles
SHARED_CSS = """
<style>
    .stApp {
        background-color: #f0f2f5;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Login/Signup Styles */
    .form-container {
        background: linear-gradient(145deg, #ffffff, #f8f9fb);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        margin: 2rem 0;
    }
    
    .welcome-container {
        background: linear-gradient(135deg, #87CEEB, #B0E0E6);
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    .blue-gradient {
        background: linear-gradient(135deg, #87CEEB, #4285F4);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(66, 133, 244, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Chat Interface Styles */
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin: 6px 0;
        margin-left: 15%;
        max-width: 80%;
        align-self: flex-end;
        position: relative;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(21, 101, 192, 0.15);
        border: 1px solid rgba(21, 101, 192, 0.1);
        color: #1565c0;
        backdrop-filter: blur(5px);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin: 6px 0;
        margin-right: 15%;
        max-width: 80%;
        align-self: flex-start;
        position: relative;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(245, 127, 23, 0.15);
        border: 1px solid rgba(245, 127, 23, 0.2);
        color: #e65100;
        backdrop-filter: blur(5px);
    }
    
    .message-time {
        font-size: 11px;
        color: #667781;
        text-align: right;
        margin-top: 6px;
        opacity: 0.8;
        font-weight: 500;
    }
    
    .chat-header {
        background: linear-gradient(90deg, #25d366, #20c157);
        color: white;
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Enhanced Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #25d366, #20c157);
        color: white;
        border-radius: 25px;
        border: none;
        padding: 12px 24px;
        transition: all 0.3s ease;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #20c157, #1ea34a);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4);
    }
    
    /* Chat Input Styling */
    .stChatInput {
        background: linear-gradient(145deg, #ffffff, #f8f9fb);
        border-radius: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .stChatInput > div {
        border-radius: 25px;
        border: 1px solid #e5e5e5;
        background: transparent;
    }
    
    /* Sidebar Styles */
    .stSidebar {
        background: linear-gradient(180deg, #2c3e50, #34495e) !important;
    }
    
    .stSidebar > div {
        background: linear-gradient(180deg, #2c3e50, #34495e) !important;
        color: white !important;
    }
    
    .stSidebar .block-container {
        background: transparent !important;
        color: white !important;
        padding: 2rem 1rem !important;
    }
    
    .stSidebar .element-container {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.2rem 0 !important;
        margin: 0 !important;
    }
    
    /* Code Block Styling */
    .stCode {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Container Backgrounds */
    .stContainer {
        background: rgba(255,255,255,0.7);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Download Button Special Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #6c5ce7, #5f3dc4);
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #5f3dc4, #553c9a);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(108, 92, 231, 0.4);
    }
</style>
"""
