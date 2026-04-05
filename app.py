import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

DATA_FILE = "runs.json"
GOAL_FILE = "goal.json"


# ---------- Data ----------
def load_runs():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    return pd.read_json(DATA_FILE)


def save_runs(df):
    df.to_json(DATA_FILE, orient="records", indent=4)


def load_goal():
    if not os.path.exists(GOAL_FILE):
        return {"goal_km": 5}
    with open(GOAL_FILE, "r") as f:
        return json.load(f)


def save_goal(goal):
    with open(GOAL_FILE, "w") as f:
        json.dump(goal, f)


def format_pace(pace):
    m = int(pace)
    s = int((pace - m) * 60)
    return f"{m}:{s:02d}"


# ---------- UI ----------
st.set_page_config(layout="wide")
st.title("🏃 AI Running Coach Dashboard")

menu = st.sidebar.selectbox(
    "Menu", ["Add Run", "Dashboard", "Goals", "History"]
)

df = load_runs()
goal = load_goal()


# ---------- Add Run ----------
if menu == "Add Run":
    st.header("➕ Add Run")

    col1, col2 = st.columns(2)

    with col1:
        distance = st.number_input("Distance (km)", 0.1, 100.0)
        heart_rate = st.number_input("Heart Rate (bpm)", 40, 220)

    with col2:
        minutes = st.number_input("Minutes", 0)
        seconds = st.number_input("Seconds", 0, 59)

    if st.button("Save"):
        total_min = minutes + seconds / 60

        if distance > 0 and total_min > 0:
            pace = total_min / distance

            run = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "distance": distance,
                "heart_rate": heart_rate,
                "time_min": total_min,
                "pace": pace
            }

            df = pd.concat([df, pd.DataFrame([run])], ignore_index=True)
            save_runs(df)

            st.success("Run saved!")


# ---------- Dashboard ----------
elif menu == "Dashboard":
    st.header("📊 Performance Dashboard")

    if df.empty:
        st.warning("No data yet.")
    else:
        df["date"] = pd.to_datetime(df["date"])

        total_distance = df["distance"].sum()
        avg_hr = df["heart_rate"].mean()
        avg_pace = df["pace"].mean()

        # Score (lower pace + lower HR = better)
        score = (1 / avg_pace) * (180 / avg_hr)

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Distance", f"{total_distance:.1f} km")
        col2.metric("Avg Pace", format_pace(avg_pace))
        col3.metric("Fitness Score", f"{score:.2f}")

        # Goal progress
        progress = min(total_distance / goal["goal_km"], 1.0)
        st.subheader("🎯 Goal Progress")
        st.progress(progress)
        st.write(f"{total_distance:.1f} / {goal['goal_km']} km")

        # Charts
        st.subheader("📈 Trends")

        fig1 = plt.figure()
        plt.plot(df["date"], df["pace"])
        plt.title("Pace Trend")
        st.pyplot(fig1)

        fig2 = plt.figure()
        plt.plot(df["date"], df["heart_rate"])
        plt.title("Heart Rate Trend")
        st.pyplot(fig2)

        # ---------- AI Insights ----------
        st.subheader("🧠 Coaching Insights")

        if avg_hr > 170:
            st.warning("⚠️ High heart rate: risk of overtraining.")
        elif avg_hr < 120:
            st.info("💡 You can push harder for better gains.")
        else:
            st.success("✅ Good training zone.")

        if len(df) > 3:
            if df["pace"].iloc[-1] < df["pace"].iloc[0]:
                st.success("🔥 Your pace is improving over time!")

        if total_distance < goal["goal_km"] * 0.3:
            st.info("📌 You're early in your goal. Stay consistent!")
        elif total_distance < goal["goal_km"]:
            st.success("🚀 You're making solid progress!")
        else:
            st.balloons()
            st.success("🏁 Goal achieved!")


# ---------- Goals ----------
elif menu == "Goals":
    st.header("🎯 Set Your Goal")

    goal_km = st.number_input("Goal Distance (km)", 1, 100, value=goal["goal_km"])

    if st.button("Save Goal"):
        save_goal({"goal_km": goal_km})
        st.success("Goal updated!")


# ---------- History ----------
elif menu == "History":
    st.header("📜 Run History")

    if df.empty:
        st.warning("No runs yet.")
    else:
        df_display = df.copy()
        df_display["pace"] = df_display["pace"].apply(format_pace)
        st.dataframe(df_display)
