import os
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

# Custom CSS for guaranteed Red (unselected) and Green (selected) button styling
st.markdown("""
    <style>
    .main {
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    
    /* Base button sizing and layout */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3.5em;
        border: 2px solid rgba(255,255,255,0.2) !important;
        transition: all 0.2s ease;
    }

    /* Force RED styling for unselected state */
    div.red-btn button, div.red-btn button:focus, div.red-btn button:active {
        background-color: #D9534F !important;
        color: #FFFFFF !important;
    }
    div.red-btn button:hover {
        background-color: #C9302C !important;
        color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }

    /* Force GREEN styling for selected state */
    div.green-btn button, div.green-btn button:focus, div.green-btn button:active {
        background-color: #449D44 !important;
        color: #FFFFFF !important;
        border-color: #2ECC71 !important;
    }
    div.green-btn button:hover {
        background-color: #398439 !important;
        color: #FFFFFF !important;
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
DOWNLOAD_PASSWORD = "goddu@yf26"

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
            st.success(f"Student: **{s_data['STUDENT NAME']}** | Chest No: **{s_data['CHESTNO']}** | Class: **{s_data['CLASS']}-{s_data['SECTION']}** | House: **{s_data['HOUSE']}**")
            
            df_items = pd.read_excel(DB_ITEMS, engine="openpyxl")
            st.write("Click items to select (Red = Available, Green = Selected):")
            
            cols = st.columns(3)
            for i, row in df_items.iterrows():
                code = str(row["ITEMCODE"]).strip()
                name = str(row["ITEMNAME"]).strip()
                cat = str(row["ONSTAGE/OFFSTAGE"]).strip().upper()
                sg = str(row["SINGLE/GROUP"]).strip().upper()
                
                is_selected = code in st.session_state.selected_items
                
                with cols[i % 3]:
                    button_label = f"✔ {name} ({cat} - {sg})" if is_selected else f"{name} ({cat} - {sg})"
                    
                    css_class = "green-btn" if is_selected else "red-btn"
                    
                    st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                    if st.button(button_label, key=f"btn_{code}"):
                        if is_selected:
                            del st.session_state.selected_items[code]
                        else:
                            st.session_state.selected_items[code] = {
                                "code": code, 
                                "name": name, 
                                "type": cat, 
                                "single_group": sg, 
                                "student": s_data
                            }
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            sel_list = list(st.session_state.selected_items.values())
            on_cnt = sum(1 for item in sel_list if item["type"] == "ONSTAGE")
            off_cnt = sum(1 for item in sel_list if item["type"] == "OFFSTAGE")
            st.info(f"Current Selection Summary — Onstage: {on_cnt}/2 | Offstage: {off_cnt}/2 (Total: {len(sel_list)}/4)")

            if st.button("Confirm & Save Registration", type="primary"):
                if not sel_list:
                    st.warning("No items selected!")
                else:
                    if len(sel_list) > 4 or on_cnt > 2 or off_cnt > 2:
                        st.error(f"Criteria Violation! Selection: {on_cnt} Onstage, {off_cnt} Offstage. Max allowed: 2 Onstage + 2 Offstage (Total 4).")
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
# SECURE DOWNLOAD PARTICIPANTS LIST
# ==========================================
st.write("---")
st.subheader("📥 Export Registrations (Admin Only)")

if not st.session_state.authenticated:
    entered_password = st.text_input("Enter Admin Password to Unlock Download:", type="password")
    if st.button("Unlock Export"):
        if entered_password == DOWNLOAD_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Password!")
else:
    st.success("Authenticated successfully!")
    if FILE_PARTICIPANTS.exists():
        with open(FILE_PARTICIPANTS, "rb") as f:
            st.download_button(
                label="Download Current participantslist.xlsx",
                data=f,
                file_name="participantslist.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    if st.button("Lock Export Again"):
        st.session_state.authenticated = False
        st.rerun()
