import streamlit as st
import sqlite3
import hashlib
import time
import re
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Langkah Ekspor",
    page_icon="✈️",
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

# Custom CSS for styling
st.markdown("""
<style>
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
    
    .character-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .blue-gradient {
        background: linear-gradient(135deg, #87CEEB, #4285F4);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1rem 0;
    }
    
    .nav-buttons {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 1rem 0;
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

# Header with navigation
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### 🏢 Langkah Ekspor")

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
            st.success("Logged out successfully!")
            st.rerun()

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
        st.markdown("Masuk ke akun Anda untuk mengakses platform Langkah Ekspor")
        
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
                    st.session_state.page = 'welcome'
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error(result)
        
        st.markdown("---")
        st.markdown("Belum punya akun? Klik tombol **Sign Up** di atas")
        
        # Social login options
        st.markdown("**Atau masuk dengan**")
        col_fb, col_google, col_apple = st.columns(3)
        with col_fb:
            if st.button("📘", use_container_width=True):
                st.info("Facebook login segera tersedia")
        with col_google:
            if st.button("🔍", use_container_width=True):
                st.info("Google login segera tersedia")
        with col_apple:
            if st.button("🍎", use_container_width=True):
                st.info("Apple login segera tersedia")
                
        st.markdown('</div>', unsafe_allow_html=True)

# SIGNUP PAGE
elif st.session_state.page == 'signup':
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Left side illustration
        st.markdown('<div class="blue-gradient">', unsafe_allow_html=True)
        st.markdown("**Bingung ekspor? Langkah Ekspor bantu UMKM dari awal sampai tembus pasar global**")
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
        
        # Social login options
        st.markdown("**Atau daftar dengan**")
        col_fb, col_google, col_apple = st.columns(3)
        with col_fb:
            if st.button("📘 Facebook", use_container_width=True):
                st.info("Facebook signup segera tersedia")
        with col_google:
            if st.button("🔍 Google", use_container_width=True):
                st.info("Google signup segera tersedia")
        with col_apple:
            if st.button("🍎 Apple", use_container_width=True):
                st.info("Apple signup segera tersedia")
                
        st.markdown('</div>', unsafe_allow_html=True)

# WELCOME PAGE (for logged in users)
elif st.session_state.page == 'welcome' and st.session_state.logged_in:
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
        
        # Character illustration
        st.markdown('<div class="character-container">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/200x250/4285F4/FFFFFF?text=Ekspor+Character", 
                width=200, caption="Ekspor Assistant")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Welcome message
        user_name = st.session_state.user['first_name']
        st.markdown(f"**Hai {user_name}! Aku Eksporo. Siap bantu ekspor bisnismu ke dunia!**")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main welcome content
        st.markdown("# Halo Selamat Datang di Langkah Ekspor! 🎉")
        
        st.markdown("**Senang bertemu denganmu di sini.**")
        
        st.markdown(f"""
        Halo **{user_name}**! Saya **Eksporo**, yang akan membimbing setiap langkah ekspor produk Anda ke luar negeri mulai 
        dari cek kesiapan, urus dokumen, sampai strategi penjualan global.
        
        Sebelum memulai, saya perlu mengenal sedikit tentang Anda. Harap jawab beberapa pertanyaan 
        sehingga saya dapat menilai kesiapan Anda dan memandu Anda secara personal yaa
        """)
        
        # Start button
        if st.button("Mulai ➜", type="primary", use_container_width=True):
            st.success("Selamat! Anda siap memulai perjalanan ekspor!")
            st.balloons()
            
            # Show user info
            with st.expander("Info Akun Anda"):
                st.write(f"**Nama:** {st.session_state.user['first_name']} {st.session_state.user['last_name']}")
                st.write(f"**Email:** {st.session_state.user['email']}")
                st.write(f"**User ID:** {st.session_state.user['id']}")

# Redirect to login if not logged in but trying to access protected pages
else:
    st.session_state.page = 'login'
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
        
        st.markdown(f"© 2024 Langkah Ekspor - Platform UMKM untuk Ekspor Global | Total Users: {user_count}")
    except:
        st.markdown("© 2024 Langkah Ekspor - Platform UMKM untuk Ekspor Global")
else:
    st.markdown("© 2024 Langkah Ekspor - Platform UMKM untuk Ekspor Global")