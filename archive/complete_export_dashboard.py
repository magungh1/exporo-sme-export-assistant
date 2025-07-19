import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import uuid
import base64
import sqlite3
import pandas as pd
import hashlib
from google import genai
from google.genai import types
import io
import os
from typing import Dict, List, Optional, Tuple

# Page configuration
st.set_page_config(
    page_title="Complete Export Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DATABASE_PATH = "export_dashboard.db"

class DatabaseManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                password_hash TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Business profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_profiles (
                profile_id TEXT PRIMARY KEY,
                user_id TEXT,
                company_name TEXT,
                business_background TEXT,
                production_location_city TEXT,
                production_location_province TEXT,
                production_capacity_amount INTEGER,
                production_capacity_unit TEXT,
                production_capacity_timeframe TEXT,
                completion_percentage REAL DEFAULT 0,
                last_updated TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Product assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_assessments (
                assessment_id TEXT PRIMARY KEY,
                user_id TEXT,
                product_type TEXT,
                product_name TEXT,
                description TEXT,
                dimensions TEXT,
                target_market TEXT,
                product_category TEXT,
                primary_materials TEXT,
                secondary_materials TEXT,
                finishing_materials TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Certifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certifications (
                cert_id TEXT PRIMARY KEY,
                user_id TEXT,
                certificate_name TEXT,
                requirement_level TEXT,
                target_market TEXT,
                status TEXT DEFAULT 'pending',
                estimated_time TEXT,
                estimated_cost REAL,
                certification_body TEXT,
                due_date DATE,
                obtained_date DATE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                user_id TEXT,
                document_type TEXT,
                document_name TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'pending',
                uploaded_at TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id TEXT PRIMARY KEY,
                user_id TEXT,
                consultation_type TEXT,
                messages TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Export progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS export_progress (
                progress_id TEXT PRIMARY KEY,
                user_id TEXT,
                step_name TEXT,
                step_category TEXT,
                status TEXT DEFAULT 'pending',
                completion_percentage REAL DEFAULT 0,
                completed_at TIMESTAMP,
                step_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Market analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_analysis (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT,
                target_country TEXT,
                product_category TEXT,
                demand_score REAL,
                requirements TEXT,
                recommendations TEXT,
                analyzed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, email: str, name: str, phone: str, password: str) -> str:
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (user_id, email, name, phone, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, email, name, phone, password_hash, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        return user_id
    
    def authenticate_user(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and return user_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('''
            SELECT user_id FROM users WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, bp.company_name, bp.completion_percentage
            FROM users u
            LEFT JOIN business_profiles bp ON u.user_id = bp.user_id
            WHERE u.user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, result))
        return None
    
    def save_business_profile(self, user_id: str, profile_data: Dict):
        """Save business profile data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        profile_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR REPLACE INTO business_profiles (
                profile_id, user_id, company_name, business_background,
                production_location_city, production_location_province,
                production_capacity_amount, production_capacity_unit,
                production_capacity_timeframe, completion_percentage, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_id, user_id, profile_data.get('company_name'),
            profile_data.get('business_background'),
            profile_data.get('production_location', {}).get('city'),
            profile_data.get('production_location', {}).get('province'),
            profile_data.get('production_capacity', {}).get('amount'),
            profile_data.get('production_capacity', {}).get('unit'),
            profile_data.get('production_capacity', {}).get('timeframe'),
            profile_data.get('completion_percentage', 0),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def save_product_assessment(self, user_id: str, assessment_data: Dict):
        """Save product assessment data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        assessment_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR REPLACE INTO product_assessments (
                assessment_id, user_id, product_type, product_name,
                description, dimensions, target_market, product_category,
                primary_materials, secondary_materials, finishing_materials, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assessment_id, user_id,
            assessment_data.get('product_assessment', {}).get('product_type'),
            assessment_data.get('product_assessment', {}).get('product_name'),
            assessment_data.get('product_assessment', {}).get('description'),
            assessment_data.get('product_assessment', {}).get('dimensions'),
            assessment_data.get('product_assessment', {}).get('target_market'),
            assessment_data.get('product_assessment', {}).get('product_category'),
            json.dumps(assessment_data.get('raw_materials', {}).get('primary_materials', [])),
            json.dumps(assessment_data.get('raw_materials', {}).get('secondary_materials', [])),
            json.dumps(assessment_data.get('raw_materials', {}).get('finishing_materials', {})),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def get_export_progress(self, user_id: str) -> Dict:
        """Calculate export progress for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get business profile completion
        cursor.execute('''
            SELECT completion_percentage FROM business_profiles WHERE user_id = ?
        ''', (user_id,))
        business_completion = cursor.fetchone()
        business_completion = business_completion[0] if business_completion else 0
        
        # Get product assessment completion
        cursor.execute('''
            SELECT COUNT(*) FROM product_assessments WHERE user_id = ?
        ''', (user_id,))
        product_count = cursor.fetchone()[0]
        product_completion = min(product_count * 30, 100)  # 30% per product, max 100%
        
        # Get document completion
        cursor.execute('''
            SELECT COUNT(*) FROM documents WHERE user_id = ? AND status = 'approved'
        ''', (user_id,))
        document_count = cursor.fetchone()[0]
        document_completion = min(document_count * 25, 100)  # 25% per document, max 100%
        
        # Get certification completion
        cursor.execute('''
            SELECT COUNT(*) FROM certifications WHERE user_id = ? AND status = 'obtained'
        ''', (user_id,))
        cert_count = cursor.fetchone()[0]
        cert_completion = min(cert_count * 20, 100)  # 20% per certification, max 100%
        
        # Calculate overall progress
        overall_progress = (
            business_completion * 0.3 +
            product_completion * 0.25 +
            document_completion * 0.25 +
            cert_completion * 0.2
        )
        
        conn.close()
        
        return {
            'overall_progress': overall_progress,
            'business_completion': business_completion,
            'product_completion': product_completion,
            'document_completion': document_completion,
            'certification_completion': cert_completion
        }
    
    def get_required_certifications(self, user_id: str) -> List[Dict]:
        """Get required certifications for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM certifications WHERE user_id = ?
        ''', (user_id,))
        
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_market_recommendations(self, user_id: str) -> List[Dict]:
        """Get market recommendations for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM market_analysis WHERE user_id = ? ORDER BY demand_score DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in results]

# Initialize database
db = DatabaseManager()

# Initialize Gemini client
@st.cache_resource
def init_gemini():
    api_key = "AIzaSyBNlRT5T_YkJ8QJBdVm6K54GQ1RqrlFJQ8"
    return genai.Client(api_key=api_key)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'messages' not in st.session_state:
    st.session_state.messages = []

# CSS styling
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    .progress-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .completed-step {
        color: #28a745;
        font-weight: bold;
    }
    .pending-step {
        color: #6c757d;
    }
    .in-progress-step {
        color: #ffc107;
        font-weight: bold;
    }
    .sidebar-nav {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        cursor: pointer;
    }
    .sidebar-nav:hover {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def login_page():
    """Login page"""
    st.title("🚀 Export Dashboard - Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if email and password:
                user_id = db.authenticate_user(email, password)
                if user_id:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Create new account")
        reg_email = st.text_input("Email", key="reg_email")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_phone = st.text_input("Phone Number", key="reg_phone")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register"):
            if all([reg_email, reg_name, reg_phone, reg_password, reg_confirm]):
                if reg_password == reg_confirm:
                    try:
                        user_id = db.create_user(reg_email, reg_name, reg_phone, reg_password)
                        st.success("Account created successfully! Please login.")
                    except Exception as e:
                        st.error("Email already exists or registration failed")
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill in all fields")

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        # User profile
        user_profile = db.get_user_profile(st.session_state.user_id)
        if user_profile:
            st.markdown("### 👤 User Profile")
            st.write(f"**Name:** {user_profile.get('name', 'N/A')}")
            st.write(f"**Email:** {user_profile.get('email', 'N/A')}")
            if user_profile.get('company_name'):
                st.write(f"**Company:** {user_profile.get('company_name')}")
        
        st.markdown("---")
        
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        if st.button("📊 Dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("👤 Business Profile"):
            st.session_state.current_page = 'business_profile'
            st.rerun()
        
        if st.button("📦 Product Assessment"):
            st.session_state.current_page = 'product_assessment'
            st.rerun()
        
        if st.button("📄 Documents"):
            st.session_state.current_page = 'documents'
            st.rerun()
        
        if st.button("🎯 Market Analysis"):
            st.session_state.current_page = 'market_analysis'
            st.rerun()
        
        if st.button("✅ Certifications"):
            st.session_state.current_page = 'certifications'
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.current_page = 'dashboard'
            st.session_state.messages = []
            st.rerun()

def render_dashboard():
    """Main dashboard page"""
    st.title("📊 Export Dashboard")
    
    # Get user progress
    progress_data = db.get_export_progress(st.session_state.user_id)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Progress", f"{progress_data['overall_progress']:.1f}%")
    
    with col2:
        st.metric("Business Profile", f"{progress_data['business_completion']:.1f}%")
    
    with col3:
        st.metric("Product Assessment", f"{progress_data['product_completion']:.1f}%")
    
    with col4:
        st.metric("Documents", f"{progress_data['document_completion']:.1f}%")
    
    # Progress visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Export Readiness Progress")
        
        # Create progress chart
        categories = ['Business Profile', 'Product Assessment', 'Documents', 'Certifications']
        values = [
            progress_data['business_completion'],
            progress_data['product_completion'],
            progress_data['document_completion'],
            progress_data['certification_completion']
        ]
        
        fig = px.bar(
            x=categories,
            y=values,
            title="Export Readiness by Category",
            color=values,
            color_continuous_scale="viridis"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Overall Readiness")
        
        # Create donut chart
        fig = go.Figure(data=[go.Pie(
            values=[progress_data['overall_progress'], 100 - progress_data['overall_progress']],
            hole=.7,
            marker_colors=['#28a745', '#e0e0e0'],
            textinfo='none',
            hoverinfo='skip'
        )])
        
        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(l=0, r=0, t=0, b=0),
            annotations=[dict(
                text=f'{progress_data["overall_progress"]:.1f}%',
                x=0.5, y=0.5,
                font_size=24,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Action items and recommendations
    st.markdown("---")
    st.markdown("### 🎯 Next Steps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Action Items")
        
        # Determine next actions based on progress
        if progress_data['business_completion'] < 50:
            st.markdown("🔸 **Complete Business Profile** - Add company details and production information")
        
        if progress_data['product_completion'] < 50:
            st.markdown("🔸 **Product Assessment** - Analyze your products and identify certification needs")
        
        if progress_data['document_completion'] < 50:
            st.markdown("🔸 **Document Upload** - Upload required export documents")
        
        if progress_data['certification_completion'] < 50:
            st.markdown("🔸 **Certifications** - Obtain required certifications for your target markets")
    
    with col2:
        st.markdown("#### 🌍 Market Recommendations")
        
        # Get market recommendations
        recommendations = db.get_market_recommendations(st.session_state.user_id)
        
        if recommendations:
            for rec in recommendations[:3]:  # Show top 3
                st.markdown(f"🔸 **{rec['target_country']}** - Demand Score: {rec['demand_score']:.1f}")
        else:
            st.markdown("Complete product assessment to get market recommendations")
    
    # Recent activity
    st.markdown("---")
    st.markdown("### 📊 Recent Activity")
    
    # Show recent progress updates
    activity_data = [
        {"date": "2025-01-08", "action": "Business profile updated", "status": "completed"},
        {"date": "2025-01-07", "action": "Product assessment started", "status": "in_progress"},
        {"date": "2025-01-06", "action": "Account created", "status": "completed"}
    ]
    
    for activity in activity_data:
        status_color = "🟢" if activity["status"] == "completed" else "🟡"
        st.markdown(f"{status_color} **{activity['date']}** - {activity['action']}")

def render_business_profile():
    """Business profile page with chat interface"""
    st.title("👤 Business Profile")
    
    # Get existing profile data
    user_profile = db.get_user_profile(st.session_state.user_id)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Business Profile Chat")
        
        # Chat interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Tell me about your business..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get AI response (simplified for demo)
            response = "Thank you for the information! Can you tell me more about your production capacity?"
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    with col2:
        st.subheader("📊 Profile Summary")
        
        if user_profile and user_profile.get('company_name'):
            st.markdown(f"**Company:** {user_profile.get('company_name')}")
            st.markdown(f"**Completion:** {user_profile.get('completion_percentage', 0):.1f}%")
        else:
            st.markdown("*No profile data yet. Start chatting to build your profile!*")
        
        # Quick form for manual entry
        st.markdown("---")
        st.subheader("📝 Quick Update")
        
        with st.form("profile_form"):
            company_name = st.text_input("Company Name", value=user_profile.get('company_name', '') if user_profile else '')
            city = st.text_input("City", value=user_profile.get('production_location_city', '') if user_profile else '')
            province = st.text_input("Province", value=user_profile.get('production_location_province', '') if user_profile else '')
            
            submitted = st.form_submit_button("Update Profile")
            
            if submitted and company_name:
                profile_data = {
                    'company_name': company_name,
                    'production_location': {'city': city, 'province': province},
                    'completion_percentage': 50.0  # Basic completion
                }
                
                db.save_business_profile(st.session_state.user_id, profile_data)
                st.success("Profile updated successfully!")
                st.rerun()

def render_product_assessment():
    """Product assessment page"""
    st.title("📦 Product Assessment")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Product Information")
        
        with st.form("product_form"):
            product_name = st.text_input("Product Name")
            product_type = st.selectbox("Product Type", ["Furniture", "Textile", "Food", "Electronics", "Other"])
            description = st.text_area("Product Description")
            target_market = st.selectbox("Target Market", ["USA", "EU", "Singapore", "Japan", "Other"])
            
            submitted = st.form_submit_button("Save Product Assessment")
            
            if submitted and product_name:
                assessment_data = {
                    'product_assessment': {
                        'product_name': product_name,
                        'product_type': product_type,
                        'description': description,
                        'target_market': target_market
                    }
                }
                
                db.save_product_assessment(st.session_state.user_id, assessment_data)
                st.success("Product assessment saved successfully!")
                st.rerun()
    
    with col2:
        st.subheader("🎯 Assessment Results")
        
        # Show certification requirements based on product type
        st.markdown("#### Required Certifications")
        
        cert_requirements = {
            "Furniture": ["SVLK", "V-Legal", "Fumigation Certificate"],
            "Textile": ["OEKO-TEX", "REACH Compliance", "CE Marking"],
            "Food": ["HACCP", "Halal Certificate", "Organic Certificate"],
            "Electronics": ["CE Marking", "FCC Certification", "RoHS Compliance"]
        }
        
        for product_type, certs in cert_requirements.items():
            with st.expander(f"{product_type} Certifications"):
                for cert in certs:
                    st.markdown(f"• {cert}")

def render_documents():
    """Document management page"""
    st.title("📄 Document Management")
    
    # Document upload
    st.subheader("📤 Upload Documents")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'doc', 'docx', 'jpg', 'png'],
        help="Upload export-related documents"
    )
    
    if uploaded_file is not None:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # In a real implementation, you would save the file and update the database
        # For now, we'll just show a success message
    
    # Document checklist
    st.markdown("---")
    st.subheader("📋 Document Checklist")
    
    required_docs = [
        {"name": "Company Registration", "status": "pending", "description": "Official company registration certificate"},
        {"name": "Product Catalog", "status": "completed", "description": "Detailed product specifications and images"},
        {"name": "Export License", "status": "pending", "description": "Government export permit"},
        {"name": "Certificate of Origin", "status": "pending", "description": "Product origin verification"},
        {"name": "Quality Certificates", "status": "in_progress", "description": "Product quality and safety certifications"}
    ]
    
    for doc in required_docs:
        col1, col2, col3 = st.columns([3, 1, 4])
        
        with col1:
            st.markdown(f"**{doc['name']}**")
        
        with col2:
            if doc['status'] == 'completed':
                st.markdown("✅ Complete")
            elif doc['status'] == 'in_progress':
                st.markdown("🟡 In Progress")
            else:
                st.markdown("⭕ Pending")
        
        with col3:
            st.markdown(f"*{doc['description']}*")

def render_market_analysis():
    """Market analysis page"""
    st.title("🌍 Market Analysis")
    
    # Country selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Select Target Markets")
        
        countries = st.multiselect(
            "Choose target countries",
            ["USA", "Germany", "Japan", "Singapore", "Australia", "United Kingdom", "Netherlands"],
            default=["USA", "Singapore"]
        )
        
        if st.button("Analyze Markets"):
            st.success("Market analysis updated!")
    
    with col2:
        st.subheader("📊 Market Insights")
        
        # Sample market data
        market_data = {
            "USA": {"demand": 85, "competition": "High", "entry_cost": "$15,000"},
            "Singapore": {"demand": 92, "competition": "Medium", "entry_cost": "$8,000"},
            "Germany": {"demand": 78, "competition": "High", "entry_cost": "$12,000"}
        }
        
        for country, data in market_data.items():
            if country in countries:
                with st.expander(f"🏳️ {country} Market Analysis"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Demand Score", f"{data['demand']}/100")
                    
                    with col_b:
                        st.metric("Competition", data['competition'])
                    
                    with col_c:
                        st.metric("Entry Cost", data['entry_cost'])
    
    # Market trends
    st.markdown("---")
    st.subheader("📈 Market Trends")
    
    # Sample trend data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
    demand_data = [65, 68, 72, 75, 78, 82, 85, 88, 90, 87, 89, 92]
    
    fig = px.line(
        x=dates,
        y=demand_data,
        title="Market Demand Trend",
        labels={"x": "Date", "y": "Demand Score"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_certifications():
    """Certifications tracking page"""
    st.title("✅ Certifications")
    
    # Get required certifications
    certifications = db.get_required_certifications(st.session_state.user_id)
    
    # Add new certification
    st.subheader("➕ Add New Certification")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cert_name = st.text_input("Certification Name")
    
    with col2:
        cert_level = st.selectbox("Requirement Level", ["Mandatory", "Recommended", "Optional"])
    
    with col3:
        target_market = st.selectbox("Target Market", ["USA", "EU", "Singapore", "Japan", "Global"])
    
    if st.button("Add Certification") and cert_name:
        # In a real implementation, you would save this to the database
        st.success(f"Certification '{cert_name}' added successfully!")
    
    # Certification progress
    st.markdown("---")
    st.subheader("📊 Certification Progress")
    
    # Sample certification data
    cert_data = [
        {"name": "SVLK", "status": "obtained", "progress": 100, "due_date": "2025-01-15"},
        {"name": "V-Legal", "status": "in_progress", "progress": 65, "due_date": "2025-02-01"},
        {"name": "Fumigation Certificate", "status": "pending", "progress": 0, "due_date": "2025-02-15"},
        {"name": "CE Marking", "status": "not_required", "progress": 0, "due_date": "N/A"}
    ]
    
    for cert in cert_data:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"**{cert['name']}**")
        
        with col2:
            if cert['status'] == 'obtained':
                st.markdown("✅ Obtained")
            elif cert['status'] == 'in_progress':
                st.markdown("🟡 In Progress")
            elif cert['status'] == 'pending':
                st.markdown("⭕ Pending")
            else:
                st.markdown("➖ Not Required")
        
        with col3:
            if cert['status'] != 'not_required':
                st.progress(cert['progress'] / 100)
        
        with col4:
            st.markdown(f"Due: {cert['due_date']}")

# Main application logic
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        render_sidebar()
        
        # Route to appropriate page
        if st.session_state.current_page == 'dashboard':
            render_dashboard()
        elif st.session_state.current_page == 'business_profile':
            render_business_profile()
        elif st.session_state.current_page == 'product_assessment':
            render_product_assessment()
        elif st.session_state.current_page == 'documents':
            render_documents()
        elif st.session_state.current_page == 'market_analysis':
            render_market_analysis()
        elif st.session_state.current_page == 'certifications':
            render_certifications()
        else:
            render_dashboard()

if __name__ == "__main__":
    main()