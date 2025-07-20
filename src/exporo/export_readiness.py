"""
Export Readiness Assessment module for Exporo SME Export Assistant
Handles comprehensive export readiness analysis including country requirements,
certification checking, and product compliance assessment
"""

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from PIL import Image
import base64
import io

# For text embeddings and FAISS (will be implemented in Phase 2)
try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    st.warning("⚠️ Text embedding libraries not available. Some features may be limited.")

from .config import GEMINI_API_KEY, DEFAULT_EXTRACTED_DATA, EXPORT_READINESS_PROMPT
from .chat import init_gemini

# Export Readiness Configuration
SUPPORTED_COUNTRIES = [
    {"name": "United States", "code": "US", "flag": "🇺🇸", "market_size": "Large", "difficulty": "High"},
    {"name": "European Union", "code": "EU", "flag": "🇪🇺", "market_size": "Large", "difficulty": "High"},
    {"name": "Japan", "code": "JP", "flag": "🇯🇵", "market_size": "Large", "difficulty": "High"},
    {"name": "Singapore", "code": "SG", "flag": "🇸🇬", "market_size": "Medium", "difficulty": "Medium"},
    {"name": "Malaysia", "code": "MY", "flag": "🇲🇾", "market_size": "Medium", "difficulty": "Low"},
    {"name": "Australia", "code": "AU", "flag": "🇦🇺", "market_size": "Large", "difficulty": "Medium"},
    {"name": "South Korea", "code": "KR", "flag": "🇰🇷", "market_size": "Large", "difficulty": "Medium"},
    {"name": "China", "code": "CN", "flag": "🇨🇳", "market_size": "Very Large", "difficulty": "High"}
]

PRODUCT_CATEGORIES = [
    "Food & Beverages", "Textiles & Apparel", "Furniture", 
    "Electronics", "Handicrafts", "Agricultural Products", 
    "Chemicals", "Automotive Parts", "Beauty & Personal Care"
]

# Sample certification requirements (will be expanded with FAISS in Phase 2)
CERTIFICATION_REQUIREMENTS = {
    "US": {
        "Food & Beverages": ["FDA Registration", "Food Safety Modernization Act (FSMA)", "Nutritional Labeling"],
        "Textiles & Apparel": ["CPSIA Compliance", "Flammability Standards", "Labeling Requirements"],
        "Electronics": ["FCC Certification", "UL Safety Standards", "Energy Star (optional)"],
        "Furniture": ["CARB Compliance", "CPSIA (children's furniture)", "Flammability Standards"]
    },
    "EU": {
        "Food & Beverages": ["CE Marking", "HACCP Certification", "Novel Food Regulation"],
        "Textiles & Apparel": ["REACH Compliance", "Oeko-Tex Standards", "CE Marking"],
        "Electronics": ["CE Marking", "RoHS Compliance", "WEEE Directive"],
        "Furniture": ["CE Marking", "REACH Compliance", "Fire Safety Standards"]
    },
    "JP": {
        "Food & Beverages": ["JAS Standards", "Food Sanitation Law", "Import Notification"],
        "Electronics": ["PSE Mark", "VCCI Certification", "Telec Certification"],
        "Textiles & Apparel": ["JIS Standards", "Safety Standards", "Labeling Requirements"]
    }
}

# EXPORT_READINESS_PROMPT is now imported from config.py

def init_export_readiness_session_state():
    """Initialize session state for export readiness assessment"""
    if 'export_assessment' not in st.session_state:
        st.session_state.export_assessment = {}
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = None
    if 'assessment_results' not in st.session_state:
        st.session_state.assessment_results = None
    if 'uploaded_product_image' not in st.session_state:
        st.session_state.uploaded_product_image = None

def get_memory_bot_data() -> Dict:
    """Retrieve product data from Memory Bot"""
    if hasattr(st.session_state, 'memory_bot') and st.session_state.memory_bot:
        return st.session_state.memory_bot
    return DEFAULT_EXTRACTED_DATA

