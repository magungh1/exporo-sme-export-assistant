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
from .config import (
    GEMINI_API_KEY,
    USER_PROFILING_PROMPT,
    EXPORT_FOCUSED_PROMPT,
    DATA_EXTRACTION_PROMPT,
    EXPORT_DATA_EXTRACTION_PROMPT,
    EXPORT_READINESS_PROMPT,
    DEFAULT_EXTRACTED_DATA,
)


# Initialize Gemini client
@st.cache_resource
def init_gemini():
    """Initialize and cache Gemini client"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY not configured. Please set it in your environment variables or .env file."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def get_bot_response(user_input, conversation_history, uploaded_images=None):
    """Get bot response using Gemini API with intelligent prompt selection"""

    # Get memory data and check profile completeness
    memory_data = st.session_state.get("memory_bot", DEFAULT_EXTRACTED_DATA)
    profile_status = check_profile_completeness(memory_data)

    # Check if user is requesting export analysis
    analysis_requested, target_country = detect_export_analysis_request(
        user_input, memory_data
    )

    # If export analysis is requested and we have a target country, perform analysis
    if analysis_requested and target_country:
        return perform_chat_based_export_analysis(target_country, memory_data)

    # If analysis requested but no country, ask for country specification
    if analysis_requested and not target_country:
        return """
🤔 **Saya siap melakukan analisis kesiapan ekspor untuk Anda!**

Namun, saya perlu tahu negara tujuan ekspor yang Anda inginkan. Berikut beberapa pilihan:

🌏 **Negara yang Tersedia:**
• 🇲🇾 **Malaysia** - Tingkat kesulitan: Rendah
• 🇸🇬 **Singapura** - Tingkat kesulitan: Sedang
• 🇦🇺 **Australia** - Tingkat kesulitan: Sedang
• 🇰🇷 **Korea Selatan** - Tingkat kesulitan: Sedang
• 🇺🇸 **Amerika Serikat** - Tingkat kesulitan: Tinggi
• 🇪🇺 **Uni Eropa** - Tingkat kesulitan: Tinggi
• 🇯🇵 **Jepang** - Tingkat kesulitan: Tinggi
• 🇨🇳 **China** - Tingkat kesulitan: Tinggi

💡 **Contoh perintah:**
- "Cek kesiapan ekspor ke Malaysia"
- "Analisis ekspor ke Amerika Serikat"
- "Siap ekspor ke Singapura tidak?"

