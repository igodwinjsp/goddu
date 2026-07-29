import os
import pandas as pd
import streamlit as st

# ==========================================
# CONSTANTS & DIRECTORIES
# ==========================================
DB_STUDENTS = "studentdb4.xlsx"
DB_ITEMS = "items4.xlsx"
FILE_PARTICIPANTS = "participantslist.xlsx"

# Page Configuration
st.set_page_config(
    page_title="SKPS Youth Festival - Entry for Participation",
    layout="wide"
)

# ==========================================
# INITIALIZATION HELPERS
# ==========================================
def ensure_sample_databases():
    """Generates sample Excel files if missing."""
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
            {"ITEMCODE": "101", "ITEMNAME": "Light Music", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "SINGLE", "BOYS/GIRLS/COMMON": "COMMON"},
            {"ITEMCODE": "102", "ITEMNAME": "Classical Dance (Girls)", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "SINGLE", "BOYS/GIRLS/COMMON": "GIRLS"},
            {"ITEMCODE": "103", "ITEMNAME": "Margamkali", "ONSTAGE/OFFSTAGE": "ONSTAGE", "SINGLE/GROUP": "GROUP", "BOYS/GIRLS/COMMON": "COMMON"},
            {"ITEMCODE": "201", "ITEMNAME": "Pencil Drawing", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "SINGLE", "BOYS/GIRLS/COMMON": "COMMON"},
            {"ITEMCODE": "202", "ITEMNAME": "Essay Writing", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "SINGLE", "BOYS/GIRLS/COMMON": "COMMON"},
            {"ITEMCODE": "203", "ITEMNAME": "Group Quiz", "ONSTAGE/OFFSTAGE": "OFFSTAGE", "SINGLE/GROUP": "GROUP", "BOYS/GIRLS/COMMON": "COMMON"},
        ])
        df_items.to_excel(DB_ITEMS, index=False)


ensure_sample_databases()

# Header
st.title("SKPS YOUTH FESTIVAL SUVARNNAM 2026")
st.subheader("CATEGORY IV - 1. ENTRY FOR PARTICIPATION")
st.markdown("---")

# Initialize Session State
if "selected_student" not in st.session_state:
    st.session_state.selected_student = None

# Step 1: Admission Number Input & Search
adm_no_input = st.text_input("Enter Admission No:", placeholder="e.g., 1001").strip()

if st.button("Fetch Student", type="primary"):
    if not adm_no_input:
        st.warning("Please enter an Admission Number.")
    else:
        # Check if already registered
        already_registered = False
        if os.path.exists(FILE_PARTICIPANTS):
            df_existing = pd.read_excel(FILE_PARTICIPANTS)
            if not df_existing.empty and "ADM NO" in df_existing.columns:
                registered_adms = df_existing["ADM NO"].astype(str).str.strip().tolist()
                if adm_no_input in registered_adms:
                    already_registered = True

        if already_registered:
            st.error(f"Registration Blocked: Student with Admission No. '{adm_no_input}' is already registered!")
            st.session_state.selected_student = None
        else:
            # Fetch Student Details from DB
            df_stud = pd.read_excel(DB_STUDENTS)
            df_stud["ADM NO"] = df_stud["ADM NO"].astype(str).str.strip()
            student_match = df_stud[df_stud["ADM NO"] == adm_no_input]

            if student_match.empty:
                st.error("Admission Number not found!")
                st.session_state.selected_student = None
            else:
                st.session_state.selected_student = student_match.iloc[0].to_dict()

