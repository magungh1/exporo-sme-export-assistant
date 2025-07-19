import streamlit as st
import json
from datetime import datetime
from google import genai
from google.genai import types
import uuid
import base64

# Configure page
st.set_page_config(
    page_title="Product Export Assessment",
    page_icon="📦",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {
        "product_assessment": {
            "product_type": "Not specified",
            "product_name": "Not specified",
            "description": "Not specified",
            "dimensions": "Not specified",
            "target_market": "Not specified",
            "product_category": "Not specified"
        },
        "raw_materials": {
            "primary_materials": [],
            "secondary_materials": [],
            "finishing_materials": {
                "type": "Not specified",
                "brand": "Not specified",
                "chemical_compliance": "Not specified"
            }
        },
        "certifications_required": [],
        "compliance_gaps": [],
        "recommendations": [],
        "extraction_timestamp": datetime.now().isoformat()
    }

# Bot prompts
USER_PROFILING_PROMPT = """You are a Product Assessment Specialist focusing on Indonesian product exports. Your role is to analyze products, identify raw materials, and determine certification requirements for various industries.

**Your Objectives:**
1. Assess the user's product in detail
2. Identify all raw materials and components used
3. Determine certification requirements for export
4. Provide clear guidance on compliance needs

**Assessment Areas:**

1. **Product Analysis:**
   - Product type and category
   - Design complexity and features
   - Target market preferences
   - Quality standards and specifications

2. **Raw Material Identification:**
   - Primary materials (wood, metal, textile, plastic, etc.)
   - Secondary components and accessories
   - Finishing materials and treatments
   - Chemical substances and additives

3. **Certification Requirements:**
   - Product-specific certifications (SVLK for wood, SNI for various products)
   - Safety standards (CE marking, FCC, etc.)
   - Environmental certifications (FSC, PEFC, etc.)
   - Industry-specific requirements
   - Phytosanitary/fumigation certificates
   - Target market compliance standards

**Conversation Approach:**
- Start by understanding their specific product
- Ask about each component systematically
- Explain certification requirements clearly
- Provide actionable next steps
- Use examples relevant to their industry

**Key Questions Flow:**
1. "Produk apa yang ingin Anda ekspor? Mohon jelaskan produk Anda secara detail."
2. "Bahan baku utama apa yang digunakan dalam produk ini?"
3. "Apakah Anda sudah mengetahui asal-usul bahan baku tersebut? Dari supplier mana?"
4. "Bahan atau komponen lain apa saja yang digunakan?"
5. "Negara mana yang menjadi target ekspor Anda?"

**Certification Guidance:**
- Explain product-specific mandatory certifications
- Provide market-specific requirements (EU, US, Japan, etc.)
- Estimate timeline for obtaining certificates
- Mention costs when relevant
- Suggest reliable certification bodies

**Important Notes:**
- Be specific about product category regulations
- If they use regulated materials, explain special requirements
- Emphasize sustainable sourcing importance
- Provide alternatives if their current materials face export restrictions
- When analyzing product images, focus on materials, design, and features that affect certification needs"""

DATA_EXTRACTION_PROMPT = """You are a Product Assessment Data Extractor specializing in general product analysis for export. Extract structured data from conversations about products and certification requirements.

**Extract the following information:**

{
  "product_assessment": {
    "product_type": "string",
    "product_name": "string",
    "description": "string",
    "dimensions": "string",
    "target_market": "string",
    "product_category": "string"
  },
  "raw_materials": {
    "primary_materials": [
      {
        "material_type": "string",
        "specific_name": "string",
        "source": "string",
        "sustainability_status": "string"
      }
    ],
    "secondary_materials": [
      {
        "material_type": "string",
        "specific_name": "string",
        "usage": "string"
      }
    ],
    "finishing_materials": {
      "type": "string",
      "brand": "string",
      "chemical_compliance": "string"
    }
  },
  "certifications_required": [
    {
      "certificate_name": "string",
      "requirement_level": "mandatory/recommended/optional",
      "target_market": "string",
      "estimated_time": "string",
      "estimated_cost": "string",
      "certification_body": "string"
    }
  ],
  "compliance_gaps": [
    {
      "gap_type": "string",
      "description": "string",
      "action_required": "string",
      "priority": "high/medium/low"
    }
  ],
  "recommendations": [
    {
      "category": "string",
      "recommendation": "string",
      "rationale": "string"
    }
  ],
  "extraction_timestamp": "ISO 8601 timestamp"
}

**Extraction Guidelines:**
- Identify material types and categorize appropriately (wood, metal, textile, plastic, chemical, etc.)
- Identify all mentioned certifications with their requirements
- Flag any compliance issues or gaps
- Include market-specific requirements
- Extract any cost or timeline estimates mentioned
- Map materials to scientific names when possible

**Special Attention for Different Product Categories:**
- Wood products: SVLK status, wood species legality, CITES requirements
- Textile products: Fiber content, dye compliance, REACH regulations
- Food products: HACCP, halal certification, organic standards
- Electronics: CE marking, FCC compliance, RoHS compliance
- Chemical products: REACH registration, SDS requirements
- General: Target market specific standards (CE marking for EU, etc.)

**Output Format:**
Return clean JSON without any markdown formatting or explanation."""

# Initialize Gemini client
@st.cache_resource
def init_gemini():
    api_key = "AIzaSyBNlRT5T_YkJ8QJBdVm6K54GQ1RqrlFJQ8"
    return genai.Client(api_key=api_key)

def get_bot_response(user_input, conversation_history, uploaded_files=None):
    """Get bot response using Gemini API with furniture assessment prompt"""
    client = init_gemini()
    
    # Prepare conversation content for Gemini
    contents = []
    
    # Add system prompt as first user message
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=USER_PROFILING_PROMPT)]
    ))
    
    # Add a model response acknowledging the system prompt
    contents.append(types.Content(
        role="model", 
        parts=[types.Part.from_text(text="Saya siap membantu sebagai Product Assessment Specialist untuk ekspor produk Indonesia. Saya akan menganalisis produk, bahan baku, dan kebutuhan sertifikasi secara detail.")]
    ))
    
    # Add conversation history
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        parts = []
        
        # Add text part
        if msg.get("content"):
            parts.append(types.Part.from_text(text=msg["content"]))
        
        # Add image parts if present
        if msg.get("images"):
            for image_data in msg["images"]:
                parts.append(types.Part.from_bytes(
                    data=base64.b64decode(image_data["data"]),
                    mime_type=image_data["mime_type"]
                ))
        
        contents.append(types.Content(role=role, parts=parts))
    
    # Add current user input
    user_parts = []
    if user_input:
        user_parts.append(types.Part.from_text(text=user_input))
    
    # Add uploaded images
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Convert to base64 for storage
            image_bytes = uploaded_file.read()
            user_parts.append(types.Part.from_bytes(
                data=image_bytes,
                mime_type=uploaded_file.type
            ))
    
    contents.append(types.Content(role="user", parts=user_parts))
    
    try:
        generate_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            max_output_tokens=500,
            temperature=0.7
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_config
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def extract_data_from_conversation(conversation_history):
    """Extract structured data using Gemini API with furniture assessment extraction prompt from 2 latest messages"""
    client = init_gemini()
    
    # Use only the 2 latest messages
    latest_messages = conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history
    
    # Prepare conversation text
    conversation_text = "\n".join([f"{msg['role']}: {msg.get('content', '')}" for msg in latest_messages])
    
    # Debug: print conversation text
    print(f"Conversation text for extraction: {conversation_text}")
    
    # Prepare contents for Gemini
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=DATA_EXTRACTION_PROMPT)]
        ),
        types.Content(
            role="model", 
            parts=[types.Part.from_text(text="I understand. I will extract structured product assessment data from the conversation and return it as clean JSON.")]
        ),
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Extract data from this conversation:\n\n{conversation_text}")]
        )
    ]
    
    try:
        generate_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=1000,
            temperature=0.1
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_config
        )
        
        # Parse JSON response
        json_text = response.text.strip() if response.text else ""
        # Remove markdown formatting if present
        if json_text.startswith("```json"):
            json_text = json_text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(json_text)
    except Exception as e:
        # Debug: print the error and response
        print(f"Extraction error: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
        print(f"JSON text: {json_text if 'json_text' in locals() else 'No json_text'}")
        
        # Fallback to default structure
        return {
            "product_assessment": {
                "product_type": "Not specified",
                "product_name": "Not specified",
                "description": "Not specified",
                "dimensions": "Not specified",
                "target_market": "Not specified",
                "product_category": "Not specified"
            },
            "raw_materials": {
                "primary_materials": [],
                "secondary_materials": [],
                "finishing_materials": {
                    "type": "Not specified",
                    "brand": "Not specified",
                    "chemical_compliance": "Not specified"
                }
            },
            "certifications_required": [],
            "compliance_gaps": [],
            "recommendations": [],
            "extraction_timestamp": datetime.now().isoformat()
        }

# Main UI
st.title("📦 Product Export Assessment")

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Chat")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Display text content
                if message.get("content"):
                    st.write(message["content"])
                
                # Display images if present
                if message.get("images"):
                    for img in message["images"]:
                        st.image(base64.b64decode(img["data"]), caption="Uploaded Image")
    
    # Chat input with file upload support
    prompt = st.chat_input(
        "Ketik pesan Anda dan/atau upload gambar produk...",
        accept_file=True,
        file_type=["jpg", "jpeg", "png", "webp"]
    )
    
    if prompt:
        # Prepare message data
        message_data = {
            "role": "user",
            "content": prompt.text if prompt.text else "",
            "images": []
        }
        
        # Handle uploaded files
        if prompt.files:
            for uploaded_file in prompt.files:
                # Convert image to base64 for storage
                image_bytes = uploaded_file.read()
                image_b64 = base64.b64encode(image_bytes).decode()
                
                message_data["images"].append({
                    "data": image_b64,
                    "mime_type": uploaded_file.type,
                    "name": uploaded_file.name
                })
        
        # Add user message to session state
        st.session_state.messages.append(message_data)
        
        # Get bot response
        bot_response = get_bot_response(
            prompt.text if prompt.text else "Saya mengirim gambar produk untuk Anda analisis",
            st.session_state.messages[:-1],
            prompt.files if prompt.files else None
        )
        
        # Add bot response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": bot_response
        })
        
        # Rerun to update chat
        st.rerun()