Negara mana yang ingin Anda analisis?
        """

    # Select appropriate prompt based on profile completeness
    if profile_status["is_complete"]:
        # Use export-focused prompt with user data
        company_name = memory_data.get("company_name", "Not specified")
        product_name = memory_data.get("product_details", {}).get("name", "Not specified")
        product_category = memory_data.get("product_category", "Not specified")

        # Format production capacity
        capacity = memory_data.get("production_capacity", {})
        capacity_str = f"{capacity.get('amount', 0)} {capacity.get('unit', '')} per {capacity.get('timeframe', '')}"

        # Format production location
        location = memory_data.get("production_location", {})
        location_str = f"{location.get('city', '')}, {location.get('province', '')}"

        system_prompt = EXPORT_FOCUSED_PROMPT.format(
            company_name=company_name,
            product_name=product_name,
            product_category=product_category,
            production_capacity=capacity_str,
            production_location=location_str
        )
    else:
        # Use profile building prompt
        system_prompt = USER_PROFILING_PROMPT

    # Normal chat flow
    client = init_gemini()

    # Prepare conversation content for Gemini
    contents = []

    # Add system prompt as first user message
    contents.append(
        types.Content(
            role="user", parts=[types.Part.from_text(text=system_prompt)]
        )
    )

    # Add a model response acknowledging the system prompt based on mode
    if profile_status["is_complete"]:
        acknowledgment_text = f"Saya Exporo, siap membantu sebagai Export Specialist untuk {memory_data.get('company_name', 'perusahaan Anda')}. Profil bisnis Anda sudah lengkap dan saya akan fokus pada strategi ekspor dan analisis kesiapan pasar internasional."
    else:
        acknowledgment_text = "Saya Exporo, siap membantu sebagai Business Profile Assistant untuk UKM Indonesia. Saya akan mengumpulkan informasi bisnis secara bertahap dan ramah serta membantu analisis kesiapan ekspor."

    contents.append(
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text=acknowledgment_text)
            ],
        )
    )

    # Add conversation history
    for msg in conversation_history:
        role = "model" if msg["role"] == "assistant" else "user"
        parts = [types.Part.from_text(text=msg["content"])]

        # Add images if present in message
        if "images" in msg and msg["images"]:
            for img_bytes in msg["images"]:
                parts.append(
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                )

        contents.append(types.Content(role=role, parts=parts))

    # Add current user input
    parts = [types.Part.from_text(text=user_input)]

    # Add uploaded images if present
    if uploaded_images:
        for uploaded_image in uploaded_images:
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            uploaded_image.save(img_byte_arr, format="JPEG")
            img_byte_arr = img_byte_arr.getvalue()

            parts.append(
                types.Part.from_bytes(data=img_byte_arr, mime_type="image/jpeg")
            )

    contents.append(types.Content(role="user", parts=parts))

    try:
        generate_config = types.GenerateContentConfig(
            response_mime_type="text/plain", max_output_tokens=4000, temperature=0.7
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents, config=generate_config
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


def extract_data_from_conversation(conversation_history):
    """Extract structured data using Gemini API with data extraction prompt from latest and previous chat"""
    client = init_gemini()

    # Use the latest 4 messages to capture both latest and previous chat context
    latest_messages = (
        conversation_history[-4:]
        if len(conversation_history) >= 4
        else conversation_history
    )

    # Prepare conversation text
    conversation_text = "\n".join(
        [f"{msg['role']}: {msg.get('content', '')}" for msg in latest_messages]
    )

    # Prepare contents for Gemini
    contents = [
        types.Content(
            role="user", parts=[types.Part.from_text(text=DATA_EXTRACTION_PROMPT)]
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"Extract data from this conversation:\n\n{conversation_text}"
                )
            ],
        ),
    ]

    try:
        generate_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config = types.ThinkingConfig(
            thinking_budget=-1),
            max_output_tokens=4000,
            temperature=0.1
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents, config=generate_config
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
        print(
            f"Response text: {response.text if 'response' in locals() else 'No response'}"
        )
        print(f"JSON text: {json_text if 'json_text' in locals() else 'No json_text'}")

        # Fallback to default structure
        return DEFAULT_EXTRACTED_DATA.copy()


def init_chat_session_state():
    """Initialize chat-related session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = DEFAULT_EXTRACTED_DATA.copy()
    if "memory_bot" not in st.session_state:
        # Load saved Memory Bot data if user is logged in
        if st.session_state.get('logged_in', False) and st.session_state.get('user'):
            from .auth import load_memory_bot_data
            user_id = st.session_state.user['id']
            st.session_state.memory_bot = load_memory_bot_data(user_id)
        else:
            st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()


def extract_export_data_from_conversation(conversation_history):
    """Extract export readiness data using Gemini API with export-specific extraction prompt from latest and previous chat"""
    client = init_gemini()

    # Use the latest 6 messages to capture both latest and previous chat context for export data
    latest_messages = (
        conversation_history[-6:]
        if len(conversation_history) >= 6
        else conversation_history
    )

    # Prepare conversation text
    conversation_text = "\n".join(
        [f"{msg['role']}: {msg.get('content', '')}" for msg in latest_messages]
    )

    # Check if conversation contains export-related keywords
    export_keywords = [
        "export",
        "ekspor",
        "international",
        "negara",
        "country",
        "market",
        "pasar",
        "certification",
        "sertifikasi",
        "readiness",
    ]
    has_export_content = any(
        keyword.lower() in conversation_text.lower() for keyword in export_keywords
    )

    if not has_export_content:
        return {}

    # Prepare contents for Gemini
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=EXPORT_DATA_EXTRACTION_PROMPT)],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(
                    text="I understand. I will extract structured export readiness data from the conversation and return it as clean JSON."
                )
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=f"Extract export data from this conversation:\n\n{conversation_text}"
                )
            ],
        ),
    ]

    try:
        generate_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=4000,
            temperature=0.1,
            thinking_config = types.ThinkingConfig(
            thinking_budget=-1)
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents, config=generate_config
        )

        # Parse JSON response
        json_text = response.text.strip() if response.text else ""
        # Remove markdown formatting if present
        if json_text.startswith("```json"):
            json_text = json_text.replace("```json", "").replace("```", "").strip()

        return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting export data: {e}")
        return {}