# Display Student Info and Item Selection Form
if st.session_state.selected_student:
    student = st.session_state.selected_student
    student_gender = str(student.get("GENDER", "")).strip().upper()

    st.success(
        f"**Student:** {student['STUDENT NAME']} | "
        f"**Chest No:** {student['CHESTNO']} | "
        f"**Class:** {student['CLASS']}-{student['SECTION']} | "
        f"**Gender:** {student_gender} | "
        f"**House:** {student['HOUSE']}"
    )

    st.write("---")
    st.markdown("### Select Items for Participation")

    df_items = pd.read_excel(DB_ITEMS)
    selected_item_codes = []

    # Create grid for items
    cols = st.columns(3)
    for idx, (_, row_data) in enumerate(df_items.iterrows()):
        code = str(row_data["ITEMCODE"]).strip()
        name = str(row_data["ITEMNAME"]).strip()
        category = str(row_data["ONSTAGE/OFFSTAGE"]).strip().upper()
        sg_type = str(row_data["SINGLE/GROUP"]).strip().upper()
        item_gender = str(row_data.get("BOYS/GIRLS/COMMON", "COMMON")).strip().upper()

        # Rule checking for gender eligibility
        allowed = True
        if item_gender == "BOYS" and student_gender != "MALE":
            allowed = False
        elif item_gender == "GIRLS" and student_gender != "FEMALE":
            allowed = False

        col = cols[idx % 3]

        with col:
            label = f"**{code}** - {name}\n\n*({category} | {sg_type} | {item_gender})*"
            if not allowed:
                st.checkbox(f"{code} - {name} (Not Eligible)", disabled=True, key=f"cb_{code}")
            else:
                is_checked = st.checkbox(f"{code} - {name} ({category} / {sg_type})", key=f"cb_{code}")
                if is_checked:
                    selected_item_codes.append(code)

    st.write("---")

    # Step 2: Confirm and Save Registration (Fixed parameter error)
    if st.button("Confirm & Save Registration", type="primary"):
        if not selected_item_codes:
            st.warning("No items selected for participation!")
        else:
            selected_rows = df_items[df_items["ITEMCODE"].astype(str).str.strip().isin(selected_item_codes)]

            # Check for missing mandatory fields
            has_error = False
            for _, item in selected_rows.iterrows():
                fields_to_check = {
                    "ADM NO": student.get("ADM NO"),
                    "CHESTNO": student.get("CHESTNO"),
                    "STUDENT NAME": student.get("STUDENT NAME"),
                    "CLASS": student.get("CLASS"),
                    "SECTION": student.get("SECTION"),
                    "GENDER": student.get("GENDER"),
                    "HOUSE": student.get("HOUSE"),
                    "ITEMCODE": item.get("ITEMCODE"),
                    "ITEMNAME": item.get("ITEMNAME"),
                    "ONSTAGE/OFFSTAGE": item.get("ONSTAGE/OFFSTAGE"),
                    "SINGLE/GROUP": item.get("SINGLE/GROUP"),
                }

                for field, val in fields_to_check.items():
                    if pd.isna(val) or str(val).strip() == "" or str(val).strip().lower() == "nan":
                        st.error(f"Registration failed! Mandatory field '{field}' is missing or empty.")
                        has_error = True
                        break
                if has_error:
                    break

            if not has_error:
                # Calculate counts for validation rules
                indiv_count = sum(1 for _, r in selected_rows.iterrows() if str(r["SINGLE/GROUP"]).strip().upper() == "SINGLE")
                group_count = sum(1 for _, r in selected_rows.iterrows() if str(r["SINGLE/GROUP"]).strip().upper() == "GROUP")
                onstage_indiv_count = sum(
                    1 for _, r in selected_rows.iterrows() 
                    if str(r["SINGLE/GROUP"]).strip().upper() == "SINGLE" and str(r["ONSTAGE/OFFSTAGE"]).strip().upper() == "ONSTAGE"
                )
                offstage_indiv_count = sum(
                    1 for _, r in selected_rows.iterrows() 
                    if str(r["SINGLE/GROUP"]).strip().upper() == "SINGLE" and str(r["ONSTAGE/OFFSTAGE"]).strip().upper() == "OFFSTAGE"
                )

                # Validation Rule 1: Limit criteria
                if indiv_count > 5 or group_count > 2 or onstage_indiv_count > 3:
                    st.error(
                        f"Criteria Violation!\n\n"
                        f"- Individual Events: {indiv_count} (Max 5)\n"
                        f"- Group Events: {group_count} (Max 2)\n"
                        f"- On-stage Individual: {onstage_indiv_count} (Max 3)"
                    )
                # Validation Rule 2: Off-stage rule when no on-stage event is chosen
                elif onstage_indiv_count == 0 and offstage_indiv_count > 5:
                    st.error("Criteria Violation! A student not participating in any on-stage event may participate in up to 5 off-stage individual events.")
                else:
                    # Append new registration
                    new_records = []
                    for _, item in selected_rows.iterrows():
                        new_records.append({
                            "ADM NO": student["ADM NO"],
                            "CHESTNO": student["CHESTNO"],
                            "STUDENT NAME": student["STUDENT NAME"],
                            "CLASS": student["CLASS"],
                            "SECTION": student["SECTION"],
                            "GENDER": student["GENDER"],
                            "HOUSE": student["HOUSE"],
                            "ITEMCODE": item["ITEMCODE"],
                            "ITEMNAME": item["ITEMNAME"],
                            "ONSTAGE/OFFSTAGE": item["ONSTAGE/OFFSTAGE"],
                            "SINGLE/GROUP": item["SINGLE/GROUP"],
                        })

                    df_new = pd.DataFrame(new_records)

                    if os.path.exists(FILE_PARTICIPANTS):
                        df_existing = pd.read_excel(FILE_PARTICIPANTS)
                        if "Sl. No." in df_existing.columns:
                            df_existing = df_existing.drop(columns=["Sl. No."])
                        df_final = pd.concat([df_existing, df_new], ignore_index=True)
                    else:
                        df_final = df_new

                    df_final.insert(0, "Sl. No.", range(1, len(df_final) + 1))
                    df_final.to_excel(FILE_PARTICIPANTS, index=False)

                    st.balloons()
                    st.success("Registration saved successfully!")
                    st.session_state.selected_student = None
