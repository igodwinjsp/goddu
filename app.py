import os
import hashlib
import streamlit as st
import pandas as pd

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SKPS YOUTH FESTIVAL SUVARNNAM 2026",
    page_icon="🏆",
    layout="wide",
)

# Custom CSS to match the dark theme and large touch targets
st.markdown("""
    <style>
    .main {
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
DB_STUDENTS = "STUDENTDB.XLSX"
DB_ITEMS = "ITEMS.XLSX"
FILE_PARTICIPANTS = "participantslist.xlsx"

# ==========================================
# INITIALIZATION HELPERS
# ==========================================
def ensure_sample_databases():
    if not os.path.exists(DB_STUDENTS):
        df_stud = pd.DataFrame([
            {"ADM NO": "1001", "CHESTNO": "C101", "STUDENT NAME": "Ananya Nair", "CLASS": "10", "SECTION": "A", "GENDER": "Female", "HOUSE": "Blue"},
            {"ADM NO": "1002", "CHESTNO": "C102", "STUDENT NAME": "Rohan Kumar", "CLASS": "10", "SECTION": "B", "GENDER": "Male", "HOUSE": "Red"},
            {"ADM NO": "1003", "CHESTNO": "C103", "STUDENT NAME": "Devika S", "CLASS": "10", "SECTION": "A", "GENDER": "Female", "HOUSE": "Yellow"},
            {"ADM NO": "1004", "CHESTNO": "C104", "STUDENT NAME": "Kevin Thomas", "CLASS": "10", "SECTION": "C", "GENDER": "Male", "HOUSE": "Green"},
        ])
        df_stud.to_excel(DB_STUDENTS, index=False)

    if not os.path.exists(DB_ITEMS):
        df_items = pd.DataFrame([
            {"ITEMCODE": "101", "ITEMNAME": "Light Music", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "SINGLE"},
            {"ITEMCODE": "102", "ITEMNAME": "Classical Dance", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "SINGLE"},
            {"ITEMCODE": "103", "ITEMNAME": "Margamkali", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "GROUP"},
            {"ITEMCODE": "201", "ITEMNAME": "Pencil Drawing", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "SINGLE"},
            {"ITEMCODE": "202", "ITEMNAME": "Essay Writing", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "SINGLE"},
            {"ITEMCODE": "203", "ITEMNAME": "Group Quiz", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "GROUP"},
        ])
        df_items.to_excel(DB_ITEMS, index=False)

ensure_sample_databases()

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
adm_no = st.text_input("Enter Admission No:").strip()

if adm_no:
    if os.path.exists(DB_STUDENTS) and os.path.exists(DB_ITEMS):
        df_stud = pd.read_excel(DB_STUDENTS)
        df_stud["ADM NO"] = df_stud["ADM NO"].astype(str).str.strip()
        student = df_stud[df_stud["ADM NO"] == adm_no]
        
        if student.empty:
            st.error("Admission Number not found!")
        else:
            s_data = student.iloc[0]
            st.success(f"Student: **{s_data['STUDENT NAME']}** | Chest No: **{s_data['CHESTNO']}** | Class: **{s_data['CLASS']}-{s_data['SECTION']}** | House: **{s_data['HOUSE']}**")
            
            df_items = pd.read_excel(DB_ITEMS)
            st.write("Select items below:")
            
            selected_items = []
            cols = st.columns(3)
            for i, row in df_items.iterrows():
                code = str(row["ITEMCODE"]).strip()
                name = str(row["ITEMNAME"]).strip()
                cat = str(row["ONSTAGE/OFFSTAGE"]).strip().upper()
                sg = str(row["SINGLE/GROUP"]).strip().upper()
                
                with cols[i % 3]:
                    if st.checkbox(f"{name} ({cat} - {sg})", key=code):
                        selected_items.append({"code": code, "name": name, "type": cat, "single_group": sg, "student": s_data})
            
            if st.button("Confirm & Save Registration"):
                if not selected_items:
                    st.warning("No items selected!")
                else:
                    onstage_count = sum(1 for item in selected_items if item["type"] == "ONSTAGE")
                    offstage_count = sum(1 for item in selected_items if item["type"] == "OFFSTAGE")
                    
                    if len(selected_items) > 4 or onstage_count > 2 or offstage_count > 2:
                        st.error(f"Criteria Violation! Selection: {onstage_count} Onstage, {offstage_count} Offstage. Max allowed: 2 Onstage + 2 Offstage (Total 4).")
                    else:
                        # Load existing participants to check for duplicates
                        if os.path.exists(FILE_PARTICIPANTS):
                            df_existing = pd.read_excel(FILE_PARTICIPANTS)
                            df_existing["ADM NO"] = df_existing["ADM NO"].astype(str).str.strip()
                            df_existing["ITEMCODE"] = df_existing["ITEMCODE"].astype(str).str.strip()
                        else:
                            df_existing = pd.DataFrame(columns=["ADM NO", "ITEMCODE"])

                        new_records = []
                        duplicate_items = []

                        for item in selected_items:
                            st_info = item["student"]
                            a_no = str(st_info["ADM NO"]).strip()
                            i_code = str(item["code"]).strip()

                            # Check if admission number + item code already exists
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
                            
                            df_final.to_excel(FILE_PARTICIPANTS, index=False)
                            st.success("Registration saved successfully for new items!")
