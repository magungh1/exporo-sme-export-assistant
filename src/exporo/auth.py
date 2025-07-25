"""
Authentication module for Exporo SME Export Assistant
Handles user registration, login, and database operations
"""

import streamlit as st
import sqlite3
import hashlib
import time
import re
import json
from datetime import datetime
from .config import DATABASE_NAME, DEFAULT_EXTRACTED_DATA
import uuid


def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_bot_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            memory_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(first_name, last_name, email, phone, password):
    """Register a new user in the database"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (first_name, last_name, email, phone, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """,
            (first_name, last_name, email, phone, password_hash),
        )

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
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        password_hash = hash_password(password)

        cursor.execute(
            """
            SELECT id, first_name, last_name, email FROM users 
            WHERE email = ? AND password_hash = ?
        """,
            (email, password_hash),
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return True, {
                "id": user[0],
                "first_name": user[1],
                "last_name": user[2],
                "email": user[3],
            }
        else:
            return False, "Invalid email or password!"

    except Exception as e:
        return False, f"Login failed: {str(e)}"


def check_email_exists(email):
    """Check if email already exists"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        count = cursor.fetchone()[0]
        conn.close()

        return count > 0
    except Exception:
        return False


def get_user_count():
    """Get total number of registered users"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        return user_count
    except Exception:
        return 0


def save_memory_bot_data(user_id: int, memory_data: dict):
    """Save Memory Bot data to database"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # Convert memory data to JSON string
        memory_json = json.dumps(memory_data, ensure_ascii=False, default=str)
        
        # Use INSERT OR REPLACE for upsert behavior
        cursor.execute("""
            INSERT OR REPLACE INTO memory_bot_data (user_id, memory_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (user_id, memory_json))
        
        conn.commit()
        conn.close()
        return True, "Memory Bot data saved successfully!"
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return False, f"Failed to save Memory Bot data: {str(e)}"

def load_memory_bot_data(user_id: int) -> dict:
    """Load Memory Bot data from database"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memory_data FROM memory_bot_data WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Parse JSON data
            memory_data = json.loads(result[0])
            return memory_data
        else:
            # Return default data if no saved data found
            return DEFAULT_EXTRACTED_DATA.copy()
            
    except Exception as e:
        print(f"Error loading Memory Bot data: {e}")
        return DEFAULT_EXTRACTED_DATA.copy()

def init_auth_session_state():
    """Initialize authentication-related session state"""
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "user" not in st.session_state:
        st.session_state.user = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False


def reset_user_data():
    """Reset user-specific data on logout"""
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.extracted_data = DEFAULT_EXTRACTED_DATA.copy()
    st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()


def show_login_page():
    """Display the login page"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Left side illustration
        st.markdown('<div class="blue-gradient">', unsafe_allow_html=True)
        st.markdown(
            "**Selamat datang kembali! Masuk untuk melanjutkan perjalanan ekspor Anda**"
        )
        st.image(
            "https://via.placeholder.com/300x200/87CEEB/FFFFFF?text=Login+Illustration",
            caption="Welcome Back",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        st.markdown("## Login")
        st.markdown("Masuk ke akun Anda untuk mengakses platform Exporo")

        # Login form
        email = st.text_input("Email", placeholder="Masukkan email Anda")
        password = st.text_input(
            "Password", type="password", placeholder="Masukkan password Anda"
        )

        st.checkbox("Ingat saya")

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
                    st.session_state.page = "dashboard"
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error(result)

        st.markdown("---")
        st.markdown("Belum punya akun? Klik tombol **Sign Up** di atas")

        st.markdown("</div>", unsafe_allow_html=True)


def show_signup_page():
    """Display the signup page"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Left side illustration
        st.markdown('<div class="blue-gradient">', unsafe_allow_html=True)
        st.markdown(
            "**Bingung ekspor? Exporo bantu UMKM dari awal sampai tembus pasar global**"
        )
        st.image(
            "https://via.placeholder.com/300x200/87CEEB/FFFFFF?text=Export+Illustration",
            caption="Export Business Illustration",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Registration form
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        st.markdown("## Daftar")
        st.markdown(
            "Mari kita siapkan semuanya agar kamu bisa mengakses akun pribadimu."
        )

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

        password = st.text_input(
            "Password", type="password", placeholder="Minimal 6 karakter"
        )
        confirm_password = st.text_input(
            "Confirm Password", type="password", placeholder="Ulangi password"
        )

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
            if email and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
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
                    success, message = register_user(
                        first_name, last_name, email, phone, password
                    )

                if success:
                    st.success("Akun berhasil dibuat! Silakan login.")
                    time.sleep(2)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)

        st.markdown("---")
        st.markdown("Sudah punya akun? Klik tombol **Login** di atas")

        st.markdown("</div>", unsafe_allow_html=True)


def show_navigation():
    """Display navigation buttons"""
    # Header with navigation
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("### 🚀 Exporo - SME Export Assistant")

    # Navigation buttons
    if not st.session_state.logged_in:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col2:
            if st.button(
                "Login",
                type="secondary" if st.session_state.page != "login" else "primary",
            ):
                st.session_state.page = "login"
                st.rerun()
        with col4:
            if st.button(
                "Sign Up",
                type="secondary" if st.session_state.page != "signup" else "primary",
            ):
                st.session_state.page = "signup"
                st.rerun()
    else:
        # Move navigation to sidebar for logged-in users
        with st.sidebar:
            # Dark sidebar styling
            st.markdown(
                """
            <style>
            .sidebar .block-container {
                background: linear-gradient(180deg, #2c3e50, #34495e) !important;
                color: white;
                border-radius: 0;
                padding: 2rem 1rem !important;
            }
            .sidebar-header {
                background: linear-gradient(135deg, #2c3e50, #34495e);
                padding: 1.5rem 1rem;
                text-align: center;
                margin: -1rem -1rem 1rem -1rem;
                border-radius: 0;
            }
            .user-profile {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                margin-bottom: 1rem;
                padding: 1rem;
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
            }
            .nav-item {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                padding: 0.8rem 1rem;
                margin: 0.3rem 0;
                border-radius: 8px;
                color: white;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-item:hover {
                background: rgba(255,255,255,0.1);
            }
            .nav-item.active {
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
            }
            .nav-icon {
                font-size: 1.2rem;
                width: 24px;
            }
            .stButton > button {
                font-size: 0.85rem !important;
            }
            .stSidebar .stButton > button {
                background: linear-gradient(135deg, #4a6741, #5a7a51) !important;
                color: white !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
            }
            .stSidebar .stButton > button:hover {
                background: linear-gradient(135deg, #5a7a51, #6a8a61) !important;
            }
            .stMarkdown {
                margin-bottom: 0 !important;
                margin-top: 0 !important;
            }
            .stSidebar .stMarkdown {
                margin: 0 !important;
                padding: 0 !important;
            }
            .stSidebar [data-testid="stMarkdownContainer"] {
                margin: 0 !important;
                padding: 0 !important;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Header with logo
            st.markdown(
                """
            <div class="sidebar-header">
                <h3 style="color: white; margin: 0;">🚀 Exporo</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">SME Export Assistant</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # User profile and navigation combined to eliminate gaps
            st.markdown(
                f"""
            <!-- User profile section -->
            <div style="
                background: linear-gradient(135deg, rgba(52, 152, 219, 0.3), rgba(41, 128, 185, 0.3));
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 0.8rem;
                margin-bottom: 0;
                padding: 1rem;
                border-radius: 12px 12px 0 0;
                max-width: 100%;
                overflow: hidden;
            ">
                <div style="
                    width: 40px; 
                    height: 40px; 
                    background: linear-gradient(135deg, #3498db, #2980b9);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 1.2rem;
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
                    flex-shrink: 0;
                ">
                    {st.session_state.user["first_name"][0].upper()}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="color: white; font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{st.session_state.user["first_name"]} {st.session_state.user["last_name"]}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{st.session_state.user["email"]}</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button(
                "📊  Dashboard Progress",
                type="primary"
                if st.session_state.page == "dashboard"
                else "secondary",
                use_container_width=True,
                key="nav_dashboard",
            ):
                st.session_state.page = "dashboard"
                st.rerun()

            if st.button(
                "📋  Langkah Ekspor Saya",
                type="primary"
                if st.session_state.page == "langkah-ekspor"
                else "secondary",
                use_container_width=True,
                key="nav_langkah",
            ):
                st.session_state.page = "langkah-ekspor"
                st.rerun()

            if st.button(
                "👤  Profil Bisnis",
                type="primary"
                if st.session_state.page == "profil-bisnis"
                else "secondary",
                use_container_width=True,
                key="nav_profil",
            ):
                st.session_state.page = "profil-bisnis"
                st.rerun()

            if st.button(
                "📄  Persiapan Dokumen",
                type="primary" if st.session_state.page == "dokumen" else "secondary",
                use_container_width=True,
                key="nav_dokumen",
            ):
                st.session_state.page = "dokumen"
                st.rerun()

            if st.button(
                "⭐  Kualitas Produk Saya",
                type="primary" if st.session_state.page == "kualitas" else "secondary",
                use_container_width=True,
                key="nav_kualitas",
            ):
                st.session_state.page = "kualitas"
                st.rerun()

            if st.button(
                "🌍  Export Readiness Check",
                type="secondary",
                use_container_width=True,
                key="nav_export_check",
            ):
                # Set flags and redirect to chat with export readiness trigger
                st.session_state.page = "chat"
                st.session_state.trigger_export_readiness = True
                st.rerun()

            if st.button(
                "🌐  Cek Pasar Global",
                type="primary"
                if st.session_state.page == "pasar-global"
                else "secondary",
                use_container_width=True,
                key="nav_pasar",
            ):
                st.session_state.page = "pasar-global"
                st.rerun()

            if st.button(
                "💬  Diskusi dengan Exporo",
                type="primary" if st.session_state.page == "chat" else "secondary",
                use_container_width=True,
                key="nav_chat",
            ):
                st.session_state.page = "chat"
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(
                "🚪  Logout",
                type="secondary",
                use_container_width=True,
                key="nav_logout",
            ):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "login"
                reset_user_data()
                st.success("Logged out successfully!")
                st.rerun()


def show_coming_soon_page(feature_key):
    """Display styled coming soon page with feature-specific colors"""
    
    FEATURE_COLORS = {
        "langkah-ekspor": {
            "primary": "#3498db", 
            "secondary": "#2980b9",
            "icon": "📋", 
            "title": "Langkah Ekspor Saya",
            "description": "Panduan langkah demi langkah untuk mempersiapkan ekspor produk Anda ke pasar internasional."
        },
        "dokumen": {
            "primary": "#f39c12", 
            "secondary": "#e67e22", 
            "icon": "📄", 
            "title": "Persiapan Dokumen",
            "description": "Bantuan lengkap untuk menyiapkan semua dokumen yang diperlukan untuk ekspor."
        },
        "kualitas": {
            "primary": "#9b59b6", 
            "secondary": "#8e44ad",
            "icon": "⭐", 
            "title": "Kualitas Produk Saya",
            "description": "Analisis dan sertifikasi kualitas produk untuk memenuhi standar internasional."
        },
        "pasar-global": {
            "primary": "#1abc9c", 
            "secondary": "#16a085",
            "icon": "🌐", 
            "title": "Cek Pasar Global",
            "description": "Riset mendalam tentang peluang pasar dan kompetitor di berbagai negara tujuan ekspor."
        }
    }
    
    if feature_key not in FEATURE_COLORS:
        feature_key = "langkah-ekspor"  # Default fallback
    
    colors = FEATURE_COLORS[feature_key]
    
    # Styled coming soon page with gradient background
    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
        color: white;
        padding: 4rem 2rem;
        border-radius: 25px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        border: 1px solid rgba(255,255,255,0.3);
    ">
        <div style="font-size: 5rem; margin-bottom: 1.5rem; text-shadow: 0 4px 8px rgba(0,0,0,0.3);">{colors['icon']}</div>
        <h1 style="margin: 0 0 1rem 0; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{colors['title']}</h1>
        <h2 style="margin: 0 0 1.5rem 0; font-size: 1.8rem; font-weight: 300; color: rgba(255,255,255,0.9);">Coming Soon! 🚀</h2>
        <p style="font-size: 1.1rem; line-height: 1.6; margin: 0 0 2rem 0; color: rgba(255,255,255,0.95); max-width: 600px; margin-left: auto; margin-right: auto;">
            {colors['description']}
        </p>
        <div style="
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 2rem auto;
            max-width: 500px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        ">
            <p style="margin: 0; font-size: 1rem; color: rgba(255,255,255,0.9);">
                <strong>📅 Fitur ini sedang dalam pengembangan aktif</strong><br>
                Akan segera tersedia untuk membantu perjalanan ekspor Anda!
            </p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # Call to action section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💬 Kembali ke Chat dengan Exporo", type="primary", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()


def show_business_profile_page():
    """Display user's actual business profile from Memory Bot data"""
    
    # Get Memory Bot data
    memory_data = st.session_state.get("memory_bot", DEFAULT_EXTRACTED_DATA)
    
    # Red theme header matching the button
    st.markdown(
        """
    <div style="
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 3rem 2rem;
        border-radius: 25px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(231, 76, 60, 0.3);
        border: 1px solid rgba(255,255,255,0.3);
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem; text-shadow: 0 4px 8px rgba(0,0,0,0.3);">👤</div>
        <h1 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">Profil Bisnis Anda</h1>
        <p style="margin: 0; font-size: 1.2rem; color: rgba(255,255,255,0.9);">
            Informasi lengkap bisnis yang telah dikumpulkan melalui Exporo
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # Company Information Section
    st.markdown("### 🏢 Informasi Perusahaan")
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = memory_data.get("company_name", "Belum diisi")
        st.markdown(f"**Nama Perusahaan:** {company_name}")
        
        business_bg = memory_data.get("business_background", "Belum diisi")
        st.markdown(f"**Latar Belakang Bisnis:** {business_bg}")
    
    with col2:
        location = memory_data.get("production_location", {})
        city = location.get("city", "Belum diisi")
        province = location.get("province", "Belum diisi")
        st.markdown(f"**Lokasi Produksi:** {city}, {province}")
        
        language = memory_data.get("conversation_language", "Indonesian")
        st.markdown(f"**Bahasa Komunikasi:** {language}")
    
    st.markdown("---")
    
    # Product Details Section
    st.markdown("### 📦 Detail Produk")
    product_details = memory_data.get("product_details", {})
    
    col1, col2 = st.columns(2)
    with col1:
        product_name = product_details.get("name", "Belum diisi")
        st.markdown(f"**Nama Produk:** {product_name}")
        
        category = memory_data.get("product_category", "Belum diisi")
        st.markdown(f"**Kategori Produk:** {category}")
    
    with col2:
        description = product_details.get("description", "Belum diisi")
        st.markdown(f"**Deskripsi:** {description}")
        
        features = product_details.get("unique_features", "Belum diisi")
        st.markdown(f"**Keunggulan Unik:** {features}")
    
    st.markdown("---")
    
    # Production Information Section
    st.markdown("### 🏭 Informasi Produksi")
    capacity = memory_data.get("production_capacity", {})
    
    amount = capacity.get("amount", 0)
    unit = capacity.get("unit", "unit")
    timeframe = capacity.get("timeframe", "bulan")
    
    # Convert amount to int/float for comparison
    try:
        amount_num = float(amount) if amount else 0
    except (ValueError, TypeError):
        amount_num = 0
    
    capacity_text = f"{amount} {unit} per {timeframe}" if amount_num > 0 else "Belum diisi"
    st.markdown(f"**Kapasitas Produksi:** {capacity_text}")
    
    # Export Readiness Section (if available)
    export_readiness = memory_data.get("export_readiness", {})
    if export_readiness and any(v for v in export_readiness.values() if v not in ["Not specified", [], ""]):
        st.markdown("---")
        st.markdown("### 🌍 Kesiapan Ekspor")
        
        col1, col2 = st.columns(2)
        with col1:
            target_countries = export_readiness.get("target_countries", [])
            if target_countries:
                st.markdown(f"**Negara Target:** {', '.join(target_countries)}")
            
            experience = export_readiness.get("export_experience", "Belum diisi")
            if experience != "Not specified":
                st.markdown(f"**Pengalaman Ekspor:** {experience}")
        
        with col2:
            goals = export_readiness.get("export_goals", "Belum diisi")
            if goals != "Not specified":
                st.markdown(f"**Tujuan Ekspor:** {goals}")
            
            budget = export_readiness.get("budget_for_export", "Belum diisi")
            if budget != "Not specified":
                st.markdown(f"**Budget Ekspor:** {budget}")
    
    # Assessment History Section (if available)
    assessment_history = memory_data.get("assessment_history", [])
    if assessment_history:
        st.markdown("---")
        st.markdown("### 📊 Riwayat Analisis Kesiapan Ekspor")
        
        for i, assessment in enumerate(assessment_history, 1):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{i}. Negara:** {assessment.get('country', 'N/A')}")
            with col2:
                st.markdown(f"**Skor:** {assessment.get('score', 'N/A')}/100")
            with col3:
                st.markdown(f"**Status:** {assessment.get('status', 'N/A')}")
            with col4:
                timestamp = assessment.get('timestamp', '')
                if timestamp:
                    try:
                        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                        st.markdown(f"**Tanggal:** {formatted_date}")
                    except:
                        st.markdown(f"**Tanggal:** {timestamp[:10]}")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✏️ Edit Profil di Chat", type="primary", use_container_width=True):
                st.session_state.page = "chat"
                st.rerun()
        
        with col_b:
            # Download profile as JSON
            profile_json = json.dumps(memory_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Download JSON",
                data=profile_json,
                file_name=f"profil_bisnis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


def show_welcome_landing_page():
    """Display the welcome/landing page after login"""
    user_name = st.session_state.user["first_name"]

    # Welcome hero section
    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, #87CEEB, #B0E0E6);
        padding: 4rem 2rem;
        border-radius: 25px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 10px 40px rgba(135, 206, 235, 0.3);
        border: 1px solid rgba(255,255,255,0.3);
    ">
        <div style="margin-bottom: 2rem;">
            <img src="https://via.placeholder.com/200x250/4285F4/FFFFFF?text=Exporo" 
                 style="width: 150px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.2);">
        </div>
        <h1 style="color: white; margin: 0; font-size: 3rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            Selamat Datang, {user_name}! 🎉
        </h1>
        <p style="color: rgba(255,255,255,0.95); margin: 1rem 0; font-size: 1.3rem; line-height: 1.6;">
            <strong>Saya Exporo</strong>, asisten AI yang akan membantu Anda mempersiapkan bisnis untuk ekspor ke pasar global!
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Features section
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
            <h3 style="color: #2c3e50; margin-bottom: 1rem;">Chat dengan AI</h3>
            <p style="color: #7f8c8d; line-height: 1.5;">
                Berbincang natural dalam Bahasa Indonesia untuk mengumpulkan profil bisnis Anda
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
            <h3 style="color: #2c3e50; margin-bottom: 1rem;">Memory Bot</h3>
            <p style="color: #7f8c8d; line-height: 1.5;">
                AI yang mengingat dan mengorganisir informasi bisnis Anda secara otomatis
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
            height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #2c3e50; margin-bottom: 1rem;">Export Profil</h3>
            <p style="color: #7f8c8d; line-height: 1.5;">
                Download profil bisnis lengkap dalam format JSON untuk keperluan ekspor
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Call to action
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
        <div style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            border: 1px solid rgba(255,255,255,0.2);
        ">
            <h3 style="color: white; margin-bottom: 1rem;">Siap Memulai Perjalanan Ekspor?</h3>
            <p style="color: rgba(255,255,255,0.9); margin-bottom: 2rem;">
                Klik tombol di bawah untuk mulai berbincang dengan Exporo dan bangun profil bisnis Anda!
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button(
            "🚀 Mulai Chat dengan Exporo", type="primary", use_container_width=True
        ):
            st.session_state.page = "chat"
            st.rerun()