def display_memory_bot_data():
    """Display existing Memory Bot data with edit option"""
    memory_data = get_memory_bot_data()
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(52, 152, 219, 0.2);
    ">
        <h4 style="color: #2c3e50; margin-bottom: 1rem;">📊 Your Product Information</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Company:** " + memory_data.get('company_name', 'Not specified'))
        st.write("**Product:** " + memory_data.get('product_details', {}).get('name', 'Not specified'))
        st.write("**Category:** " + memory_data.get('product_category', 'Not specified'))
        
    with col2:
        capacity = memory_data.get('production_capacity', {})
        capacity_str = f"{capacity.get('amount', 0)} {capacity.get('unit', '')} per {capacity.get('timeframe', '')}"
        st.write("**Production Capacity:** " + capacity_str)
        
        location = memory_data.get('production_location', {})
        location_str = f"{location.get('city', '')}, {location.get('province', '')}"
        st.write("**Location:** " + location_str)
    
    # Option to update data
    if st.button("✏️ Update Product Information", type="secondary"):
        st.info("💡 You can update your product information in the Chat section with Exporo!")

def display_country_selector():
    """Display interactive country selection interface"""
    st.markdown("""
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
    ">🌍 Select Target Export Country</div>
    """, unsafe_allow_html=True)
    
    # Create country selection with cards
    cols = st.columns(4)
    
    for i, country in enumerate(SUPPORTED_COUNTRIES):
        with cols[i % 4]:
            # Create country card
            if st.button(
                f"{country['flag']} {country['name']}\n🏪 {country['market_size']} Market\n📊 {country['difficulty']} Entry",
                key=f"country_{country['code']}",
                use_container_width=True
            ):
                st.session_state.selected_country = country
                st.rerun()
    
    # Display selected country info
    if st.session_state.selected_country:
        country = st.session_state.selected_country
        st.success(f"✅ Selected: {country['flag']} {country['name']}")
        
        # Show country details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Market Size", country['market_size'])
        with col2:
            st.metric("Entry Difficulty", country['difficulty'])
        with col3:
            # Get certification count
            memory_data = get_memory_bot_data()
            product_category = memory_data.get('product_category', 'Other')
            cert_count = len(CERTIFICATION_REQUIREMENTS.get(country['code'], {}).get(product_category, []))
            st.metric("Required Certifications", cert_count)

