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
                reset_user_data()
                st.success("Logged out successfully!")
                st.rerun()