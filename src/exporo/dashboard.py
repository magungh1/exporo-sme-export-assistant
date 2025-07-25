"""
Dashboard module for Exporo SME Export Assistant
Displays export progress tracking interface similar to the reference design
"""

import streamlit as st
import json
import sqlite3
from datetime import datetime
from .config import DATABASE_NAME, DEFAULT_EXTRACTED_DATA
from .auth import load_memory_bot_data


def get_dashboard_data(user_id: int) -> dict:
    """Fetch and process all dashboard data from database"""
    try:
        # Get user info from users table
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT first_name, last_name, email, created_at
            FROM users WHERE id = ?
        """, (user_id,))

        user_data = cursor.fetchone()
        conn.close()

        if not user_data:
            return {}

        # Get memory bot data for business profile
        memory_data = load_memory_bot_data(user_id)

        # Calculate profile completeness
        profile_status = calculate_profile_completeness(memory_data)

        # Get assessment summary
        assessment_summary = get_assessment_summary(memory_data)

        return {
            "user": {
                "first_name": user_data[0],
                "last_name": user_data[1],
                "email": user_data[2],
                "created_at": user_data[3]
            },
            "business_profile": memory_data,
            "profile_completeness": profile_status,
            "assessment_summary": assessment_summary
        }

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return {}


def calculate_profile_completeness(memory_data: dict) -> dict:
    """Calculate profile completion percentage and progress"""

    # Helper function to check if capacity amount is valid
    def has_valid_capacity(capacity_data):
        try:
            amount = capacity_data.get("amount", 0)
            if amount is None:
                return False
            return float(amount) > 0
        except (ValueError, TypeError):
            return False

    required_fields = [
        memory_data.get("company_name", "Not specified") != "Not specified",
        memory_data.get("product_details", {}).get("name", "Not specified") != "Not specified",
        memory_data.get("product_category", "Not specified") != "Not specified",
        has_valid_capacity(memory_data.get("production_capacity", {})),
        memory_data.get("production_location", {}).get("city", "Not specified") != "Not specified",
        memory_data.get("business_background", "Not specified") != "Not specified"
    ]

    completed = sum(required_fields)
    total = len(required_fields)
    percentage = (completed / total) * 100

    return {
        "percentage": percentage,
        "completed": int(completed),
        "total": int(total),
        "is_complete": bool(completed == total)
    }


def get_assessment_summary(memory_data: dict) -> dict:
    """Get export readiness assessment summary"""
    # Ensure we have valid data structures
    if not isinstance(memory_data, dict):
        memory_data = {}

    assessment_history = memory_data.get("assessment_history", [])
    export_readiness = memory_data.get("export_readiness", {})

    # Ensure assessment_history is a list
    if not isinstance(assessment_history, list):
        assessment_history = []

    # Ensure export_readiness is a dict
    if not isinstance(export_readiness, dict):
        export_readiness = {}

    if not assessment_history:
        return {
            "latest_score": 0,
            "total_assessments": 0,
            "countries_assessed": [],
            "target_countries": export_readiness.get("target_countries", []) if isinstance(export_readiness.get("target_countries"), list) else []
        }

    # Get latest assessment
    latest_assessment = assessment_history[-1] if assessment_history else {}
    if not isinstance(latest_assessment, dict):
        latest_assessment = {}

    # Calculate average score with safe numeric conversion
    scores = []
    for assessment in assessment_history:
        if isinstance(assessment, dict) and assessment.get("score"):
            try:
                score = float(assessment.get("score", 0))
                if 0 <= score <= 100:  # Valid score range
                    scores.append(score)
            except (ValueError, TypeError):
                continue

    avg_score = sum(scores) / len(scores) if scores else 0

    # Safe extraction of countries
    countries_assessed = []
    for assessment in assessment_history:
        if isinstance(assessment, dict) and assessment.get("country"):
            country = assessment.get("country", "")
            if isinstance(country, str) and country.strip():
                countries_assessed.append(country.strip())

    countries_assessed = list(set(countries_assessed))  # Remove duplicates

    # Safe extraction of latest score
    try:
        latest_score = float(latest_assessment.get("score", 0)) if latest_assessment.get("score") else 0
        if not (0 <= latest_score <= 100):
            latest_score = 0
    except (ValueError, TypeError):
        latest_score = 0

    # Safe extraction of target countries
    target_countries = export_readiness.get("target_countries", [])
    if not isinstance(target_countries, list):
        target_countries = []

    return {
        "latest_score": latest_score,
        "average_score": avg_score,
        "total_assessments": len(assessment_history),
        "countries_assessed": countries_assessed,
        "target_countries": target_countries,
        "latest_country": str(latest_assessment.get("country", "")) if latest_assessment.get("country") else "",
        "latest_status": str(latest_assessment.get("status", "")) if latest_assessment.get("status") else ""
    }


def show_dashboard_page():
    """Display the main dashboard page"""
    # Get user data
    user_id = st.session_state.user["id"]
    dashboard_data = get_dashboard_data(user_id)

    if not dashboard_data:
        st.error("Unable to load dashboard data")
        return

    user_data = dashboard_data["user"]
    business_profile = dashboard_data["business_profile"]
    profile_status = dashboard_data["profile_completeness"]
    assessment_summary = dashboard_data["assessment_summary"]

    # Dashboard header
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            border: 1px solid rgba(255,255,255,0.2);
        ">
            <h1 style="color: white; margin: 0; font-size: 2.5rem;">📊 Lacak Progress Ekspor</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                Monitor perjalanan ekspor bisnis Anda
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main content layout
    col1, col2, col3 = st.columns([2, 3, 2])

    with col1:
        show_profile_summary(business_profile, profile_status)

    with col2:
        show_export_progress_tracker(business_profile, assessment_summary)

    with col3:
        show_global_expansion_score(assessment_summary)
        show_country_recommendations(assessment_summary)


def show_profile_summary(business_profile: dict, profile_status: dict):
    """Display business profile summary card"""
    st.markdown("### 👤 Detail Produk")

    # Profile completion indicator
    completion_color = "#4CAF50" if profile_status["is_complete"] else "#FF9800"
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="
                    width: 40px;
                    height: 40px;
                    background: {completion_color};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    margin-right: 1rem;
                ">
                    {int(float(profile_status.get("percentage", 0)))}%
                </div>
                <div>
                    <div style="font-weight: bold; color: #2c3e50;">Profil Lengkap</div>
                    <div style="font-size: 0.9rem; color: #7f8c8d;">{int(profile_status.get("completed", 0))}/{int(profile_status.get("total", 1))} selesai</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Business details with safe data extraction
    company_name = str(business_profile.get("company_name", "Belum diisi")) if business_profile.get("company_name") else "Belum diisi"

    # Safe product name extraction
    product_details = business_profile.get("product_details", {})
    if not isinstance(product_details, dict):
        product_details = {}
    product_name = str(product_details.get("name", "Belum diisi")) if product_details.get("name") else "Belum diisi"

    # Safe capacity extraction
    capacity = business_profile.get("production_capacity", {})
    if not isinstance(capacity, dict):
        capacity = {}

    try:
        capacity_amount = capacity.get('amount', 0)
        if capacity_amount is None or capacity_amount == "":
            capacity_amount = 0
        capacity_amount = float(capacity_amount)
        has_capacity = capacity_amount > 0
    except (ValueError, TypeError):
        has_capacity = False
        capacity_amount = 0

    capacity_unit = str(capacity.get('unit', '')) if capacity.get('unit') else ''
    capacity_timeframe = str(capacity.get('timeframe', '')) if capacity.get('timeframe') else ''

    if has_capacity and (capacity_unit or capacity_timeframe):
        capacity_text = f"{capacity_amount} {capacity_unit} per {capacity_timeframe}".strip()
    elif has_capacity:
        capacity_text = str(capacity_amount)
    else:
        capacity_text = "Belum diisi"

    # Safe category extraction
    category = str(business_profile.get("product_category", "Belum diisi")) if business_profile.get("product_category") else "Belum diisi"

    # Safe location extraction
    location = business_profile.get("production_location", {})
    if not isinstance(location, dict):
        location = {}

    city = str(location.get('city', '')) if location.get('city') else ''
    province = str(location.get('province', '')) if location.get('province') else ''

    if city and province:
        location_text = f"{city}, {province}"
    elif city:
        location_text = city
    elif province:
        location_text = province
    else:
        location_text = "Belum diisi"

    st.markdown(f"**Nama Usaha:** {company_name}")
    st.markdown(f"**Produk Dijual:** {product_name}")
    st.markdown(f"**Kapasitas Produksi:** {capacity_text}")
    st.markdown(f"**Kategori Produk:** {category}")
    st.markdown(f"**Lokasi Produksi:** {location_text}")

    # Edit profile button
    if st.button("✏️ Edit Profil", use_container_width=True, key="edit_profile"):
        st.session_state.page = "chat"
        st.rerun()


def show_export_progress_tracker(business_profile: dict, assessment_summary: dict):
    """Display export progress tracker with two stages"""
    st.markdown("### 📈 Progress Ekspor")

    # Progress notification banner
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #FF6B35, #F7931E);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
        ">
            <strong>🚀 Lanjutkan Pendampingan Ekspansi</strong><br>
            <small>Chat dengan Exporo untuk melanjutkan analisis kesiapan ekspor</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("💬 Chat Sekarang", type="primary", use_container_width=True, key="chat_now"):
        st.session_state.page = "chat"
        st.rerun()

    st.markdown("---")

    # Stage 1: Product Quality & Export Potential
    st.markdown("#### Proses 1: Kualitas Produk & Potensi Ekspor")

    # Calculate stage 1 progress based on profile completeness
    profile_completion = calculate_profile_completeness(business_profile)
    stage1_progress = profile_completion["percentage"] / 100

    st.progress(stage1_progress, text=f"Langkah 1 dari 3 selesai ({int(stage1_progress * 100)}%)")

    # Stage 1 checklist
    company_complete = business_profile.get("company_name", "Not specified") != "Not specified"
    product_complete = business_profile.get("certification", {}).get("name", "Not specified") != "Not specified"

    # Check capacity completion with proper type handling
    try:
        capacity_amount = business_profile.get("production_capacity", {}).get("amount", 0)
        capacity_complete = float(capacity_amount) > 0 if capacity_amount else False
    except (ValueError, TypeError):
        capacity_complete = False

    st.markdown("**Rangkuman:**")
    status_icon = "✅" if company_complete else "⏳"
    st.markdown(f"{status_icon} Company Assesment")

    status_icon = "✅" if product_complete else "⏳"
    st.markdown(f"{status_icon} Validasi standar mutu dan keamanan sesuai standar internasional")

    status_icon = "✅" if capacity_complete else "⏳"
    st.markdown(f"{status_icon} Identifikasi keunikan atau nilai tambah produk sebagai USP")

    st.markdown(f"**Belum diselesaikan** • Tentukan HS Code produk untuk klasifikasi bea cukai")

    st.markdown("---")

    # Stage 2: Sales Strategy
    st.markdown("#### Proses 2: Strategi Penjualan")

    # Calculate stage 2 progress based on export readiness and assessments
    countries_assessed = assessment_summary.get("countries_assessed", [])
    target_countries = assessment_summary.get("target_countries", [])

    # Ensure we have lists
    if not isinstance(countries_assessed, list):
        countries_assessed = []
    if not isinstance(target_countries, list):
        target_countries = []

    has_assessments = len(countries_assessed) > 0
    has_targets = len(target_countries) > 0

    stage2_items = [has_assessments, has_targets]
    stage2_progress = sum(stage2_items) / len(stage2_items) if stage2_items else 0

    st.progress(stage2_progress, text=f"Langkah 1 dari 3 selesai ({int(stage2_progress * 100)}%)")

    # Stage 2 checklist
    st.markdown("**Rangkuman:**")
    status_icon = "✅" if has_assessments else "⏳"
    st.markdown(f"{status_icon} Riset pasar dan preferensi konsumen di berbagai negara")

    status_icon = "✅" if has_targets else "⏳"
    st.markdown(f"{status_icon} Identifikasi kebutuhan dan kebotuhan utama mereka")

    st.markdown("⏳ Bandingkan harga kompetitor di marketplace internasional")
    st.markdown("⏳ Tentukan harga jual ekspor dengan memperhitungkan seluruh biaya dan margin")


def show_global_expansion_score(assessment_summary: dict):
    """Display global expansion readiness score"""
    st.markdown("### 🌍 Skor Ekspansi Global")

    # Get the latest or average score with safe conversion
    try:
        latest_score = assessment_summary.get("latest_score", 0)
        average_score = assessment_summary.get("average_score", 0)

        # Convert to float first, then int
        if latest_score:
            score = int(float(latest_score))
        elif average_score:
            score = int(float(average_score))
        else:
            score = 0

        # Ensure score is within valid range
        score = max(0, min(100, score))
    except (ValueError, TypeError):
        score = 0

    # Determine readiness level and color
    if score >= 80:
        color = "#4CAF50"  # Green
        level = "Siap Ekspor"
    elif score >= 60:
        color = "#FF9800"  # Orange
        level = "Perlu Persiapan"
    else:
        color = "#F44336"  # Red
        level = "Butuh Pengembangan"

    # Create circular progress indicator
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(145deg, #ffffff, #f8f9fb);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 1.5rem;
        ">
            <div style="
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: conic-gradient({color} {score * 3.6}deg, #e0e0e0 0deg);
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem auto;
                position: relative;
            ">
                <div style="
                    width: 90px;
                    height: 90px;
                    border-radius: 50%;
                    background: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                ">
                    <div style="font-size: 2rem; font-weight: bold; color: {color};">{score}</div>
                    <div style="font-size: 0.8rem; color: #666;">/ 100</div>
                </div>
            </div>
            <div style="font-weight: bold; color: #2c3e50; margin-bottom: 0.5rem;">{level}</div>
            <div style="font-size: 0.9rem; color: #7f8c8d;">
                {assessment_summary.get("total_assessments", 0)} negara dinilai
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_country_recommendations(assessment_summary: dict):
    """Display country recommendations panel"""
    st.markdown("### 🎯 Rekomendasi Negara Potensial")

    # Country data with flags and difficulty levels
    country_data = {
        "Singapore": {"flag": "🇸🇬", "difficulty": "Mudah", "color": "#4CAF50"},
        "Malaysia": {"flag": "🇲🇾", "difficulty": "Mudah", "color": "#4CAF50"},
        "Australia": {"flag": "🇦🇺", "difficulty": "Sedang", "color": "#FF9800"},
        "Japan": {"flag": "🇯🇵", "difficulty": "Sulit", "color": "#F44336"},
        "Amerika Serikat": {"flag": "🇺🇸", "difficulty": "Sulit", "color": "#F44336"}
    }

    # Get target countries and assessed countries with safe extraction
    target_countries = assessment_summary.get("target_countries", [])
    assessed_countries = assessment_summary.get("countries_assessed", [])

    # Ensure we have lists
    if not isinstance(target_countries, list):
        target_countries = []
    if not isinstance(assessed_countries, list):
        assessed_countries = []

    # Show recommendations
    for country, data in country_data.items():
        is_target = country in target_countries
        is_assessed = country in assessed_countries

        # Determine card styling
        if is_assessed:
            border_color = "#4CAF50"
            bg_color = "rgba(76, 175, 80, 0.1)"
            status = "✅ Dinilai"
        elif is_target:
            border_color = "#2196F3"
            bg_color = "rgba(33, 150, 243, 0.1)"
            status = "🎯 Target"
        else:
            border_color = "#e0e0e0"
            bg_color = "#ffffff"
            status = "📋 Tersedia"

        st.markdown(
            f"""
            <div style="
                background: {bg_color};
                border: 2px solid {border_color};
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 0.5rem;
                transition: all 0.3s ease;
            ">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">{data["flag"]}</span>
                        <div>
                            <div style="font-weight: bold; color: #2c3e50;">{country}</div>
                            <div style="font-size: 0.8rem; color: {data['color']};">{data["difficulty"]}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.8rem; color: #666;">{status}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Action button
    if st.button("🔍 Analisis Kesiapan Ekspor", use_container_width=True, key="analyze_readiness"):
        st.session_state.page = "chat"
        st.session_state.trigger_export_readiness = True
        st.rerun()
