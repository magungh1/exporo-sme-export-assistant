"""
Chat module for Exporo SME Export Assistant
Handles chat interface, Gemini AI integration, and memory bot functionality
"""

import streamlit as st
import json
from datetime import datetime
import uuid
import base64
import io
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, USER_PROFILING_PROMPT, DATA_EXTRACTION_PROMPT, DEFAULT_EXTRACTED_DATA

# Initialize Gemini client
@st.cache_resource
def init_gemini():
    """Initialize and cache Gemini client"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY not configured. Please set it in your environment variables or .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)

def get_bot_response(user_input, conversation_history, uploaded_images=None):
    """Get bot response using Gemini API with user profiling prompt"""
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
        parts=[types.Part.from_text(text="Saya Exporo, siap membantu sebagai Business Profile Assistant untuk UKM Indonesia. Saya akan mengumpulkan informasi bisnis secara bertahap dan ramah.")]
    ))
    
    # Add conversation history
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        parts = [types.Part.from_text(text=msg["content"])]
        
        # Add images if present in message
        if "images" in msg and msg["images"]:
            for img_bytes in msg["images"]:
                parts.append(types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/jpeg"
                ))
        
        contents.append(types.Content(
            role=role,
            parts=parts
        ))
    
    # Add current user input
    parts = [types.Part.from_text(text=user_input)]
    
    # Add uploaded images if present
    if uploaded_images:
        for uploaded_image in uploaded_images:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            uploaded_image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            parts.append(types.Part.from_bytes(
                data=img_byte_arr,
                mime_type="image/jpeg"
            ))
    
    contents.append(types.Content(
        role="user",
        parts=parts
    ))
    
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
    """Extract structured data using Gemini API with data extraction prompt from 2 latest messages"""
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
            parts=[types.Part.from_text(text="I understand. I will extract structured business profile data from the conversation and return it as clean JSON.")]
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
        return DEFAULT_EXTRACTED_DATA.copy()

def init_chat_session_state():
    """Initialize chat-related session state"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = DEFAULT_EXTRACTED_DATA.copy()
    if 'memory_bot' not in st.session_state:
        st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()

def update_memory_bot(newly_extracted_data):
    """Update memory_bot with only non-null values from extracted_data"""
    if newly_extracted_data and isinstance(newly_extracted_data, dict):
        # Debug: print extracted data
        print(f"Newly extracted data: {newly_extracted_data}")
        
        # Update extracted_data (temporary)
        for key, value in newly_extracted_data.items():
            if key != "extraction_timestamp" and value != "Not specified" and value != "extraction_error" and value != "" and value != 0:
                if isinstance(value, dict):
                    # Update nested dictionary - only if new value is meaningful
                    for nested_key, nested_value in value.items():
                        if (nested_value != "Not specified" and nested_value != "extraction_error" and 
                            nested_value != "" and nested_value != 0 and nested_value is not None):
                            st.session_state.extracted_data[key][nested_key] = nested_value
                else:
                    # Update simple value - only if new value is meaningful
                    if value is not None:
                        st.session_state.extracted_data[key] = value
        
        # Update memory_bot - only non-null values from extracted_data
        for key, value in newly_extracted_data.items():
            if key != "extraction_timestamp" and value and value != "Not specified" and value != "extraction_error" and value != "" and value != 0:
                if isinstance(value, dict):
                    # Update nested dictionary in memory_bot - only if new value is meaningful
                    for nested_key, nested_value in value.items():
                        if (nested_value and nested_value != "Not specified" and nested_value != "extraction_error" and 
                            nested_value != "" and nested_value != 0 and nested_value is not None):
                            st.session_state.memory_bot[key][nested_key] = nested_value
                else:
                    # Update simple value in memory_bot - only if new value is meaningful
                    if value is not None:
                        st.session_state.memory_bot[key] = value
    
    # Update timestamp
    st.session_state.extracted_data["extraction_timestamp"] = datetime.now().isoformat()

def show_welcome_message():
    """Display welcome message for first-time users"""
    if len(st.session_state.messages) == 0:
        _, col2, _ = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
            
            # Character illustration
            st.image("https://via.placeholder.com/200x250/4285F4/FFFFFF?text=Exporo+Character", 
                    width=200, caption="Exporo Assistant")
            
            # Welcome message
            user_name = st.session_state.user['first_name']
            st.markdown(f"**Hai {user_name}! Aku Exporo. Siap bantu ekspor bisnismu ke dunia!**")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Main welcome content
            st.markdown(f"""
            Halo **{user_name}**! Saya **Exporo**, yang akan membimbing setiap langkah ekspor produk Anda ke luar negeri mulai 
            dari cek kesiapan, urus dokumen, sampai strategi penjualan global.
            
            Sebelum memulai, saya perlu mengenal sedikit tentang Anda. Mulai percakapan di bawah untuk memulai profiling bisnis Anda!
            """)

