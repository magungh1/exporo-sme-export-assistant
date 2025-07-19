import streamlit as st
import json
from datetime import datetime
import re
from google import genai
from google.genai import types
import uuid
import base64
import io
import sqlite3
import hashlib
import time

# Configure page
st.set_page_config(
    page_title="Exporo - SME Export Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database setup
def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('langkah_ekspor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(first_name, last_name, email, phone, password):
    """Register a new user in the database"""
    try:
        conn = sqlite3.connect('langkah_ekspor.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, phone, password_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, password_hash))
        
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email already exists!"
    except Exception as e:
        conn.close()
        return False, f"Registration failed: {str(e)}"

def login_user(email, password):
    """Authenticate user login"""
    try:
        conn = sqlite3.connect('langkah_ekspor.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT id, first_name, last_name, email FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return True, {
                'id': user[0],
                'first_name': user[1],
                'last_name': user[2],
                'email': user[3]
            }
        else:
            return False, "Invalid email or password!"
    
    except Exception as e:
        return False, f"Login failed: {str(e)}"

def check_email_exists(email):
    """Check if email already exists"""
    try:
        conn = sqlite3.connect('langkah_ekspor.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except:
        return False

# Initialize database
init_db()

# Custom CSS for combined styling
st.markdown("""
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
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 2rem 0;
    }
    
    .welcome-container {
        background: linear-gradient(135deg, #87CEEB, #B0E0E6);
        padding: 3rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .blue-gradient {
        background: linear-gradient(135deg, #87CEEB, #4285F4);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
    }
    
    /* Chat Interface Styles */
    .chat-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-height: 500px;
        max-height: 500px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        scroll-behavior: smooth;
    }
    
    .stContainer > div {
        max-height: 500px;
        overflow-y: auto;
    }
    
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 18px 18px 4px 18px;
        padding: 8px 12px;
        margin: 4px 0;
        margin-left: 20%;
        max-width: 80%;
        align-self: flex-end;
        position: relative;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        color: #1565c0;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        border-radius: 18px 18px 18px 4px;
        padding: 8px 12px;
        margin: 4px 0;
        margin-right: 20%;
        max-width: 80%;
        align-self: flex-start;
        position: relative;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        border: 1px solid #f57f17;
        color: #e65100;
    }
    
    .message-time {
        font-size: 11px;
        color: #667781;
        text-align: right;
        margin-top: 4px;
        opacity: 0.8;
    }
    
    .chat-input {
        background-color: #ffffff;
        border-radius: 25px;
        border: 1px solid #e5e5e5;
        padding: 10px 15px;
        margin-top: 1rem;
    }
    
    .sidebar .element-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stChatInput {
        background-color: #ffffff;
        border-radius: 25px;
    }
    
    .stChatInput > div {
        border-radius: 25px;
        border: 1px solid #e5e5e5;
    }
    
    .stButton > button {
        background-color: #25d366;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #20c157;
        transform: translateY(-1px);
    }
    
    .chat-header {
        background: linear-gradient(90deg, #25d366, #20c157);
        color: white;
        padding: 1rem;
        border-radius: 10px 10px 0 0;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {
        "company_name": "Not specified",
        "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
        "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
        "product_category": "Not specified",
        "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
        "business_background": "Not specified",
        "extraction_timestamp": datetime.now().isoformat(),
        "conversation_language": "Indonesian"
    }
if 'memory_bot' not in st.session_state:
    st.session_state.memory_bot = {
        "company_name": "Not specified",
        "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
        "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
        "product_category": "Not specified",
        "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
        "business_background": "Not specified",
        "extraction_timestamp": datetime.now().isoformat(),
        "conversation_language": "Indonesian"
    }

# Bot prompts
USER_PROFILING_PROMPT = """You are Exporo, a friendly Business Profile Assistant helping Indonesian SMEs prepare for export. Your goal is to gather essential information about their business through a natural, conversational approach.

**Your Objectives:**
1. Collect comprehensive business information
2. Make the user feel comfortable sharing details
3. Guide them through the profiling process step-by-step

**Information to Gather:**
- Product details (name, description, unique features)
- Production capacity (units per month/year)
- Product category/industry classification
- Production location (city, province)
- Company name
- Brief business background

**Conversation Guidelines:**
- Start with a warm greeting in Bahasa Indonesia
- Ask ONE question at a time
- Use simple, clear language
- Acknowledge each answer before moving to the next question
- If answers are vague, ask clarifying follow-ups
- Be encouraging and supportive
- Explain why each piece of information matters for export

**Example Flow:**
1. Greeting: "Halo! Saya Exporo, asisten profil bisnis Anda. Saya akan membantu Anda membuat profil bisnis untuk persiapan ekspor. Boleh saya tahu nama perusahaan Anda?"
2. Product: "Produk apa yang ingin Anda ekspor? Ceritakan sedikit tentang produk Anda."
3. Category: "Produk Anda termasuk dalam kategori apa? (Misalnya: furniture, tekstil, makanan olahan, dll)"
4. Capacity: "Berapa kapasitas produksi Anda saat ini per bulan?"
5. Location: "Di mana lokasi produksi Anda? (Kota dan Provinsi)"

**Important:**
- Always introduce yourself as Exporo at the beginning
- Build rapport before diving into questions
- If user seems hesitant, explain the benefits of completing their profile
- Always thank them for their time and information
- Keep responses friendly and encouraging"""

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

# Initialize Gemini client
@st.cache_resource
def init_gemini():
    api_key = "AIzaSyBNlRT5T_YkJ8QJBdVm6K54GQ1RqrlFJQ8"
    return genai.Client(api_key=api_key)

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
        return {
            "company_name": "Not specified",
            "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
            "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
            "product_category": "Not specified",
            "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
            "business_background": "Not specified",
            "extraction_timestamp": datetime.now().isoformat(),
            "conversation_language": "Indonesian"
        }

# Header with navigation
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### 🚀 Exporo - SME Export Assistant")

# Navigation buttons
if not st.session_state.logged_in:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col2:
        if st.button("Login", type="secondary" if st.session_state.page != 'login' else "primary"):
            st.session_state.page = 'login'
            st.rerun()
    with col4:
        if st.button("Sign Up", type="secondary" if st.session_state.page != 'signup' else "primary"):
            st.session_state.page = 'signup'
            st.rerun()
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Welcome, {st.session_state.user['first_name']}!")
    with col3:
        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = 'login'
            # Reset chat data on logout
            st.session_state.messages = []
            st.session_state.user_id = str(uuid.uuid4())
            st.session_state.extracted_data = {
                "company_name": "Not specified",
                "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
                "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
                "product_category": "Not specified",
                "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
                "business_background": "Not specified",
                "extraction_timestamp": datetime.now().isoformat(),
                "conversation_language": "Indonesian"
            }
            st.session_state.memory_bot = {
                "company_name": "Not specified",
                "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
                "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
                "product_category": "Not specified",
                "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
                "business_background": "Not specified",
                "extraction_timestamp": datetime.now().isoformat(),
                "conversation_language": "Indonesian"
            }
            st.success("Logged out successfully!")
            st.rerun()

# MAIN CONTENT BASED ON AUTHENTICATION STATUS
if not st.session_state.logged_in:
    # LOGIN PAGE
    if st.session_state.page == 'login':
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Left side illustration
            st.markdown('<div class="blue-gradient">', unsafe_allow_html=True)
            st.markdown("**Selamat datang kembali! Masuk untuk melanjutkan perjalanan ekspor Anda**")
            st.image("https://via.placeholder.com/300x200/87CEEB/FFFFFF?text=Login+Illustration", 
                    caption="Welcome Back")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            st.markdown("## Login")
            st.markdown("Masuk ke akun Anda untuk mengakses platform Exporo")
            
            # Login form
            email = st.text_input("Email", placeholder="Masukkan email Anda")
            password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
            
            remember_me = st.checkbox("Ingat saya")
            
            if st.button("Masuk", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("Harap isi email dan password")
                else:
                    with st.spinner("Memverifikasi akun..."):
                        time.sleep(1)
                        success, result = login_user(email, password)
                        
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user = result
                        st.session_state.page = 'chat'
                        st.success("Login berhasil!")
                        st.rerun()
                    else:
                        st.error(result)
            
            st.markdown("---")
            st.markdown("Belum punya akun? Klik tombol **Sign Up** di atas")
            
            st.markdown('</div>', unsafe_allow_html=True)

    # SIGNUP PAGE
    elif st.session_state.page == 'signup':
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Left side illustration
            st.markdown('<div class="blue-gradient">', unsafe_allow_html=True)
            st.markdown("**Bingung ekspor? Exporo bantu UMKM dari awal sampai tembus pasar global**")
            st.image("https://via.placeholder.com/300x200/87CEEB/FFFFFF?text=Export+Illustration", 
                    caption="Export Business Illustration")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Registration form
            st.markdown('<div class="form-container">', unsafe_allow_html=True)
            
            st.markdown("## Daftar")
            st.markdown("Mari kita siapkan semuanya agar kamu bisa mengakses akun pribadimu.")
            
            # Form fields
            col_fname, col_lname = st.columns(2)
            with col_fname:
                first_name = st.text_input("First Name", placeholder="Masukkan nama depan")
            with col_lname:
                last_name = st.text_input("Last Name", placeholder="Masukkan nama belakang")
            
            col_email, col_phone = st.columns(2)
            with col_email:
                email = st.text_input("Email", placeholder="contoh@email.com")
            with col_phone:
                phone = st.text_input("Phone Number", placeholder="08xxxxxxxxxx")
            
            password = st.text_input("Password", type="password", placeholder="Minimal 6 karakter")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Ulangi password")
            
            # Terms checkbox
            terms_agreed = st.checkbox("Saya setuju dengan semua Syarat dan Ketentuan")
            
            # Sign up button
            if st.button("Buat Akun", type="primary", use_container_width=True):
                # Validation
                errors = []
                
                if not first_name.strip():
                    errors.append("First Name wajib diisi")
                if not last_name.strip():
                    errors.append("Last Name wajib diisi")
                if not email.strip():
                    errors.append("Email wajib diisi")
                if not password:
                    errors.append("Password wajib diisi")
                if len(password) < 6:
                    errors.append("Password minimal 6 karakter")
                if not confirm_password:
                    errors.append("Confirm Password wajib diisi")
                if password != confirm_password:
                    errors.append("Password dan Confirm Password tidak sama")
                if not terms_agreed:
                    errors.append("Harap setujui syarat dan ketentuan terlebih dahulu")
                
                # Email format validation
                if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                    errors.append("Format email tidak valid")
                
                # Check if email already exists
                if email and check_email_exists(email):
                    errors.append("Email sudah terdaftar, silakan gunakan email lain")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Register user
                    with st.spinner("Membuat akun..."):
                        time.sleep(1.5)
                        success, message = register_user(first_name, last_name, email, phone, password)
                        
                    if success:
                        st.success("Akun berhasil dibuat! Silakan login.")
                        time.sleep(2)
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error(message)
            
            st.markdown("---")
            st.markdown("Sudah punya akun? Klik tombol **Login** di atas")
            
            st.markdown('</div>', unsafe_allow_html=True)

# CHAT INTERFACE (for logged in users)
else:
    # Show welcome message for first-time users
    if len(st.session_state.messages) == 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        
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

    # Chat Interface
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
            
            for i, message in enumerate(st.session_state.messages):
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
        st.subheader("🧠 Memory Bot")
        
        # Show user ID
        st.caption(f"Session ID: {st.session_state.user_id[:8]}...")
        
        if st.session_state.messages:
            # Extract data from conversation (2 latest messages)
            newly_extracted_data = extract_data_from_conversation(st.session_state.messages)
            
            # Update memorized data with newly extracted data
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
            
            # Display memory_bot as raw JSON
            st.code(json.dumps(st.session_state.memory_bot, indent=2, ensure_ascii=False), language="json")
            
            # Download button for memory_bot data
            st.download_button(
                label="Download JSON",
                data=json.dumps(st.session_state.memory_bot, indent=2, ensure_ascii=False),
                file_name=f"business_profile_{st.session_state.user_id[:8]}.json",
                mime="application/json"
            )
            
            # Gemini status
            try:
                client = init_gemini()
                st.success("🤖 Connected to Gemini")
            except Exception as e:
                st.error(f"❌ Gemini API connection failed: {str(e)}")
                
        else:
            st.write("Mulai percakapan untuk melihat data yang diekstrak...")

    # Reset chat button (only for logged in users)
    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []
        st.session_state.user_id = str(uuid.uuid4())  # New session ID
        st.session_state.extracted_data = {
            "company_name": "Not specified",
            "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
            "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
            "product_category": "Not specified",
            "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
            "business_background": "Not specified",
            "extraction_timestamp": datetime.now().isoformat(),
            "conversation_language": "Indonesian"
        }
        st.session_state.memory_bot = {
            "company_name": "Not specified",
            "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
            "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
            "product_category": "Not specified",
            "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
            "business_background": "Not specified",
            "extraction_timestamp": datetime.now().isoformat(),
            "conversation_language": "Indonesian"
        }
        st.rerun()

# Footer
st.markdown("---")
if st.session_state.logged_in:
    # Show database stats for admin/demo purposes
    try:
        conn = sqlite3.connect('langkah_ekspor.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        st.markdown(f"© 2024 Exporo - Platform UMKM untuk Ekspor Global | Total Users: {user_count}")
    except:
        st.markdown("© 2024 Exporo - Platform UMKM untuk Ekspor Global")
else:
    st.markdown("© 2024 Exporo - Platform UMKM untuk Ekspor Global")