def update_memory_bot(newly_extracted_data):
    """Update memory_bot with meaningful values from extracted_data - persistent dictionary with existing data protection"""
    if newly_extracted_data and isinstance(newly_extracted_data, dict):
        # Ensure memory_bot exists and is a copy of DEFAULT_EXTRACTED_DATA structure
        if "memory_bot" not in st.session_state:
            st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()

        # Update extracted_data (temporary) - less restrictive filtering
        for key, value in newly_extracted_data.items():
            if key != "extraction_timestamp" and is_meaningful_value(value):
                if isinstance(value, dict):
                    # Ensure nested dict exists in extracted_data
                    if key not in st.session_state.extracted_data:
                        st.session_state.extracted_data[key] = {}
                    # Update nested dictionary - only meaningful values
                    for nested_key, nested_value in value.items():
                        if is_meaningful_value(nested_value):
                            st.session_state.extracted_data[key][nested_key] = nested_value
                else:
                    st.session_state.extracted_data[key] = value

        # Update memory_bot with persistent merging and existing data protection
        for key, value in newly_extracted_data.items():
            if key != "extraction_timestamp" and is_meaningful_value(value):
                if isinstance(value, dict):
                    # Ensure nested dict exists in memory_bot
                    if key not in st.session_state.memory_bot:
                        st.session_state.memory_bot[key] = {}
                    elif not isinstance(st.session_state.memory_bot[key], dict):
                        st.session_state.memory_bot[key] = {}

                    # Merge nested dictionary values persistently with existing data protection
                    for nested_key, nested_value in value.items():
                        if is_meaningful_value(nested_value):
                            # Check if existing data exists and is meaningful
                            existing_value = st.session_state.memory_bot[key].get(nested_key)

                            # Only update if:
                            # 1. No existing data exists, OR
                            # 2. Existing data is not meaningful, OR
                            # 3. New value is more specific/detailed than existing
                            if (not existing_value or
                                not is_meaningful_value(existing_value) or
                                is_more_detailed_value(nested_value, existing_value)):
                                st.session_state.memory_bot[key][nested_key] = nested_value
                else:
                    # Check existing simple value before updating
                    existing_value = st.session_state.memory_bot.get(key)

                    # Only update if:
                    # 1. No existing data exists, OR
                    # 2. Existing data is not meaningful, OR
                    # 3. New value is more specific/detailed than existing
                    if (not existing_value or
                        not is_meaningful_value(existing_value) or
                        is_more_detailed_value(value, existing_value)):
                        st.session_state.memory_bot[key] = value

        # Update timestamp
        st.session_state.extracted_data["extraction_timestamp"] = datetime.now().isoformat()

        # Auto-save Memory Bot data to database if user is logged in
        if st.session_state.get('logged_in', False) and st.session_state.get('user'):
            from .auth import save_memory_bot_data
            user_id = st.session_state.user['id']
            success, message = save_memory_bot_data(user_id, st.session_state.memory_bot)
            if not success:
                print(f"Failed to auto-save Memory Bot data: {message}")

def is_meaningful_value(value):
    """Check if a value is meaningful and should be stored"""
    if value is None:
        return False
    if isinstance(value, str):
        return value not in ["", "Not specified", "extraction_error", "Belum diisi", "unclear"]
    if isinstance(value, (list, dict)):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return True  # Allow 0 as a valid value
    return bool(value)