with col2:
    st.subheader("📊 Product Assessment Data")
    
    # Show user ID
    st.caption(f"Session ID: {st.session_state.user_id[:8]}...")
    
    if st.session_state.messages:
        # Extract data from conversation (2 latest messages)
        newly_extracted_data = extract_data_from_conversation(st.session_state.messages)
        
        # Update memorized data with newly extracted data
        if newly_extracted_data and isinstance(newly_extracted_data, dict):
            # Debug: print extracted data
            print(f"Newly extracted data: {newly_extracted_data}")
            
            # Helper function to update nested structures
            def update_nested_data(current_data, new_data):
                if isinstance(new_data, dict):
                    for key, value in new_data.items():
                        if key != "extraction_timestamp":
                            if isinstance(value, dict):
                                if key not in current_data:
                                    current_data[key] = {}
                                update_nested_data(current_data[key], value)
                            elif isinstance(value, list):
                                if key not in current_data:
                                    current_data[key] = []
                                # For lists, append new items if they're not empty
                                if value and value != []:
                                    current_data[key] = value
                            else:
                                # Update simple values only if meaningful
                                if (value != "Not specified" and value != "extraction_error" 
                                    and value != "" and value != 0 and value is not None):
                                    current_data[key] = value
            
            update_nested_data(st.session_state.extracted_data, newly_extracted_data)
        
        # Update timestamp
        st.session_state.extracted_data["extraction_timestamp"] = datetime.now().isoformat()
        
        # Display memorized data as JSON
        st.code(json.dumps(st.session_state.extracted_data, indent=2, ensure_ascii=False), language="json")
        
        # Download button
        st.download_button(
            label="Download JSON",
            data=json.dumps(st.session_state.extracted_data, indent=2, ensure_ascii=False),
            file_name=f"product_assessment_{st.session_state.user_id[:8]}.json",
            mime="application/json"
        )
        
        # Gemini status
        try:
            client = init_gemini()
            st.success("🤖 Connected to Gemini")
        except Exception as e:
            st.error(f"❌ Gemini API connection failed: {str(e)}")
            
    else:
        st.write("Mulai percakapan untuk melihat data assessment yang diekstrak...")

# Reset button
if st.button("🔄 Reset Assessment"):
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.extracted_data = {
        "product_assessment": {
            "product_type": "Not specified",
            "product_name": "Not specified",
            "description": "Not specified",
            "dimensions": "Not specified",
            "target_market": "Not specified",
            "product_category": "Not specified"
        },
        "raw_materials": {
            "primary_materials": [],
            "secondary_materials": [],
            "finishing_materials": {
                "type": "Not specified",
                "brand": "Not specified",
                "chemical_compliance": "Not specified"
            }
        },
        "certifications_required": [],
        "compliance_gaps": [],
        "recommendations": [],
        "extraction_timestamp": datetime.now().isoformat()
    }
    st.rerun()

# Show prompts used
with st.expander("🔧 Prompts Used"):
    st.subheader("Product Assessment Bot Prompt")
    st.code(USER_PROFILING_PROMPT)
    
    st.subheader("Data Extraction Prompt") 
    st.code(DATA_EXTRACTION_PROMPT)