def show_chat_interface():
    """Display the main chat interface"""
    col1, col2 = st.columns([2, 1])

    with col1:
        # Chat header
        st.markdown('<div class="chat-header">💬 Exporo Chat Assistant</div>', unsafe_allow_html=True)
        
        # Display chat history in a styled container with fixed height and auto-scroll
        chat_container = st.container(height=500, border=True)
        with chat_container:
            if not st.session_state.messages:
                st.markdown("""
                <div style="text-align: center; color: #667781; margin-top: 50px; font-style: italic;">
                    👋 Selamat datang! Mulai percakapan dengan mengetik pesan di bawah.
                </div>
                """, unsafe_allow_html=True)
            
            for message in st.session_state.messages:
                # Get timestamp - use message timestamp if available, otherwise current time
                if 'timestamp' in message:
                    msg_time = datetime.fromisoformat(message['timestamp']).strftime("%H:%M")
                else:
                    msg_time = datetime.now().strftime("%H:%M")
                
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        {message["content"]}
                        <div class="message-time">{msg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display images if present
                    if message.get("images"):
                        for img in message["images"]:
                            st.image(base64.b64decode(img["data"]), caption="📷 Gambar produk", width=300)
                            
                else:  # assistant message
                    st.markdown(f"""
                    <div class="assistant-message">
                        {message["content"]}
                        <div class="message-time">{msg_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
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
                "images": [],
                "timestamp": datetime.now().isoformat()
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
            
            # Set flag to generate bot response
            st.session_state.generate_response = True
            
            # Rerun to show user message immediately
            st.rerun()
        
        # Generate bot response if flag is set
        if st.session_state.get('generate_response', False):
            # Clear the flag
            st.session_state.generate_response = False
            
            # Get the last user message
            last_user_message = st.session_state.messages[-1]
            
            # Show typing indicator while getting bot response
            with st.spinner("💭 Sedang mengetik..."):
                # Get bot response
                bot_response = get_bot_response(
                    last_user_message["content"] if last_user_message["content"] else "Saya mengirim gambar untuk Anda lihat",
                    st.session_state.messages[:-1],
                    None  # Files are already processed and stored in the message
                )
                
                # Add bot response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": bot_response,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Rerun to show bot response
            st.rerun()

    with col2:
        show_memory_bot()

def show_memory_bot():
    """Display the memory bot sidebar"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    ">
        <h3 style="color: white; margin: 0; font-weight: 600;">🧠 Memory Bot</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Show user ID
    st.caption(f"Session ID: {st.session_state.user_id[:8]}...")
    
    if st.session_state.messages:
        # Extract data from conversation (2 latest messages)
        newly_extracted_data = extract_data_from_conversation(st.session_state.messages)
        
        # Update memory bot
        update_memory_bot(newly_extracted_data)
        
        # Display memory_bot as raw JSON
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #f8f9fa, #e9ecef);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(0,0,0,0.1);
            margin: 1rem 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        ">
        """, unsafe_allow_html=True)
        
        st.code(json.dumps(st.session_state.memory_bot, indent=2, ensure_ascii=False), language="json")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Download button for memory_bot data
        st.download_button(
            label="Download JSON",
            data=json.dumps(st.session_state.memory_bot, indent=2, ensure_ascii=False),
            file_name=f"business_profile_{st.session_state.user_id[:8]}.json",
            mime="application/json"
        )
        
        # Gemini status with background
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(0,0,0,0.05);
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        ">
        """, unsafe_allow_html=True)
        
        try:
            init_gemini()
            st.success("🤖 Connected to Gemini")
        except ValueError as e:
            st.error(f"⚠️ Configuration Error: {str(e)}")
            st.info("💡 Create a .env file with your GEMINI_API_KEY or set it as an environment variable")
        except Exception as e:
            st.error(f"❌ Gemini API connection failed: {str(e)}")
            
        st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        st.write("Mulai percakapan untuk melihat data yang diekstrak...")

def reset_chat():
    """Reset chat data"""
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())  # New session ID
    st.session_state.extracted_data = DEFAULT_EXTRACTED_DATA.copy()
    st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()

def show_chat_reset_button():
    """Show reset chat button"""
    if st.button("🔄 Reset Chat"):
        reset_chat()
        st.rerun()

def show_full_chat_page():
    """Display the complete chat page"""
    show_welcome_message()
    show_chat_interface()
    show_chat_reset_button()