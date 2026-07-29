import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
DB_STUDENTS = "studentdb4.xlsx"
DB_ITEMS = "items4.xlsx"

# Admin Password from Secrets
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "Admin@SKPS2026!")

# Page Setup
st.set_page_config(
    page_title="SKPS Youth Festival - Category IV Entry",
    layout="wide"
)

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# HELPER FUNCTIONS FOR GOOGLE SHEETS STORAGE
# ==========================================
def load_participants():
    """Safely reads participant registrations from Google Sheets."""
    try:
        # Read data from the 'Participants' worksheet
        df = conn.read(worksheet="Participants", ttl=0)  # ttl=0 disables caching for real-time reads
        df = df.dropna(how="all")  # Drop completely empty rows
        return df
    except Exception:
        return pd.DataFrame()

def save_participants(df_updated):
    """Overwrites the Google Sheet with updated participant registrations."""
    conn.update(worksheet="Participants", data=df_updated)

# Initialize Session State
if "selected_student" not in st.session_state:
    st.session_state.selected_student = None

# ==========================================
# SIDEBAR - ADMIN PANEL
# ==========================================
st.sidebar.title("🔒 Admin Panel")
admin_password_input = st.sidebar.text_input("Enter Admin Password", type="password")

if admin_password_input == ADMIN_PASSWORD:
    st.sidebar.success("Admin Authenticated")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Admin Controls")

    df_current = load_participants()

    # 1. View & Download Data
    if not df_current.empty:
        st.sidebar.markdown(f"**Total Registered Entries:** {len(df_current)}")
        
        # Download button converts live Google Sheet data to Excel download
        excel_bytes = pd.ExcelWriter("temp.xlsx")
        df_current.to_excel(excel_bytes, index=False)
        excel_bytes.close()

        with open("temp.xlsx", "rb") as f:
            st.sidebar.download_button(
                label="📥 Download Participants List (.xlsx)",
                data=f.read(),
                file_name="participantslist_Category4.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.sidebar.info("No registration data available yet.")

    st.sidebar.markdown("---")

    # 2. Clear All Data (Clears Google Sheet)
    if st.sidebar.button("⚠️ Clear All Registration Data", use_container_width=True):
        empty_df = pd.DataFrame(columns=[
            "Sl. No.", "ADM NO", "CHESTNO", "STUDENT NAME", "CLASS", 
            "SECTION", "GENDER", "HOUSE", "ITEMCODE", "ITEMNAME", 
            "ONSTAGE/OFFSTAGE", "SINGLE/GROUP"
        ])
        save_participants(empty_df)
        st.sidebar.success("All participant data has been cleared from Google Sheets!")
        st.rerun()

elif admin_password_input:
    st.sidebar.error("Incorrect Password!")
else:
    st.sidebar.info("Enter password to unlock Admin controls.")

# ==========================================
# MAIN APP - ENTRY FOR PARTICIPATION
# ==========================================
st.title("SKPS YOUTH FESTIVAL SUVARNNAM 2026")
st.subheader("CATEGORY IV - 1. ENTRY FOR PARTICIPATION")
st.markdown("---")

# Step 1: Admission Number Input & Search
adm_no_input = st.text_input("Enter Admission No:", placeholder="e.g., 1001").strip()

if st.button("Fetch Student", type="primary"):
    if not adm_no_input:
        st.warning("Please enter an Admission Number.")
    else:
        # Check if already registered in Google Sheet
        already_registered = False
        df_existing = load_participants()
        
        if not df_existing.empty and "ADM NO" in df_existing.columns:
            registered_adms = df_existing["ADM NO"].astype(str).str.strip().tolist()
            if adm_no_input in registered_adms:
                already_registered = True

        if already_registered:
            st.error(f"Registration Blocked: Student with Admission No. '{adm_no_input}' is already registered!")
            st.session_state.selected_student = None
        else:
            # Fetch Student Details from local database file
            if pd.io.common.file_exists(DB_STUDENTS):
                df_stud = pd.read_excel(DB_STUDENTS)
                df_stud["ADM NO"] = df_stud["ADM NO"].astype(str).str.strip()
                student_match = df_stud[df_stud["ADM NO"] == adm_no_input]

                if student_match.empty:
                    st.error("Admission Number not found!")
                    st.session_state.selected_student = None
                else:
                    st.session_state.selected_student = student_match.iloc[0].to_dict()
            else:
                st.error(f"Student database file '{DB_STUDENTS}' not found in repository.")

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

    if pd.io.common.file_exists(DB_ITEMS):
        df_items = pd.read_excel(DB_ITEMS)
        selected_item_codes = []

        # Grid view for items
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
                if not allowed:
                    st.checkbox(f"{code} - {name} (Not Eligible)", disabled=True, key=f"cb_{code}")
                else:
                    is_checked = st.checkbox(f"{code} - {name} ({category} / {sg_type})", key=f"cb_{code}")
                    if is_checked:
                        selected_item_codes.append(code)

        st.write("---")

        # Step 2: Confirm and Save Registration
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
                        # Prepare records to save
                        new_records = []
                        for _, item in selected_rows.iterrows():
                            new_records.append({
                                "ADM NO": str(student["ADM NO"]),
                                "CHESTNO": str(student["CHESTNO"]),
                                "STUDENT NAME": str(student["STUDENT NAME"]),
                                "CLASS": str(student["CLASS"]),
                                "SECTION": str(student["SECTION"]),
                                "GENDER": str(student["GENDER"]),
                                "HOUSE": str(student["HOUSE"]),
                                "ITEMCODE": str(item["ITEMCODE"]),
                                "ITEMNAME": str(item["ITEMNAME"]),
                                "ONSTAGE/OFFSTAGE": str(item["ONSTAGE/OFFSTAGE"]),
                                "SINGLE/GROUP": str(item["SINGLE/GROUP"]),
                            })

                        df_new = pd.DataFrame(new_records)
                        df_existing = load_participants()

                        if not df_existing.empty:
                            if "Sl. No." in df_existing.columns:
                                df_existing = df_existing.drop(columns=["Sl. No."])
                            df_final = pd.concat([df_existing, df_new], ignore_index=True)
                        else:
                            df_final = df_new

                        df_final.insert(0, "Sl. No.", range(1, len(df_final) + 1))
                        
                        # Save directly to Google Sheet
                        save_participants(df_final)

                        st.balloons()
                        st.success("Registration saved successfully to Google Sheets!")
                        st.session_state.selected_student = None
    else:
        st.error(f"Items database file '{DB_ITEMS}' not found in repository.")
