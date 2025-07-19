"""
Authentication module for Exporo SME Export Assistant
Handles user registration, login, and database operations
"""

import streamlit as st
import sqlite3
import hashlib
import time
import re
from config import DATABASE_NAME, DEFAULT_EXTRACTED_DATA
import uuid
from datetime import datetime

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DATABASE_NAME)
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
        conn = sqlite3.connect(DATABASE_NAME)
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
        conn = sqlite3.connect(DATABASE_NAME)
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
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except:
        return False

def get_user_count():
    """Get total number of registered users"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        return user_count
    except:
        return 0

def init_auth_session_state():
    """Initialize authentication-related session state"""
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'logged_in' not in st.session_state:
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

def show_signup_page():
    """Display the signup page"""
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
            if st.button("Login", type="secondary" if st.session_state.page != 'login' else "primary"):
                st.session_state.page = 'login'
                st.rerun()
        with col4:
            if st.button("Sign Up", type="secondary" if st.session_state.page != 'signup' else "primary"):
                st.session_state.page = 'signup'
                st.rerun()
    else:
        # Move navigation to sidebar for logged-in users
        with st.sidebar:
            # Dark sidebar styling
            st.markdown("""
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
            """, unsafe_allow_html=True)
            
            # Header with logo
            st.markdown("""
            <div class="sidebar-header">
                <h3 style="color: white; margin: 0;">🚀 Exporo</h3>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">SME Export Assistant</p>
            </div>
            """, unsafe_allow_html=True)
            
            # User profile and navigation combined to eliminate gaps
            st.markdown(f"""
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
                    {st.session_state.user['first_name'][0].upper()}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="color: white; font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{st.session_state.user['first_name']} {st.session_state.user['last_name']}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{st.session_state.user['email']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📋  Langkah Ekspor Saya", 
                        type="primary" if st.session_state.page == 'langkah-ekspor' else "secondary", 
                        use_container_width=True,
                        key="nav_langkah"):
                st.session_state.page = 'langkah-ekspor'
                st.info("📋 Langkah Ekspor Saya - Coming Soon!")
                
            if st.button("👤  Profil Bisnis", 
                        type="primary" if st.session_state.page == 'profil-bisnis' else "secondary", 
                        use_container_width=True,
                        key="nav_profil"):
                st.session_state.page = 'profil-bisnis'
                st.info("👤 Profil Bisnis - Coming Soon!")
                
            if st.button("📄  Persiapan Dokumen", 
                        type="primary" if st.session_state.page == 'dokumen' else "secondary", 
                        use_container_width=True,
                        key="nav_dokumen"):
                st.session_state.page = 'dokumen'
                st.info("📄 Persiapan Dokumen - Coming Soon!")
                
            if st.button("⭐  Kualitas Produk Saya", 
                        type="primary" if st.session_state.page == 'kualitas' else "secondary", 
                        use_container_width=True,
                        key="nav_kualitas"):
                st.session_state.page = 'kualitas'
                st.info("⭐ Kualitas Produk Saya - Coming Soon!")
                
            if st.button("🌍  Cek Pasar Global", 
                        type="primary" if st.session_state.page == 'pasar-global' else "secondary", 
                        use_container_width=True,
                        key="nav_pasar"):
                st.session_state.page = 'pasar-global'
                st.info("🌍 Cek Pasar Global - Coming Soon!")
                
            if st.button("💬  Diskusi dengan Exporo", 
                        type="primary" if st.session_state.page == 'chat' else "secondary", 
                        use_container_width=True,
                        key="nav_chat"):
                st.session_state.page = 'chat'
                st.rerun()
                
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚪  Logout", 
                        type="secondary", 
                        use_container_width=True,
                        key="nav_logout"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = 'login'
                reset_user_data()
                st.success("Logged out successfully!")
                st.rerun()

def show_welcome_landing_page():
    """Display the welcome/landing page after login"""
    user_name = st.session_state.user['first_name']
    
    # Welcome hero section
    st.markdown(f"""
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
    """, unsafe_allow_html=True)
    
    # Features section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
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
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
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
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
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
        """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
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
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Mulai Chat dengan Exporo", type="primary", use_container_width=True):
            st.session_state.page = 'chat'
            st.rerun()