def is_more_detailed_value(new_value, existing_value):
    """Check if new value is more detailed/specific than existing value"""
    # If types are different, prefer non-default values
    if type(new_value) != type(existing_value):
        return is_meaningful_value(new_value) and not is_meaningful_value(existing_value)

    # For strings, check if new value is more specific
    if isinstance(new_value, str) and isinstance(existing_value, str):
        # Longer, more detailed strings are generally better
        if len(new_value.strip()) > len(existing_value.strip()):
            return True
        # If lengths are similar, prefer non-generic values
        generic_terms = ["Not specified", "Belum diisi", "unclear", "extraction_error"]
        new_is_generic = any(term.lower() in new_value.lower() for term in generic_terms)
        existing_is_generic = any(term.lower() in existing_value.lower() for term in generic_terms)
        return not new_is_generic and existing_is_generic

    # For numbers, prefer larger meaningful values (like production capacity)
    if isinstance(new_value, (int, float)) and isinstance(existing_value, (int, float)):
        return new_value > existing_value and new_value > 0

    # For lists, prefer longer lists with more items
    if isinstance(new_value, list) and isinstance(existing_value, list):
        return len(new_value) > len(existing_value)

    # For dicts, prefer dicts with more meaningful keys
    if isinstance(new_value, dict) and isinstance(existing_value, dict):
        new_meaningful_keys = sum(1 for k, v in new_value.items() if is_meaningful_value(v))
        existing_meaningful_keys = sum(1 for k, v in existing_value.items() if is_meaningful_value(v))
        return new_meaningful_keys > existing_meaningful_keys

    # Default: don't replace existing value
    return False


