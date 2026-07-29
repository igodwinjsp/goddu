import os
import pandas as pd
import streamlit as st
from filelock import FileLock

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
DB_STUDENTS = "studentdb4.xlsx"
DB_ITEMS = "items4.xlsx"
FILE_PARTICIPANTS = "participantslist.xlsx"
LOCK_FILE = "participantslist.xlsx.lock"

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "Admin@SKPS2026!")

st.set_page_config(
    page_title="SKPS Youth Festival - Category IV Entry",
    layout="wide"
)

# ==========================================
# SAFE CONCURRENT FILE HANDLING (FILELOCK)
# ==========================================
def safe_load_participants():
    """Safely reads participant registrations using a file lock."""
    lock = FileLock(LOCK_FILE, timeout=10)
    with lock:
        if not os.path.exists(FILE_PARTICIPANTS) or os.path.getsize(FILE_PARTICIPANTS) == 0:
            return pd.DataFrame()
        try:
            return pd.read_excel(FILE_PARTICIPANTS)
        except Exception:
            return pd.DataFrame()

def safe_append_participants(new_records):
    """
    Safely appends new registration rows while locking the file 
    so concurrent users cannot overwrite each other's data.
    """
    lock = FileLock(LOCK_FILE, timeout=15)
    with lock:
        df_new = pd.DataFrame(new_records)

        # Read existing inside the lock block
        if os.path.exists(FILE_PARTICIPANTS) and os.path.getsize(FILE_PARTICIPANTS) > 0:
            try:
                df_existing = pd.read_excel(FILE_PARTICIPANTS)
            except Exception:
                df_existing = pd.DataFrame()
        else:
            df_existing = pd.DataFrame()

        if not df_existing.empty:
            if "Sl. No." in df_existing.columns:
                df_existing = df_existing.drop(columns=["Sl. No."])
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.insert(0, "Sl. No.", range(1, len(df_final) + 1))
        
        # Save back to disk securely
        df_final.to_excel(FILE_PARTICIPANTS, index=False)

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

    df_current = safe_load_participants()

    if not df_current.empty:
        st.sidebar.markdown(f"**Total Registered Entries:** {len(df_current)}")
        
        with open(FILE_PARTICIPANTS, "rb") as f:
            st.sidebar.download_button(
                label="📥 Download Participants List (.xlsx)",
                data=f.read(),
                file_name="participantslist_Category4.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.sidebar.info("No registration data available to download yet.")

    st.sidebar.markdown("---")

    if st.sidebar.button("⚠️ Clear All Registration Data", use_container_width=True):
        lock = FileLock(LOCK_FILE, timeout=10)
        with lock:
            if os.path.exists(FILE_PARTICIPANTS):
                os.remove(FILE_PARTICIPANTS)
        st.sidebar.success("All participant data has been cleared!")
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

adm_no_input = st.text_input("Enter Admission No:", placeholder="e.g., 1001").strip()

if st.button("Fetch Student", type="primary"):
    if not adm_no_input:
        st.warning("Please enter an Admission Number.")
    else:
        df_existing = safe_load_participants()
        already_registered = False
        
        if not df_existing.empty and "ADM NO" in df_existing.columns:
            registered_adms = df_existing["ADM NO"].astype(str).str.strip().tolist()
            if adm_no_input in registered_adms:
                already_registered = True

        if already_registered:
            st.error(f"Registration Blocked: Student with Admission No. '{adm_no_input}' is already registered!")
            st.session_state.selected_student = None
        else:
            if os.path.exists(DB_STUDENTS):
                df_stud = pd.read_excel(DB_STUDENTS)
                df_stud["ADM NO"] = df_stud["ADM NO"].astype(str).str.strip()
                student_match = df_stud[df_stud["ADM NO"] == adm_no_input]

                if student_match.empty:
                    st.error("Admission Number not found!")
                    st.session_state.selected_student = None
                else:
                    st.session_state.selected_student = student_match.iloc[0].to_dict()
            else:
                st.error(f"Student database file '{DB_STUDENTS}' not found.")

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

    if os.path.exists(DB_ITEMS):
        df_items = pd.read_excel(DB_ITEMS)
        selected_item_codes = []

        cols = st.columns(3)
        for idx, (_, row_data) in enumerate(df_items.iterrows()):
            code = str(row_data["ITEMCODE"]).strip()
            name = str(row_data["ITEMNAME"]).strip()
            category = str(row_data["ONSTAGE/OFFSTAGE"]).strip().upper()
            sg_type = str(row_data["SINGLE/GROUP"]).strip().upper()
            item_gender = str(row_data.get("BOYS/GIRLS/COMMON", "COMMON")).strip().upper()

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

        if st.button("Confirm & Save Registration", type="primary"):
            if not selected_item_codes:
                st.warning("No items selected for participation!")
            else:
                selected_rows = df_items[df_items["ITEMCODE"].astype(str).str.strip().isin(selected_item_codes)]

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

                    if indiv_count > 5 or group_count > 2 or onstage_indiv_count > 3:
                        st.error(
                            f"Criteria Violation!\n\n"
                            f"- Individual Events: {indiv_count} (Max 5)\n"
                            f"- Group Events: {group_count} (Max 2)\n"
                            f"- On-stage Individual: {onstage_indiv_count} (Max 3)"
                        )
                    elif onstage_indiv_count == 0 and offstage_indiv_count > 5:
                        st.error("Criteria Violation! A student not participating in any on-stage event may participate in up to 5 off-stage individual events.")
                    else:
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

                        # Safely append using file locking
                        safe_append_participants(new_records)

                        st.balloons()
                        st.success("Registration saved successfully!")
                        st.session_state.selected_student = None
    else:
        st.error(f"Items database file '{DB_ITEMS}' not found.")
