import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection


def save_score(name, score):
    conn = st.connection("gsheets", type=GSheetsConnection)
    # We read the current data to append the new score
    try:
        existing_data = conn.read(ttl=0)  # ttl=0 ensures we don't use old cached data
    except:
        existing_data = pd.DataFrame(columns=['Name', 'Score'])

    new_entry = pd.DataFrame([[name, score]], columns=['Name', 'Score'])
    updated_data = pd.concat([existing_data, new_entry], ignore_index=True)

    # This writes back to the Google Sheet
    conn.update(data=updated_data)

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

# --- PAGE LOGIC ---
if page == "Login":
    st.title("🔐 Agent Login")
    agent_name = st.text_input("Enter your Full Name or Agent ID:", placeholder="e.g. John Doe")

    if st.button("Login"):
        if agent_name:
            st.session_state.user = agent_name
            st.success(f"Welcome, {agent_name}! You can now go to the Practice section.")
        else:
            st.warning("Please enter a name to track your score.")

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
    st.title("🏆 Global Leaderboard")
    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        df_leaderboard = conn.read(ttl="1m")  # Refresh every minute
        if not df_leaderboard.empty:
            df_leaderboard = df_leaderboard.sort_values(by='Score', ascending=False).reset_index(drop=True)
            # Display the Top 10 in a clean table
            st.subheader("Top Performers")
            st.table(df_leaderboard.head(10))

            # Visual Chart for the Top 5
            st.divider()
            st.subheader("Performance Visualization")
            st.bar_chart(data=df_leaderboard.head(5), x="Name", y="Score", color="#29b5e8")

        else:
            st.info("The leaderboard is currently empty. Be the first to complete the training!")
    except Exception as e:
        st.error("Could not connect to Google Sheets. Check your Secrets configuration.")