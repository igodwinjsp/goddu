import os
import hashlib
import streamlit as st
import pandas as pd
import openpyxl
from pathlib import Path

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SKPS YOUTH FESTIVAL SUVARNNAM 2026",
    page_icon="🏆",
    layout="wide",
)

# Custom CSS targeting button elements directly so unselected items are Red and selected items turn Green
st.markdown("""
    <style>
    .main {
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    
    /* Global button base styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3.5em;
        border: 2px solid rgba(255,255,255,0.2) !important;
        transition: all 0.2s ease;
    }

    /* Unselected item buttons -> RED */
    div[data-testid="column"] button {
        background-color: #C0392B !important;
        color: #FFFFFF !important;
    }
    div[data-testid="column"] button:hover {
        background-color: #A93226 !important;
        border-color: #FFFFFF !important;
    }

    /* Selected item buttons -> GREEN */
    div[data-testid="column"] button.selected-item-btn {
        background-color: #27AE60 !important;
        color: #FFFFFF !important;
        border-color: #2ECC71 !important;
    }
    div[data-testid="column"] button.selected-item-btn:hover {
        background-color: #219653 !important;
        border-color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
DB_STUDENTS = Path("STUDENTDB.XLSX")
DB_ITEMS = Path("ITEMS.XLSX")
FILE_PARTICIPANTS = Path("participantslist.xlsx")

# Admin password configuration using Streamlit Secrets for public safety
try:
    ADMIN_PASSWORD_HASH = st.secrets["ADMIN_PASSWORD_HASH"]
except Exception:
    ADMIN_PASSWORD_HASH = hashlib.sha256("goddu@yf26".encode()).hexdigest()

# Check if registrations are explicitly closed via Streamlit Secrets (default to open if not specified)
try:
    REGISTRATIONS_OPEN = st.secrets.get("REGISTRATIONS_OPEN", True)
except Exception:
    REGISTRATIONS_OPEN = True

# ==========================================
# INITIALIZATION HELPERS
# ==========================================
if not FILE_PARTICIPANTS.exists():
    df_empty = pd.DataFrame(columns=[
        "ADM NO", "CHESTNO", "STUDENT NAME", "CLASS", "SECTION", 
        "GENDER", "HOUSE", "ITEMCODE", "ITEMNAME", "ONSTAGE/OFFSTAGE", "SINGLE/GROUP"
    ])
    df_empty.to_excel(FILE_PARTICIPANTS, index=False)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "selected_items" not in st.session_state:
    st.session_state.selected_items = {}

if "current_adm_no" not in st.session_state:
    st.session_state.current_adm_no = ""

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ==========================================
# APP HEADER
# ==========================================
st.markdown("<h1 style='text-align: center; color: #FFD700;'>SKPS YOUTH FESTIVAL SUVARNNAM 2026</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #FFFFFF;'>CATEGORY IV - ENTRY FOR PARTICIPATION</h3>", unsafe_allow_html=True)
st.write("---")

# ==========================================
# 1. ENTRY FOR PARTICIPATION (ISOLATED VIEW)
# ==========================================
st.subheader("1. Entry for Participation")

if not REGISTRATIONS_OPEN:
    st.warning("🔒 **Registrations are currently closed.** The portal is no longer accepting new participant entries.")
else:
    adm_no = st.text_input("Enter Admission No:", value=st.session_state.current_adm_no).strip()

    # Reset selections if admission number changes
    if adm_no != st.session_state.current_adm_no:
        st.session_state.current_adm_no = adm_no
        st.session_state.selected_items = {}

    if adm_no:
        if DB_STUDENTS.exists() and DB_ITEMS.exists():
            df_stud = pd.read_excel(DB_STUDENTS, engine="openpyxl")
            df_stud["ADM NO"] = df_stud["ADM NO"].astype(str).str.strip()
            student = df_stud[df_stud["ADM NO"] == adm_no]
            
            if student.empty:
                st.error("Admission Number not found!")
            else:
                s_data = student.iloc[0]
                student_gender = str(s_data.get("GENDER", "")).strip().upper()
                
                st.success(f"Student: **{s_data['STUDENT NAME']}** | Chest No: **{s_data['CHESTNO']}** | Class: **{s_data['CLASS']}-{s_data['SECTION']}** | Gender: **{student_gender}** | House: **{s_data['HOUSE']}**")
                
                df_items = pd.read_excel(DB_ITEMS, engine="openpyxl")
                st.write("Click items to select (Red = Available, Green = Selected):")
                
                cols = st.columns(3)
                for i, row in df_items.iterrows():
                    code = str(row["ITEMCODE"]).strip()
                    name = str(row["ITEMNAME"]).strip()
                    cat = str(row["ONSTAGE/OFFSTAGE"]).strip().upper()
                    sg = str(row["SINGLE/GROUP"]).strip().upper()
                    item_gender = str(row.get("BOYS/GIRLS/COMMON", "COMMON")).strip().upper()

                    # Gender validation check per item
                    allowed = True
                    if item_gender == "BOYS" and student_gender != "MALE":
                        allowed = False
                    elif item_gender == "GIRLS" and student_gender != "FEMALE":
                        allowed = False

                    is_selected = code in st.session_state.selected_items
                    
                    with cols[i % 3]:
                        if not allowed:
                            st.button(f"NOT ALLOWED\n{name}", disabled=True, key=f"item_{code}")
                        else:
                            button_label = f"✔ {name} ({cat} - {sg})" if is_selected else f"{name} ({cat} - {sg})"
                            
                            if is_selected:
                                st.markdown(f"""
                                    <style>
                                    div[data-testid="column"] button:has-text("{name}") {{
                                        background-color: #27AE60 !important;
                                        border-color: #2ECC71 !important;
                                    }}
                                    </style>
                                """, unsafe_allow_html=True)
                            
                            if st.button(button_label, key=f"btn_{code}"):
                                if is_selected:
                                    del st.session_state.selected_items[code]
                                else:
                                    st.session_state.selected_items[code] = {
                                        "code": code, 
                                        "name": name, 
                                        "type": cat, 
                                        "single_group": sg, 
                                        "gender_rule": item_gender,
                                        "student": s_data
                                    }
                                st.rerun()

                sel_list = list(st.session_state.selected_items.values())
                
                indiv_count = sum(1 for item in sel_list if item["single_group"] == "SINGLE")
                group_count = sum(1 for item in sel_list if item["single_group"] == "GROUP")
                onstage_indiv_count = sum(1 for item in sel_list if item["single_group"] == "SINGLE" and item["type"] == "ONSTAGE")
                offstage_indiv_count = sum(1 for item in sel_list if item["single_group"] == "SINGLE" and item["type"] == "OFFSTAGE")

                st.info(f"Selection Summary — Individual: {indiv_count}/5 | Group: {group_count}/2 | On-stage Individual: {onstage_indiv_count}/3")

                if st.button("Confirm & Save Registration", type="primary"):
                    if not sel_list:
                        st.warning("No items selected!")
                    else:
                        if indiv_count > 5 or group_count > 2 or onstage_indiv_count > 3:
                            st.error(f"Criteria Violation: Individual ({indiv_count}/5), Group ({group_count}/2), On-stage Individual ({onstage_indiv_count}/3).")
                        elif onstage_indiv_count == 0 and offstage_indiv_count > 5:
                            st.error("Criteria Violation: Non-onstage participants are capped at 5 off-stage individual events.")
                        else:
                            if FILE_PARTICIPANTS.exists():
                                df_existing = pd.read_excel(FILE_PARTICIPANTS, engine="openpyxl")
                                df_existing["ADM NO"] = df_existing["ADM NO"].astype(str).str.strip()
                                df_existing["ITEMCODE"] = df_existing["ITEMCODE"].astype(str).str.strip()
                            else:
                                df_existing = pd.DataFrame(columns=["ADM NO", "ITEMCODE"])

                            new_records = []
                            duplicate_items = []

                            for item in sel_list:
                                st_info = item["student"]
                                a_no = str(st_info["ADM NO"]).strip()
                                i_code = str(item["code"]).strip()

                                already_registered = False
                                if not df_existing.empty:
                                    match = df_existing[
                                        (df_existing["ADM NO"] == a_no) & 
                                        (df_existing["ITEMCODE"] == i_code)
                                    ]
                                    if not match.empty:
                                        already_registered = True

                                if already_registered:
                                    duplicate_items.append(item["name"])
                                else:
                                    new_records.append({
                                        "ADM NO": a_no,
                                        "CHESTNO": st_info["CHESTNO"],
                                        "STUDENT NAME": st_info["STUDENT NAME"],
                                        "CLASS": st_info["CLASS"],
                                        "SECTION": st_info["SECTION"],
                                        "GENDER": st_info["GENDER"],
                                        "HOUSE": st_info["HOUSE"],
                                        "ITEMCODE": i_code,
                                        "ITEMNAME": item["name"],
                                        "ONSTAGE/OFFSTAGE": item["type"],
                                        "SINGLE/GROUP": item["single_group"],
                                    })

                            if duplicate_items:
                                st.error(f"Duplicate Entry Blocked! Student is already registered for: {', '.join(duplicate_items)}")
                            
                            if new_records:
                                df_new = pd.DataFrame(new_records)
                                if not df_existing.empty:
                                    df_final = pd.concat([df_existing, df_new], ignore_index=True)
                                else:
                                    df_final = df_new
                                
                                df_final.to_excel(FILE_PARTICIPANTS, index=False, engine="openpyxl")
                                st.success("Registration saved successfully for new items!")
                                st.session_state.selected_items = {}
        else:
            st.error("Required database files (`STUDENTDB.XLSX` or `ITEMS.XLSX`) are missing from the repository directory.")

# ==========================================
# SECURE DOWNLOAD & ADMIN MANAGEMENT
# ==========================================
st.write("---")
st.subheader("📥 Admin Management & Export")

if not st.session_state.authenticated:
    entered_password = st.text_input("Enter Admin Password to Unlock Management Options:", type="password")
    if st.button("Unlock Admin Panel"):
        if hashlib.sha256(entered_password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Password!")
else:
    st.success("Authenticated successfully as Admin!")
    
    if FILE_PARTICIPANTS.exists():
        with open(FILE_PARTICIPANTS, "rb") as f:
            st.download_button(
                label="Download Current participantslist.xlsx",
                data=f,
                file_name="participantslist.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    st.write("---")
    if st.button("⚠️ Clear All Participant Entries", type="secondary"):
        df_empty = pd.DataFrame(columns=[
            "ADM NO", "CHESTNO", "STUDENT NAME", "CLASS", "SECTION", 
            "GENDER", "HOUSE", "ITEMCODE", "ITEMNAME", "ONSTAGE/OFFSTAGE", "SINGLE/GROUP"
        ])
        df_empty.to_excel(FILE_PARTICIPANTS, index=False, engine="openpyxl")
        st.success("All participant entries have been securely cleared!")
        st.rerun()

    if st.button("Lock Admin Panel Again"):
        st.session_state.authenticated = False
        st.rerun()
