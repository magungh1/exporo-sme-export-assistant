import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import json
import uuid
import base64
from google import genai
from google.genai import types

# Page configuration
st.set_page_config(
    page_title="Langkah Ekspor Saya",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'consultation_type' not in st.session_state:
    st.session_state.consultation_type = None

# Initialize session state for both chat systems
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize extracted data for business profiling
if 'extracted_business_data' not in st.session_state:
    st.session_state.extracted_business_data = {
        "company_name": "Not specified",
        "product_details": {"name": "Not specified", "description": "Not specified", "unique_features": "Not specified"},
        "production_capacity": {"amount": 0, "unit": "Not specified", "timeframe": "Not specified"},
        "product_category": "Not specified",
        "production_location": {"city": "Not specified", "province": "Not specified", "country": "Indonesia"},
        "business_background": "Not specified",
        "extraction_timestamp": datetime.now().isoformat(),
        "conversation_language": "Indonesian"
    }

# Initialize extracted data for product assessment
if 'extracted_product_data' not in st.session_state:
    st.session_state.extracted_product_data = {
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

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #4A90E2;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px;
        font-weight: bold;
    }
    .consultation-button {
        background-color: #28a745 !important;
        color: white !important;
    }
    .back-button {
        background-color: #6c757d !important;
        color: white !important;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .step-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .completed-step {
        color: #28a745;
    }
    .pending-step {
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Bot prompts for business profiling
BUSINESS_PROFILING_PROMPT = """You are a friendly Business Profile Assistant helping Indonesian SMEs prepare for export. Your goal is to gather essential information about their business through a natural, conversational approach.

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
1. Greeting: "Selamat datang! Saya akan membantu Anda membuat profil bisnis untuk persiapan ekspor. Boleh saya tahu nama perusahaan Anda?"
2. Product: "Produk apa yang ingin Anda ekspor? Ceritakan sedikit tentang produk Anda."
3. Category: "Produk Anda termasuk dalam kategori apa? (Misalnya: furniture, tekstil, makanan olahan, dll)"
4. Capacity: "Berapa kapasitas produksi Anda saat ini per bulan?"
5. Location: "Di mana lokasi produksi Anda? (Kota dan Provinsi)"

**Important:**
- Build rapport before diving into questions
- If user seems hesitant, explain the benefits of completing their profile
- Always thank them for their time and information"""

# Bot prompts for product assessment
PRODUCT_ASSESSMENT_PROMPT = """You are a Product Assessment Specialist focusing on Indonesian product exports. Your role is to analyze products, identify raw materials, and determine certification requirements for various industries.

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

# Initialize Gemini client
@st.cache_resource
def init_gemini():
    api_key = "AIzaSyBNlRT5T_YkJ8QJBdVm6K54GQ1RqrlFJQ8"
    return genai.Client(api_key=api_key)

def get_bot_response(user_input, conversation_history, consultation_type, uploaded_files=None):
    """Get bot response using Gemini API with appropriate prompt"""
    client = init_gemini()
    
    # Choose prompt based on consultation type
    if consultation_type == "business_profiling":
        system_prompt = BUSINESS_PROFILING_PROMPT
        assistant_intro = "Saya siap membantu sebagai Business Profile Assistant untuk UKM Indonesia. Saya akan mengumpulkan informasi bisnis secara bertahap dan ramah."
    else:  # product_assessment
        system_prompt = PRODUCT_ASSESSMENT_PROMPT
        assistant_intro = "Saya siap membantu sebagai Product Assessment Specialist untuk ekspor produk Indonesia. Saya akan menganalisis produk, bahan baku, dan kebutuhan sertifikasi secara detail."
    
    # Prepare conversation content for Gemini
    contents = []
    
    # Add system prompt as first user message
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=system_prompt)]
    ))
    
    # Add a model response acknowledging the system prompt
    contents.append(types.Content(
        role="model", 
        parts=[types.Part.from_text(text=assistant_intro)]
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

def render_dashboard():
    """Render the main dashboard page"""
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/50", width=50)  # Replace with actual logo
        st.title("Langkah Ekspor")
        
        # User profile
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://via.placeholder.com/40", width=40)  # User avatar
        with col2:
            st.markdown("**Marley Botosh**")
        
        st.markdown("---")
        
        # Navigation menu
        if st.button("📊 Langkah Ekspor Saya"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("👤 Profil Bisnis"):
            st.session_state.current_page = 'business_chat'
            st.session_state.consultation_type = 'business_profiling'
            st.rerun()
        
        if st.button("📦 Assessment Produk"):
            st.session_state.current_page = 'product_chat'
            st.session_state.consultation_type = 'product_assessment'
            st.rerun()
        
        if st.button("🚪 Logout"):
            st.session_state.current_page = 'dashboard'
            st.rerun()

    # Main content
    st.title("Langkah Ekspor Saya")

    # Top section with three columns
    col1, col2, col3 = st.columns([2, 1.5, 2])

    # Product Details
    with col1:
        st.markdown("### Produk Detail")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        details = {
            "Nama Usaha": "CV Jati Sejahtera",
            "Produk Dijual": "Meja makan kayu jati minimalis",
            "Kapasitas Produksi": "±100 unit/bulan",
            "Kategori Produk": "_(Belum didaftarkan)_",
            "Lokasi Produksi": "Jepara, Jawa Tengah"
        }
        
        for key, value in details.items():
            if key == "Kategori Produk":
                st.markdown(f"**{key}**: <span style='color: red;'>{value}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{key}**: {value}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Export Readiness Chart
    with col2:
        st.markdown("### Kesiapan Ekspor")
        
        # Create a donut chart
        fig = go.Figure(data=[go.Pie(
            values=[42, 58],
            hole=.7,
            marker_colors=['#28a745', '#e0e0e0'],
            textinfo='none',
            hoverinfo='skip'
        )])
        
        fig.update_layout(
            showlegend=False,
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            annotations=[dict(
                text='42%',
                x=0.5, y=0.5,
                font_size=24,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<center>42% Siap Ekspor</center>", unsafe_allow_html=True)

    # Country Recommendations
    with col3:
        st.markdown("### Rekomendasi Negara Potensial")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        countries = [
            ("🇸🇬 Singapura", "High Demand"),
            ("🇺🇸 USA", "Butuh sertifikasi V-Legal"),
            ("🇲🇾 Malaysia", "Entry-level market")
        ]
        
        for country, note in countries:
            st.markdown(f"**{country}** – {note}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Progress Steps
    st.markdown("---")

    # Create two columns for the steps
    col1, col2 = st.columns(2)

    # Step 1
    with col1:
        with st.container():
            st.markdown("### Langkah 1: Kualitas Produk & Potensi Ekspor")
            
            # Progress bar
            st.progress(1/7, text="1 of 7 steps completed")
            
            st.markdown("**Rangkuman:**")
            st.markdown("Produk Anda sudah layak untuk pasar ekspor, tetapi masih perlu melengkapi sertifikasi legalitas kayu dan deskripsi produk yang lebih detail.")
            
            steps = [
                ("Unggah Foto Produk & Deskripsi", "Selasa, 1 Juli 2025", True),
                ("Tentukan Komposisi & Bahan Baku", "Selasa, 1 Juli 2025", True),
                ("Cek Kebutuhan Sertifikasi (V-Legal, FLEGT)", "Selasa, 3 Juli 2025", False),
                ("Tentukan HS Code Produk", "Selasa, 3 Juli 2025", False)
            ]
            
            for step, date, completed in steps:
                if completed:
                    st.markdown(f"✅ **{step}**")
                    st.caption(f"   {date}")
                else:
                    st.markdown(f"⭕ {step}")
                    st.caption(f"   {date}")
            
            if st.button("Konsultasi Produk", key="konsultasi1"):
                st.session_state.current_page = 'product_chat'
                st.session_state.consultation_type = 'product_assessment'
                st.rerun()

    # Step 2
    with col2:
        with st.container():
            st.markdown("### Langkah 2: Strategi Penjualan")
            
            # Progress bar
            st.progress(1/7, text="1 of 7 steps completed")
            
            st.markdown("**Rangkuman:**")
            st.markdown("Anda telah memilih marketplace tujuan, tapi strategi harga dan promosi belum dirancang.")
            
            steps = [
                ("Pilih Marketplace Global", "Selasa, 1 Juli 2025", True),
                ("Simulasikan Harga Jual Ekspor", "Selasa, 1 Juli 2025", True),
                ("Lengkapi Profil Bisnis", "Selasa, 3 Juli 2025", False),
                ("Tentukan Target Pasar", "Selasa, 3 Juli 2025", False)
            ]
            
            for step, date, completed in steps:
                if completed:
                    st.markdown(f"✅ **{step}**")
                    st.caption(f"   {date}")
                else:
                    st.markdown(f"⭕ {step}")
                    st.caption(f"   {date}")
            
            if st.button("Konsultasi Bisnis", key="konsultasi2"):
                st.session_state.current_page = 'business_chat'
                st.session_state.consultation_type = 'business_profiling'
                st.rerun()

    # Steps 3 and 4
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Langkah 3: Distribusi & Logistik")
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown("Coming soon...")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown("### Langkah 4: Legalitas & Dokumen")
        st.markdown('<div class="step-card">', unsafe_allow_html=True)
        st.markdown("Coming soon...")
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("<center>© 2025 Langkah Ekspor - Platform Ekspor Indonesia</center>", unsafe_allow_html=True)

def render_business_chat():
    """Render the business profiling chat interface"""
    st.title("👤 Konsultasi Profil Bisnis")
    
    # Back button
    if st.button("← Kembali ke Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
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
                prompt.text if prompt.text else "Saya mengirim gambar untuk Anda lihat",
                st.session_state.messages[:-1],
                "business_profiling",
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
        st.subheader("📊 Business Profile Data")
        
        # Show user ID
        st.caption(f"Session ID: {st.session_state.user_id[:8]}...")
        
        if st.session_state.messages:
            # Display memorized data as JSON
            st.code(json.dumps(st.session_state.extracted_business_data, indent=2, ensure_ascii=False), language="json")
            
            # Download button
            st.download_button(
                label="Download JSON",
                data=json.dumps(st.session_state.extracted_business_data, indent=2, ensure_ascii=False),
                file_name=f"business_profile_{st.session_state.user_id[:8]}.json",
                mime="application/json"
            )
        else:
            st.write("Mulai percakapan untuk melihat data yang diekstrak...")
        
        # Reset button
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.session_state.user_id = str(uuid.uuid4())
            st.rerun()

def render_product_chat():
    """Render the product assessment chat interface"""
    st.title("📦 Konsultasi Assessment Produk")
    
    # Back button
    if st.button("← Kembali ke Dashboard"):
        st.session_state.current_page = 'dashboard'
        st.rerun()
    
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
                "product_assessment",
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
            # Display memorized data as JSON
            st.code(json.dumps(st.session_state.extracted_product_data, indent=2, ensure_ascii=False), language="json")
            
            # Download button
            st.download_button(
                label="Download JSON",
                data=json.dumps(st.session_state.extracted_product_data, indent=2, ensure_ascii=False),
                file_name=f"product_assessment_{st.session_state.user_id[:8]}.json",
                mime="application/json"
            )
        else:
            st.write("Mulai percakapan untuk melihat data assessment yang diekstrak...")
        
        # Reset button
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.session_state.user_id = str(uuid.uuid4())
            st.rerun()

# Main navigation logic
if st.session_state.current_page == 'dashboard':
    render_dashboard()
elif st.session_state.current_page == 'business_chat':
    render_business_chat()
elif st.session_state.current_page == 'product_chat':
    render_product_chat()
else:
    render_dashboard()