def display_product_image_upload():
    """Display product image upload for compliance verification"""
    st.markdown("""
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
    ">📸 Upload Product Image for Compliance Check</div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a product image for analysis",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear photo of your product for compliance verification"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Product Image", use_column_width=True)
        st.session_state.uploaded_product_image = uploaded_file
        st.success("✅ Product image uploaded successfully!")

def get_certification_requirements(country_code: str, product_category: str) -> List[str]:
    """Get certification requirements for specific country and product category"""
    return CERTIFICATION_REQUIREMENTS.get(country_code, {}).get(product_category, [])

def save_assessment_to_memory_bot(assessment_results: Dict):
    """Save assessment results to memory bot for tracking"""
    if 'memory_bot' not in st.session_state:
        st.session_state.memory_bot = DEFAULT_EXTRACTED_DATA.copy()
    
    # Create assessment record
    assessment_record = {
        "country": assessment_results['country']['name'],
        "country_code": assessment_results['country']['code'],
        "score": assessment_results['overall_score'],
        "timestamp": datetime.now().isoformat(),
        "status": assessment_results.get('export_readiness_level', 'Assessed'),
        "product": assessment_results['product_info']['name'],
        "category": assessment_results['product_info']['category']
    }
    
    # Add to assessment history
    if 'assessment_history' not in st.session_state.memory_bot:
        st.session_state.memory_bot['assessment_history'] = []
    
    # Remove duplicate assessments for the same country
    st.session_state.memory_bot['assessment_history'] = [
        record for record in st.session_state.memory_bot['assessment_history']
        if record.get('country') != assessment_results['country']['name']
    ]
    
    # Add new assessment record
    st.session_state.memory_bot['assessment_history'].append(assessment_record)
    
    # Update export readiness data
    if 'export_readiness' not in st.session_state.memory_bot:
        st.session_state.memory_bot['export_readiness'] = DEFAULT_EXTRACTED_DATA['export_readiness'].copy()
    
    # Add target country if not already present
    target_countries = st.session_state.memory_bot['export_readiness']['target_countries']
    if assessment_results['country']['name'] not in target_countries:
        target_countries.append(assessment_results['country']['name'])

def analyze_export_readiness() -> Dict:
    """Perform comprehensive AI-powered export readiness analysis"""
    memory_data = get_memory_bot_data()
    country = st.session_state.selected_country
    
    if not country:
        return {"error": "No country selected"}
    
    # Get product details
    company_name = memory_data.get('company_name', 'Not specified')
    product_name = memory_data.get('product_details', {}).get('name', 'Product')
    product_category = memory_data.get('product_category', 'Other')
    product_description = memory_data.get('product_details', {}).get('description', 'No description')
    
    # Get production info
    capacity = memory_data.get('production_capacity', {})
    capacity_str = f"{capacity.get('amount', 0)} {capacity.get('unit', '')} per {capacity.get('timeframe', '')}"
    
    location = memory_data.get('production_location', {})
    location_str = f"{location.get('city', '')}, {location.get('province', '')}, Indonesia"
    
    # Get certification requirements
    certifications = get_certification_requirements(country['code'], product_category)
    cert_str = ", ".join(certifications) if certifications else "No specific certifications found"
    
    try:
        # Initialize Gemini AI
        client = init_gemini()
        
        # Prepare the prompt with actual data
        formatted_prompt = EXPORT_READINESS_PROMPT.format(
            target_country=country['name'],
            company_name=company_name,
            product_name=product_name,
            product_category=product_category,
            product_description=product_description,
            production_capacity=capacity_str,
            production_location=location_str,
            market_difficulty=country['difficulty'],
            market_size=country['market_size'],
            required_certifications=cert_str
        )
        
        # Send to Gemini for analysis
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=formatted_prompt
        )
        
        # Parse the AI response
        ai_response = response.text.strip()
        
        # Clean up the response (remove markdown formatting if any)
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        
        # Parse JSON response
        assessment_data = json.loads(ai_response)
        
        # Add additional metadata
        assessment_data.update({
            "certifications": certifications,
            "country": country,
            "product_info": {
                "name": product_name,
                "category": product_category,
                "description": product_description,
                "company": company_name
            },
            "ai_powered": True
        })
        
        return assessment_data
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Error parsing AI response: {str(e)}")
        # Fallback to basic analysis
        return get_fallback_analysis(memory_data, country, certifications)
        
    except Exception as e:
        st.error(f"❌ AI Analysis Error: {str(e)}")
        # Fallback to basic analysis
        return get_fallback_analysis(memory_data, country, certifications)

def get_fallback_analysis(memory_data: Dict, country: Dict, certifications: List[str]) -> Dict:
    """Fallback analysis when AI is not available"""
    
    # Get product details
    product_name = memory_data.get('product_details', {}).get('name', 'Product')
    product_category = memory_data.get('product_category', 'Other')
    product_description = memory_data.get('product_details', {}).get('description', 'No description')
    
    # Calculate basic readiness score
    base_score = 65
    
    # Adjust based on available data
    if product_name != "Not specified":
        base_score += 5
    if product_category != "Not specified":
        base_score += 5
    if product_description != "No description":
        base_score += 5
    if st.session_state.uploaded_product_image:
        base_score += 10
    
    # Adjust based on target country difficulty
    difficulty_adjustment = {"Low": 10, "Medium": 0, "High": -10}
    base_score += difficulty_adjustment.get(country['difficulty'], 0)
    
    # Ensure score is within bounds
    overall_score = max(0, min(100, base_score))
    
    # Generate category scores
    category_scores = {
        "regulatory_compliance": max(0, min(100, overall_score + 5)),
        "market_viability": max(0, min(100, overall_score - 5)),
        "documentation_readiness": max(0, min(100, overall_score - 10)),
        "competitive_positioning": max(0, min(100, overall_score + 3))
    }
    
    # Generate action items
    action_items = []
    
    if category_scores["regulatory_compliance"] < 80:
        action_items.append(f"Research and obtain required certifications for {country['name']}")
    
    if category_scores["documentation_readiness"] < 70:
        action_items.append("Prepare export documentation and compliance certificates")
    
    if category_scores["market_viability"] < 75:
        action_items.append("Conduct market research and identify target customers")
    
    if not st.session_state.uploaded_product_image:
        action_items.append("Upload product images for visual compliance verification")
    
    if len(certifications) > 0:
        cert_str = ", ".join(certifications)
        action_items.append(f"Obtain the following certifications: {cert_str}")
    
    # Estimate timeline
    timeline_weeks = len(action_items) * 2 + (4 if country['difficulty'] == "High" else 2)
    timeline = f"{timeline_weeks} weeks"
    
    # Determine readiness level
    readiness_level = "Ready" if overall_score >= 80 else "Needs Preparation" if overall_score >= 60 else "Significant Work Required"
    
    return {
        "overall_score": overall_score,
        "category_scores": category_scores,
        "action_items": action_items,
        "timeline_estimate": timeline,
        "market_insights": f"Basic analysis for {product_category} export to {country['name']}. AI analysis recommended for detailed insights.",
        "certification_priority": certifications[:2] if certifications else [],
        "competitive_advantages": ["Made in Indonesia", "Competitive pricing"],
        "potential_challenges": [f"{country['difficulty']} market entry difficulty", "Certification requirements"],
        "export_readiness_level": readiness_level,
        "certifications": certifications,
        "country": country,
        "product_info": {
            "name": product_name,
            "category": product_category,
            "description": product_description
        },
        "ai_powered": False
    }

def display_assessment_results(results: Dict):
    """Display comprehensive assessment results"""
    if "error" in results:
        st.error(f"❌ Assessment Error: {results['error']}")
        return
    
    # Header
    st.markdown("""
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
    ">📊 Export Readiness Assessment Results</div>
    """, unsafe_allow_html=True)
    
    # Overall Score
    score = results['overall_score']
    score_color = "#27ae60" if score >= 80 else "#f39c12" if score >= 60 else "#e74c3c"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {score_color}20, {score_color}10);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 1.5rem;
        border: 1px solid {score_color}40;
    ">
        <h2 style="color: {score_color}; margin: 0;">Overall Readiness Score</h2>
        <h1 style="color: {score_color}; margin: 0.5rem 0;">{score}/100</h1>
        <p style="margin: 0;">for {results['country']['flag']} {results['country']['name']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category Scores
    st.subheader("📈 Category Breakdown")
    
    categories = results['category_scores']
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("🏛️ Regulatory Compliance", f"{categories['regulatory_compliance']}/100")
        st.metric("📋 Documentation Readiness", f"{categories['documentation_readiness']}/100")
    
    with col2:
        st.metric("🎯 Market Viability", f"{categories['market_viability']}/100")
        st.metric("🏆 Competitive Positioning", f"{categories['competitive_positioning']}/100")
    
    # Action Items
    st.subheader("✅ Action Plan")
    
    if results['action_items']:
        for i, action in enumerate(results['action_items'], 1):
            st.write(f"{i}. {action}")
    else:
        st.success("🎉 Great! No immediate actions required.")
    
    # Timeline
    st.subheader("⏱️ Estimated Timeline")
    timeline = results.get('timeline_estimate', results.get('timeline', 'Not specified'))
    st.info(f"📅 Estimated preparation time: **{timeline}**")
    
    # Market Insights (AI-powered)
    if 'market_insights' in results:
        st.subheader("🎯 Market Insights")
        st.write(results['market_insights'])
    
    # Competitive Advantages
    if 'competitive_advantages' in results and results['competitive_advantages']:
        st.subheader("💪 Competitive Advantages")
        for advantage in results['competitive_advantages']:
            st.write(f"✅ {advantage}")
    
    # Potential Challenges
    if 'potential_challenges' in results and results['potential_challenges']:
        st.subheader("⚠️ Potential Challenges")
        for challenge in results['potential_challenges']:
            st.write(f"⚠️ {challenge}")
    
    # Export Readiness Level
    if 'export_readiness_level' in results:
        readiness_level = results['export_readiness_level']
        level_color = "#27ae60" if readiness_level == "Ready" else "#f39c12" if readiness_level == "Needs Preparation" else "#e74c3c"
        
        st.markdown(f"""
        <div style="
            background: {level_color}20;
            padding: 1rem;
            border-radius: 10px;
            border-left: 5px solid {level_color};
            margin: 1rem 0;
        ">
            <h4 style="color: {level_color}; margin: 0;">📊 Export Readiness Level: {readiness_level}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Certification Priority
    if 'certification_priority' in results and results['certification_priority']:
        st.subheader("🏆 Priority Certifications")
        for i, cert in enumerate(results['certification_priority'], 1):
            st.write(f"{i}. {cert}")
    
    # Required Certifications
    if results['certifications']:
        st.subheader("📜 All Required Certifications")
        for cert in results['certifications']:
            st.write(f"• {cert}")
    
    # AI-powered indicator
    if results.get('ai_powered', False):
        st.success("🤖 Analysis powered by Gemini AI")
    else:
        st.info("📊 Basic analysis - Connect to Gemini AI for enhanced insights")
    
    # Export Results Button
    if st.button("📄 Download Assessment Report", type="primary"):
        # Generate comprehensive text report
        timeline = results.get('timeline_estimate', results.get('timeline', 'Not specified'))
        readiness_level = results.get('export_readiness_level', 'Not assessed')
        market_insights = results.get('market_insights', 'No insights available')
        
        report_text = f"""
EXPORT READINESS ASSESSMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Type: {"AI-Powered" if results.get('ai_powered', False) else "Basic Analysis"}

=== PRODUCT INFORMATION ===
Company: {results['product_info'].get('company', 'Not specified')}
Product: {results['product_info']['name']}
Category: {results['product_info']['category']}
Target Market: {results['country']['name']}

=== ASSESSMENT RESULTS ===
Overall Score: {results['overall_score']}/100
Export Readiness Level: {readiness_level}

Category Breakdown:
- Regulatory Compliance: {categories['regulatory_compliance']}/100
- Market Viability: {categories['market_viability']}/100
- Documentation Readiness: {categories['documentation_readiness']}/100
- Competitive Positioning: {categories['competitive_positioning']}/100

=== MARKET INSIGHTS ===
{market_insights}

=== ACTION PLAN ===
{chr(10).join([f"{i+1}. {item}" for i, item in enumerate(results['action_items'])])}

=== COMPETITIVE ADVANTAGES ===
{chr(10).join([f"+ {adv}" for adv in results.get('competitive_advantages', [])])}

=== POTENTIAL CHALLENGES ===
{chr(10).join([f"- {challenge}" for challenge in results.get('potential_challenges', [])])}

=== CERTIFICATION REQUIREMENTS ===
Priority Certifications:
{chr(10).join([f"1. {cert}" for cert in results.get('certification_priority', [])])}

All Required Certifications:
{chr(10).join([f"• {cert}" for cert in results['certifications']])}

=== TIMELINE ===
Estimated Preparation Time: {timeline}

---
Report generated by Exporo SME Export Assistant
For more information, visit: https://github.com/magungh1/exporo-sme-export-assistant
        """
        
        st.download_button(
            label="📥 Download Complete Report",
            data=report_text,
            file_name=f"export_readiness_{results['country']['code'].lower()}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

def show_export_readiness_page():
    """Display the complete export readiness assessment page"""
    # Page Header
    st.markdown("""
    <div style="
        background: linear-gradient(180deg, #2c3e50, #34495e);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(44, 62, 80, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    ">
        <h2 style="color: white; margin: 0; font-size: 1.5rem;">🌍 Export Readiness Assessment</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; font-size: 0.9rem;">
            Comprehensive analysis for international market entry
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_export_readiness_session_state()
    
    # Step 1: Display Memory Bot Data
    display_memory_bot_data()
    
    # Step 2: Country Selection
    display_country_selector()
    
    # Step 3: Product Image Upload (optional)
    if st.session_state.selected_country:
        display_product_image_upload()
        
        # Step 4: Run Assessment
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Analyze Export Readiness", type="primary", use_container_width=True):
                with st.spinner("🔄 Analyzing export readiness..."):
                    results = analyze_export_readiness()
                    st.session_state.assessment_results = results
                    
                    # Save assessment to memory bot for tracking
                    if results and 'error' not in results:
                        save_assessment_to_memory_bot(results)
                        
                st.success("✅ Assessment completed and saved to Memory Bot!")
                st.rerun()
    
    # Step 5: Display Results
    if st.session_state.assessment_results:
        st.markdown("---")
        display_assessment_results(st.session_state.assessment_results)

def reset_export_assessment():
    """Reset export assessment data"""
    st.session_state.export_assessment = {}
    st.session_state.selected_country = None
    st.session_state.assessment_results = None
    st.session_state.uploaded_product_image = None