import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

# --- PREMIUM GLASS UI & FONT CONFIGURATION ---
def apply_premium_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300&display=swap');
        html, body, [class*="css"], .stText, .stMarkdown {
            font-family: 'Figtree', sans-serif !important;
            font-weight: 300 !important;
        }
        /* Make headers also thin */
        h1, h2, h3 { font-weight: 300 !important; }

        /* Glassmorphism for the login container */
        .login-box {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
        }
        </style>
    """, unsafe_allow_html=True)


apply_premium_ui()

from streamlit_gsheets import GSheetsConnection

# This connection now automatically uses the Service Account credentials
conn = st.connection("gsheets", type=GSheetsConnection)


def save_score(name, score):
    # Calculate numeric reward level
    if score >= 100:
        asterisk_count = 3
    elif score >= 70:
        asterisk_count = 2
    elif score >= 40:
        asterisk_count = 1
    else:
        asterisk_count = 0

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(ttl=0)

        # Store as a number so we can process it visually later
        new_entry = pd.DataFrame([[name, score, asterisk_count]],
                                 columns=['Name', 'Score', 'Asterisks'])
        updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(data=updated_data)

        # Visual feedback for the agent using the logo
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write(f"### Achievement Unlocked!")
        cols = st.columns(5)
        for i in range(asterisk_count):
            with cols[i]:
                # Adjust 'dp_logo.png' to your actual filename
                st.image("dp_logo.png", width=50)
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sync Error: {e}")

    new_entry = pd.DataFrame([[name, score, asterisks]], columns=['Name', 'Score', 'Asterisks'])
    updated_data = pd.concat([existing_data, new_entry], ignore_index=True)

    # Update Google Sheet
    conn.update(data=updated_data)
    st.success(f"Score saved! You earned: {asterisks}")

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Case Reasons Restructure Training", layout="wide")

# --- DATA LOADING ---
# This reads your file and fills in the blanks for the categories
df = pd.read_csv('[CC][GLOBAL] New Case Reasons Restructure - New Case Taxonomy for Efficiency.csv')
df['Case Reason 1 (mandatory)'] = df['Case Reason 1 (mandatory)'].ffill()
df['Case Reason 2 (mandatory)'] = df['Case Reason 2 (mandatory)'].ffill()

# --- INITIALIZE SESSION STATE ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'quiz_complete' not in st.session_state:
    st.session_state.quiz_complete = False
if 'question_solved' not in st.session_state: # Track if the current scenario is finished
    st.session_state.question_solved = False

if 'shuffled_data' not in st.session_state:
    st.session_state.shuffled_data = df.dropna(subset=['Definition / Notes']).sample(frac=1).reset_index(drop=True)

def reset_quiz():
    st.session_state.score = 0
    st.session_state.current_question = 0
    st.session_state.quiz_complete = False
    st.session_state.question_solved = False # Reset this too
    st.session_state.shuffled_data = df.dropna(subset=['Definition / Notes']).sample(frac=1).reset_index(drop=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Menu")
page = st.sidebar.radio("Go to", ["Login", "Explanation", "Practice", "Leaderboard"])
if st.session_state.role == "admin":
    menu = ["Admin Dashboard", "Explanation", "Leaderboard"]
else:
    menu = ["Login", "Explanation", "Practice", "Leaderboard"]

# --- PAGE LOGIC ---
if 'role' not in st.session_state: st.session_state.role = None
if 'country' not in st.session_state: st.session_state.country = None

if page == "Login":
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.title("🛡️ Docplanner Training Portal")

    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Agent Name / ID")
    with col2:
        country = st.selectbox("Market / Country", ["Global", "Spain", "Poland", "Italy", "Brazil", "Mexico"])

    role_type = st.radio("Access Level", ["Agent", "Admin Manager"], horizontal=True)

    password = ""
    if role_type == "Admin Manager":
        password = st.text_input("Admin Security Key", type="password")

    if st.button("Initialize Session"):
        if role_type == "Admin Manager" and password == "DP2026!":  # Set your manager's key
            st.session_state.role = "admin"
            st.session_state.user = username
            st.session_state.country = country
            st.success("Admin Dashboard Unlocked")
            st.rerun()
        elif role_type == "Agent" and username:
            st.session_state.role = "user"
            st.session_state.user = username
            st.session_state.country = country
            st.success(f"Tailored {country} Scenarios Loading...")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Explanation":
    st.title("📚 New Case Taxonomy Guide")
    st.info("Explore the new categories below to understand their purpose and usage.")

    # Get the list of all main categories (Case Reason 1)
    categories = df['Case Reason 1 (mandatory)'].unique()

    for cat1 in categories:
        with st.expander(f"📁 {cat1}"):
            # Get only the rows for this specific main category
            sub_df = df[df['Case Reason 1 (mandatory)'] == cat1]

            # Group by Case Reason 2 to keep it organized
            for cat2 in sub_df['Case Reason 2 (mandatory)'].unique():
                st.markdown(f"### 🔹 {cat2}")

                # Show the individual items (Case Reason 3) and their definitions
                reason3_df = sub_df[sub_df['Case Reason 2 (mandatory)'] == cat2]
                for _, row in reason3_df.iterrows():
                    r3 = row['Case Reason 3 (optional)']
                    definition = row['Definition / Notes']

                    # If there's a Reason 3, show it; otherwise show the definition
                    if pd.notna(r3):
                        st.write(f"**{r3}:** {definition if pd.notna(definition) else 'No definition provided.'}")
                    else:
                        st.write(f"{definition if pd.notna(definition) else 'No definition provided.'}")

                st.write("")  # Add a little space

elif page == "Practice":
    if 'user' not in st.session_state:
        st.warning("Please log in first to save your progress!")
        st.stop()
    st.title("🛠 Interactive Practice")

    if 'user' not in st.session_state:
        st.warning("Please log in first!")
        st.stop()

    practice_df = st.session_state.shuffled_data
    total_questions = 10

    # --- CHEAT SHEET IN SIDEBAR ---
    with st.sidebar:
        st.divider()
        st.subheader("📖 Quick Reference")
        search_term = st.text_input("Search keyword:")
        filtered_df = df[
            df['Definition / Notes'].str.contains(search_term, case=False, na=False)] if search_term else df.head(10)
        for _, row in filtered_df.iterrows():
            with st.expander(f"{row['Case Reason 1 (mandatory)']} > {row['Case Reason 2 (mandatory)']}"):
                st.write(f"**R3:** {row['Case Reason 3 (optional)']}\n\n**Note:** {row['Definition / Notes']}")

    if st.session_state.quiz_complete:
        st.balloons()
        st.success(f"Training Complete, {st.session_state.user}! Final score: {st.session_state.score}")
        if st.button("Restart Practice"):
            reset_quiz()
            st.rerun()
    else:
        current_row = practice_df.iloc[st.session_state.current_question]
        st.info(f"**Scenario {st.session_state.current_question + 1}:** {current_row['Definition / Notes']}")

        # --- DROPDOWNS ---
        options_r1 = sorted(df['Case Reason 1 (mandatory)'].unique().tolist())
        user_choice_r1 = st.selectbox("Select Case Reason 1:", ["-- Choose --"] + options_r1,
                                      key=f"r1_{st.session_state.current_question}")

        user_choice_r2 = "-- Choose --"
        user_choice_r3 = None

        if user_choice_r1 != "-- Choose --":
            options_r2 = sorted(
                df[df['Case Reason 1 (mandatory)'] == user_choice_r1]['Case Reason 2 (mandatory)'].unique().tolist())
            user_choice_r2 = st.selectbox("Select Case Reason 2:", ["-- Choose --"] + options_r2,
                                          key=f"r2_{st.session_state.current_question}")

            if user_choice_r2 != "-- Choose --":
                r3_options = df[(df['Case Reason 1 (mandatory)'] == user_choice_r1) & (
                            df['Case Reason 2 (mandatory)'] == user_choice_r2)][
                    'Case Reason 3 (optional)'].dropna().unique().tolist()
                if r3_options:
                    user_choice_r3 = st.selectbox("Select Case Reason 3 (Optional):", ["-- Choose --"] + r3_options,
                                                  key=f"r3_{st.session_state.current_question}")

        # --- ACTION BUTTONS ---
        st.divider()
        if not st.session_state.question_solved:
            if st.button("Submit Answer"):
                correct_r1 = current_row['Case Reason 1 (mandatory)']
                correct_r2 = current_row['Case Reason 2 (mandatory)']
                correct_r3 = current_row['Case Reason 3 (optional)']

                check_r1 = (user_choice_r1 == correct_r1)
                check_r2 = (user_choice_r2 == correct_r2)
                check_r3 = (user_choice_r3 == correct_r3) if pd.notna(correct_r3) else True

                if check_r1 and check_r2 and check_r3:
                    st.success("🎯 Correct! +10 points")
                    st.session_state.score += 10
                    st.session_state.question_solved = True
                    st.rerun()
                else:
                    st.error("❌ Not quite. -5 points. Check the sidebar and try again!")
                    st.session_state.score -= 5
        else:
            st.success(
                f"Correct! Path: {current_row['Case Reason 1 (mandatory)']} → {current_row['Case Reason 2 (mandatory)']}")

            if st.button("Move to Next Scenario ➡️"):
                if st.session_state.current_question + 1 < total_questions:
                    st.session_state.current_question += 1
                    st.session_state.question_solved = False
                    st.rerun()
                else:
                    # THIS IS THE PART YOU WERE LOOKING FOR:
                    # Save the final score to the CSV file
                    save_score(st.session_state.user, st.session_state.score)
                    # Mark the quiz as finished
                    st.session_state.quiz_complete = True
                    st.rerun()



elif page == "Leaderboard":
    st.title("🏆 Global Wall of Fame")
    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        df_leaderboard = conn.read(ttl="1m")
        if not df_leaderboard.empty:
            df_leaderboard = df_leaderboard.sort_values(by='Score', ascending=False)

            for _, row in df_leaderboard.head(10).iterrows():
                # Glassmorphism row for each agent
                with st.container():
                    st.markdown(f"""
                        <div style="background: rgba(255, 255, 255, 0.05); 
                                    padding: 15px; border-radius: 10px; margin-bottom: 10px;
                                    display: flex; align-items: center; justify-content: space-between;">
                            <span style="font-size: 20px;">{row['Name']}</span>
                            <span style="font-weight: bold; color: #29b5e8;">{row['Score']} pts</span>
                        </div>
                    """, unsafe_allow_html=True)

                    # Row for the reward logos
                    cols = st.columns(10)
                    count = int(row['Asterisks']) if pd.notna(row['Asterisks']) else 0
                    for i in range(count):
                        with cols[i]:
                            st.image("dp_logo.png", width=30)

        else:
            st.info("The leaderboard is currently empty.")
    except Exception as e:
        st.error("GCP Sync Status: Offline. Check Secrets.")

elif page == "Admin Dashboard":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("⚙️ System Management")

    col1, col2, col3 = st.columns(3)

    # 1. Google Sheets Sync
    with col1:
        st.write("**Google Sheets API**")
        st.success("Connected")

    # 2. Google Drive Label API (as requested)
    with col2:
        st.write("**G-Drive Label Sync**")
        st.warning("Idle")  # Ready for Step 2 if you enable the API

    # 3. Vertex AI Status
    with col3:
        st.write("**Vertex AI (Gemini)**")
        st.success("Active")

    st.divider()
    st.write("### Cloud Metadata")
    st.json({
        "Project ID": st.secrets["connections"]["gsheets"]["project_id"],
        "Service Account": st.secrets["connections"]["gsheets"]["client_email"],
        "SSync Method": "GCP Service Account Auth"
    })
    st.markdown('</div>', unsafe_allow_html=True)