def show_welcome_message():
    """Display welcome message for first-time users"""
    if len(st.session_state.messages) == 0:
        _, col2, _ = st.columns([1, 2, 1])

        with col2:
            st.markdown('<div class="welcome-container">', unsafe_allow_html=True)

            # Character illustration
            st.image(
                "https://via.placeholder.com/200x250/4285F4/FFFFFF?text=Exporo+Character",
                width=200,
                caption="Exporo Assistant",
            )

            # Welcome message
            user_name = st.session_state.user["first_name"]
            st.markdown(
                f"**Hai {user_name}! Aku Exporo. Siap bantu ekspor bisnismu ke dunia!**"
            )

            st.markdown("</div>", unsafe_allow_html=True)

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
        st.markdown(
            """
        <div style="
            background: linear-gradient(180deg, #2c3e50, #34495e);
            color: white;
            padding: 1.2rem;
            border-radius: 15px;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: bold;
            box-shadow: 0 6px 20px rgba(44, 62, 80, 0.3);
            border: 1px solid rgba(255,255,255,0.2);
        ">💬 Exporo Chat Assistant</div>
        """,
            unsafe_allow_html=True,
        )

        # Display chat history in a styled container with dynamic height
        st.markdown("""
        <style>
        .chat-container {
            height: calc(75vh - 250px);
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 1rem;
            background: white;
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Wrap chat messages in the dynamic height container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        if not st.session_state.messages:
            for message in st.session_state.messages:
                # Get timestamp - use message timestamp if available, otherwise current time
                if "timestamp" in message:
                    msg_time = datetime.fromisoformat(message["timestamp"]).strftime(
                        "%H:%M"
                    )
                else:
                    msg_time = datetime.now().strftime("%H:%M")

                if message["role"] == "user":
                    st.markdown(
                        f"""
                    <div class="user-message">
                        {message["content"]}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display images if present
                    if message.get("images"):
                        for img in message["images"]:
                            st.image(
                                base64.b64decode(img["data"]),
                                caption="📷 Gambar produk",
                                width=300,
                            )

                else:  # assistant message
                    # Check if this is an export readiness analysis response
                    is_export_analysis = (
                        "ANALISIS KESIAPAN EKSPOR" in message["content"] or
                        "🎯 **ANALISIS KESIAPAN EKSPOR" in message["content"]
                    )

                    if is_export_analysis:
                        # Display export analysis without timestamp
                        st.markdown(
                            f"""
                        <div class="assistant-message">
                            {message["content"]}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        # Display regular messages with timestamp
                        st.markdown(
                            f"""
                        <div class="assistant-message">{message["content"]}</div>""",
                            unsafe_allow_html=True,
                        )

        # Close the chat container div
        st.markdown('</div>', unsafe_allow_html=True)

        # Chat input with file upload support
        prompt = st.chat_input(
            "Ketik pesan Anda dan/atau upload gambar produk...",
            accept_file=True,
            file_type=["jpg", "jpeg", "png", "webp"],
        )

        if prompt:
            # Prepare message data
            message_data = {
                "role": "user",
                "content": prompt.text if prompt.text else "",
                "images": [],
                "timestamp": datetime.now().isoformat(),
            }

            # Handle uploaded files
            if prompt.files:
                for uploaded_file in prompt.files:
                    # Convert image to base64 for storage
                    image_bytes = uploaded_file.read()
                    image_b64 = base64.b64encode(image_bytes).decode()

                    message_data["images"].append(
                        {
                            "data": image_b64,
                            "mime_type": uploaded_file.type,
                            "name": uploaded_file.name,
                        }
                    )

            # Add user message to session state
            st.session_state.messages.append(message_data)

            # Set flag to generate bot response
            st.session_state.generate_response = True

            # Rerun to show user message immediately
            st.rerun()

        # Generate bot response if flag is set
        if st.session_state.get("generate_response", False):
            # Clear the flag
            st.session_state.generate_response = False

            # Safety check: ensure there are messages before accessing
            if st.session_state.messages:
                # Get the last user message
                last_user_message = st.session_state.messages[-1]

                # Show typing indicator while getting bot response
                with st.spinner("💭 Sedang mengetik..."):
                    # Get bot response
                    bot_response = get_bot_response(
                        last_user_message["content"]
                        if last_user_message["content"]
                        else "Saya mengirim gambar untuk Anda lihat",
                        st.session_state.messages[:-1],
                        None,  # Files are already processed and stored in the message
                    )

                    # Add bot response
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": bot_response,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Extract data immediately after bot response
                    newly_extracted_data = extract_data_from_conversation(st.session_state.messages)
                    export_data = extract_export_data_from_conversation(st.session_state.messages)

                    # Merge export data with business data
                    if export_data:
                        if "export_readiness" in export_data:
                            newly_extracted_data["export_readiness"] = export_data["export_readiness"]
                        if "assessment_history" in export_data:
                            newly_extracted_data["assessment_history"] = export_data["assessment_history"]

                    # Store extracted data for immediate use in this render cycle
                    st.session_state.latest_extracted_data = newly_extracted_data

                    # Update memory bot
                    update_memory_bot(newly_extracted_data)

                # Rerun to show bot response
                st.rerun()
            else:
                # If no messages, clear the flag and don't generate response
                st.session_state.generate_response = False

    with col2:
        show_memory_bot()


def show_memory_bot():
    """Display the memory bot sidebar"""
    st.markdown(
        """
    <div style="
        background: linear-gradient(180deg, #2c3e50, #34495e);
        color: white;
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(44, 62, 80, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    ">🧠 Memory Bot</div>
    """,
        unsafe_allow_html=True,
    )

    # Display memory_bot with enhanced export information
    # Always use the persistent memory_bot data
    memory_data = st.session_state.memory_bot

    # If there's latest extracted data available, use it for immediate preview
    if hasattr(st.session_state, 'latest_extracted_data') and st.session_state.latest_extracted_data:
        # Create a temporary merged view for display without modifying memory_bot
        display_data = memory_data.copy()
        for key, value in st.session_state.latest_extracted_data.items():
            if is_meaningful_value(value):
                if isinstance(value, dict) and key in display_data and isinstance(display_data[key], dict):
                    display_data[key].update(value)
                else:
                    display_data[key] = value
        memory_data = display_data

    # Show business profile section
    st.markdown("**👤 Business Profile**")
    business_data = {
        k: v
        for k, v in memory_data.items()
        if k not in ["export_readiness", "assessment_history"]
    }
    st.code(
        json.dumps(business_data, indent=2, ensure_ascii=False), language="json"
    )

    # Show export readiness section if data exists
    export_readiness = memory_data.get("export_readiness", {})
    if export_readiness and any(
        v != "Not specified" and v != [] for v in export_readiness.values()
    ):
        st.markdown("**🌍 Export Readiness Profile**")
        st.code(
            json.dumps(export_readiness, indent=2, ensure_ascii=False),
            language="json",
        )

    # Show assessment history if exists
    assessment_history = memory_data.get("assessment_history", [])
    if assessment_history:
        st.markdown("**📊 Assessment History**")
        st.code(
            json.dumps(assessment_history, indent=2, ensure_ascii=False),
            language="json",
        )

    # Add manual save button and download option
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save to Database", help="Save Memory Bot data to database"):
            if st.session_state.get('logged_in', False) and st.session_state.get('user'):
                from .auth import save_memory_bot_data
                user_id = st.session_state.user['id']
                success, message = save_memory_bot_data(user_id, st.session_state.memory_bot)
                if success:
                    st.success("✅ Memory Bot data saved!")
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("⚠️ Please log in to save data")

    with col2:
        # Download Memory Bot data as JSON
        memory_json = json.dumps(memory_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download JSON",
            data=memory_json,
            file_name=f"memory_bot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download Memory Bot data as JSON file"
        )

    if not memory_data or all(v == "Not specified" or v == {} or v == [] for k, v in memory_data.items() if k != "extraction_timestamp"):
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


def perform_chat_based_export_analysis(target_country: str, memory_data: dict) -> str:
    """Perform export readiness analysis through chat and return formatted response"""
    client = init_gemini()

    # Get product details from memory
    company_name = memory_data.get("company_name", "Not specified")
    product_name = memory_data.get("product_details", {}).get("name", "Product")
    product_category = memory_data.get("product_category", "Other")
    product_description = memory_data.get("product_details", {}).get(
        "description", "No description"
    )

    # Get production info
    capacity = memory_data.get("production_capacity", {})
    capacity_str = f"{capacity.get('amount', 0)} {capacity.get('unit', '')} per {capacity.get('timeframe', '')}"

    location = memory_data.get("production_location", {})
    location_str = (
        f"{location.get('city', '')}, {location.get('province', '')}, Indonesia"
    )

    # Country mapping for difficulty and market size
    countries_info = {
        "Amerika Serikat": {"difficulty": "High", "market_size": "Large"},
        "US": {"difficulty": "High", "market_size": "Large"},
        "Uni Eropa": {"difficulty": "High", "market_size": "Large"},
        "EU": {"difficulty": "High", "market_size": "Large"},
        "Jepang": {"difficulty": "High", "market_size": "Large"},
        "Japan": {"difficulty": "High", "market_size": "Large"},
        "Singapura": {"difficulty": "Medium", "market_size": "Medium"},
        "Singapore": {"difficulty": "Medium", "market_size": "Medium"},
        "Malaysia": {"difficulty": "Low", "market_size": "Medium"},
        "Australia": {"difficulty": "Medium", "market_size": "Large"},
        "Korea Selatan": {"difficulty": "Medium", "market_size": "Large"},
        "South Korea": {"difficulty": "Medium", "market_size": "Large"},
        "China": {"difficulty": "High", "market_size": "Very Large"},
        "Cina": {"difficulty": "High", "market_size": "Very Large"},
    }

    country_info = countries_info.get(
        target_country, {"difficulty": "Medium", "market_size": "Medium"}
    )

    try:
        # Prepare the prompt with actual data
        formatted_prompt = EXPORT_READINESS_PROMPT.format(
            target_country=target_country,
            company_name=company_name,
            product_name=product_name,
            product_category=product_category,
            product_description=product_description,
            production_capacity=capacity_str,
            production_location=location_str,
            market_difficulty=country_info["difficulty"],
            market_size=country_info["market_size"],
            required_certifications="Sertifikasi yang diperlukan akan dijelaskan dalam analisis",
        )

        # Send to Gemini for analysis
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", contents=formatted_prompt
        )

        # Parse the AI response
        ai_response = response.text.strip()

        # Try to parse as JSON first for structured data
        try:
            assessment_data = json.loads(
                ai_response.replace("```json", "").replace("```", "").strip()
            )

            # Convert to readable format for chat
            readable_response = f"""
🎯 **ANALISIS KESIAPAN EKSPOR - {target_country}**

📊 **Skor Keseluruhan: {assessment_data.get("overall_score", "N/A")}/100**

📈 **Breakdown per Kategori:**
• Kepatuhan Regulasi: {assessment_data.get("category_scores", {}).get("regulatory_compliance", "N/A")}/100
• Viabilitas Pasar: {assessment_data.get("category_scores", {}).get("market_viability", "N/A")}/100
• Kesiapan Dokumentasi: {assessment_data.get("category_scores", {}).get("documentation_readiness", "N/A")}/100
• Posisi Kompetitif: {assessment_data.get("category_scores", {}).get("competitive_positioning", "N/A")}/100

✅ **Rencana Aksi:**
{chr(10).join([f"{i + 1}. {item}" for i, item in enumerate(assessment_data.get("action_items", []))])}

⏱️ **Estimasi Waktu Persiapan:** {assessment_data.get("timeline_estimate", "Tidak ditentukan")}

🎯 **Insight Pasar:**
{assessment_data.get("market_insights", "Tidak tersedia")}

💪 **Keunggulan Kompetitif:**
{chr(10).join([f"• {adv}" for adv in assessment_data.get("competitive_advantages", [])])}

⚠️ **Tantangan Potensial:**
{chr(10).join([f"• {challenge}" for challenge in assessment_data.get("potential_challenges", [])])}

🏆 **Status Kesiapan:** {assessment_data.get("export_readiness_level", "Tidak dinilai")}

🤖 *Analisis ini dibuat menggunakan Gemini AI berdasarkan profil bisnis Anda.*
            """

            # Save assessment to memory bot
            if "assessment_history" not in st.session_state.memory_bot:
                st.session_state.memory_bot["assessment_history"] = []

            assessment_record = {
                "country": target_country,
                "score": assessment_data.get("overall_score", 0),
                "timestamp": datetime.now().isoformat(),
                "status": assessment_data.get("export_readiness_level", "Assessed"),
                "product": product_name,
                "category": product_category,
            }

            # Remove duplicate assessments for the same country
            st.session_state.memory_bot["assessment_history"] = [
                record
                for record in st.session_state.memory_bot["assessment_history"]
                if record.get("country") != target_country
            ]

            st.session_state.memory_bot["assessment_history"].append(assessment_record)

            # Auto-save updated Memory Bot data with assessment
            if st.session_state.get('logged_in', False) and st.session_state.get('user'):
                from .auth import save_memory_bot_data
                user_id = st.session_state.user['id']
                save_memory_bot_data(user_id, st.session_state.memory_bot)

            return readable_response

        except json.JSONDecodeError:
            # If not JSON, return the response as is with formatting
            return f"""
🎯 **ANALISIS KESIAPAN EKSPOR - {target_country}**

{ai_response}

🤖 *Analisis ini dibuat menggunakan Gemini AI berdasarkan profil bisnis Anda.*
            """

    except Exception as e:
        return f"""
❌ **Maaf, terjadi kesalahan saat menganalisis kesiapan ekspor:**

{str(e)}

💡 **Saran:** Coba lagi dalam beberapa saat atau pastikan koneksi internet Anda stabil.
        """


def check_profile_completeness(memory_data: dict) -> dict:
    """Check if user profile is 100% complete for mode switching"""
    required_fields = [
        memory_data.get("company_name", "Not specified") != "Not specified",
        memory_data.get("product_details", {}).get("name", "Not specified") != "Not specified",
        memory_data.get("product_category", "Not specified") != "Not specified",
        (lambda x: float(x) > 0 if str(x).replace('.', '').isdigit() else False)(memory_data.get("production_capacity", {}).get("amount", 0)),
        memory_data.get("production_location", {}).get("city", "Not specified") != "Not specified"
    ]

    completed = sum(required_fields)
    total = len(required_fields)

    missing_fields = []
    if not required_fields[0]:
        missing_fields.append("company_name")
    if not required_fields[1]:
        missing_fields.append("product_name")
    if not required_fields[2]:
        missing_fields.append("product_category")
    if not required_fields[3]:
        missing_fields.append("production_capacity")
    if not required_fields[4]:
        missing_fields.append("production_location")

    return {
        "percentage": (completed / total) * 100,
        "is_complete": completed == total,
        "missing_count": total - completed,
        "missing_fields": missing_fields,
        "completed_fields": completed,
        "total_fields": total
    }


def detect_export_analysis_request(
    user_input: str, memory_data: dict
) -> tuple[bool, str]:
    """Detect if user is requesting export analysis and extract target country"""
    user_input_lower = user_input.lower()

    # Keywords that trigger export analysis
    analysis_triggers = [
        "cek kesiapan ekspor",
        "analisis ekspor",
        "export readiness",
        "siap ekspor",
        "kesiapan ekspor",
        "analisis kesiapan",
    ]

    # Country keywords
    countries = {
        "amerika": "Amerika Serikat",
        "us": "Amerika Serikat",
        "usa": "Amerika Serikat",
        "eropa": "Uni Eropa",
        "eu": "Uni Eropa",
        "europe": "Uni Eropa",
        "jepang": "Jepang",
        "japan": "Jepang",
        "singapura": "Singapura",
        "singapore": "Singapura",
        "malaysia": "Malaysia",
        "australia": "Australia",
        "korea": "Korea Selatan",
        "south korea": "Korea Selatan",
        "china": "China",
        "cina": "China",
    }

    # Check if analysis is requested
    analysis_requested = any(
        trigger in user_input_lower for trigger in analysis_triggers
    )

    # Extract country if mentioned
    target_country = None
    for keyword, country_name in countries.items():
        if keyword in user_input_lower:
            target_country = country_name
            break

    # If analysis requested but no country specified, check memory for target countries
    if analysis_requested and not target_country:
        export_readiness = memory_data.get("export_readiness", {})
        target_countries = export_readiness.get("target_countries", [])
        if target_countries:
            target_country = target_countries[0]  # Use first target country

    return analysis_requested, target_country


def show_full_chat_page():
    """Display the complete standalone chat page"""
    # Initialize messages if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Track current page and reset chat if coming from a different page
    current_page = "chat"
    last_page = st.session_state.get("last_page", "")

    # Auto-reset chat if coming from a different page (not chat)
    if last_page != "" and last_page != "chat":
        st.session_state.messages = []
        st.session_state.user_id = str(uuid.uuid4())

    # Update last page tracker
    st.session_state.last_page = current_page

    # Check for export readiness trigger from sidebar
    has_export_trigger = st.session_state.get("trigger_export_readiness", False)

    # Handle export readiness trigger from sidebar
    if has_export_trigger:
        # Clear the trigger flag
        st.session_state.trigger_export_readiness = False

        # Clear any existing messages for fresh start with export readiness
        st.session_state.messages = []

        # Auto-add export readiness request message
        auto_message = {
            "role": "user",
            "content": "Cek kesiapan ekspor",
            "images": [],
            "timestamp": datetime.now().isoformat(),
        }
        st.session_state.messages.append(auto_message)

        # Set flag to generate bot response
        st.session_state.generate_response = True

    # Chat page header
    st.markdown(
        """
    <div style="
        background: linear-gradient(180deg, #2c3e50, #34495e);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(44, 62, 80, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    ">
        <h2 style="color: white; margin: 0; font-size: 1.5rem;">💬 Chat dengan Exporo</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.9rem;">
            Asisten AI untuk profiling bisnis ekspor Anda
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    show_chat_interface()
    show_chat_reset_button()
