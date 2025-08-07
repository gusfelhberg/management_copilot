import streamlit as st
import requests
from datetime import date
import sys
from pathlib import Path
import json
import config
from datetime import datetime
# sys.path.append(str(Path(__file__).resolve().parent))
from memory_utils import load_memory, save_message
from sync_notion import sync_team_1on1, sync_people_updates
from notion_client_helper import get_team_members
import os

st.set_page_config(page_title="Team Insight", layout="wide")
state = st.session_state


def load_data(filepath):
    with open(filepath) as f:
        return json.load(f)

def filter_team_data(records, start_date, end_date):
    team_updates = load_data(os.path.join(config.ROOT_FOLDER, 'data', 'parsed_data', 'project_updates.json'))

    filtered = []

    for entry in records:

        date_str = entry.get("date")
        if date_str:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if (not start_date or date >= start_date) and (not end_date or date <= end_date):
                filtered.append(entry)
    return filtered

def data_config():

    if st.sidebar.button("🔁 Sync 1-on-1 Data"):
        with st.spinner("Syncing Team 1-on-1 data..."):
            sync_team_1on1()
        with st.spinner("Syncing People Updates..."):
            sync_people_updates()
        st.success('Data synced successfully')

    if "team_1_on_1s" not in state:
        state['team_1_on_1s'] = dict()
    if "team_manager_updates" not in state:
        state['team_manager_updates'] = dict()
    if "complete" not in state["team_1_on_1s"]:
        state["team_1_on_1s"]["complete"] = load_data(os.path.join(config.ROOT_FOLDER, "data", "parsed_data", "team_1on1.json"))
    if "complete" not in state["team_manager_updates"]:
        state["team_manager_updates"]["complete"] = load_data(os.path.join(config.ROOT_FOLDER, "data", "parsed_data", "people_updates.json"))

    st.sidebar.caption(f'Loaded **{len(state["team_1_on_1s"]["complete"])}** 1-on-1 entries.')
    st.sidebar.caption(f'Loaded **{len(state["team_manager_updates"]["complete"])}** manager update entries.')

    if 'team_members' not in st.session_state:
        state['team_members'] = get_team_members()

    team_member = st.sidebar.selectbox(
        "Select Team Members",
        options=['Select'] + state['team_members']
    )

    if team_member != 'Select':
        if st.sidebar.button("🔁 Re-run Agent"):
            if "team_insight" not in state:
                state['team_insight'] = dict()

            if team_member not in state['team_1_on_1s']:
                state['team_1_on_1s'][team_member] = [meeting for meeting in state["team_1_on_1s"]["complete"] if meeting['meeting_participant'] == team_member]
                state['team_manager_updates'][team_member] = [update for update in state["team_manager_updates"]["complete"] if update['person'] == team_member]
            
            try:
                with st.spinner(f'Updating insights for {team_member}...'):
                    response = requests.post(
                        f"{config.MCP_APP_HOST}/mcp/tasks",
                        json={
                            "type": "team_insight",
                            "context": {
                                "team_member": team_member,
                                "one_on_ones": state['team_1_on_1s'][team_member],
                                "manager_updates": state['team_manager_updates'][team_member]
                            }
                        }
                    )
                    response.raise_for_status()
                    result = response.json()["data"]["result"][team_member]

                    state["team_insight"][team_member] = result
            except Exception as e:
                st.error(f"❌ Failed to contact MCP server for {team_member}: {e}")
                pass

def display_team_insight():

    # insights = state.get("team_insight", {})
    if "team_insight" in state:
        tab_labels = sorted(list(state["team_insight"].keys()))
        if len(tab_labels) > 0:
            tabs = st.tabs(tab_labels)
            for tab, person in zip(tabs, tab_labels):
                with tab:
                    insight = state["team_insight"][person]
                    cols = st.columns(3)
                    cols[0].metric("Average Stress", insight.get("average_stress", "N/A"))
                    cols[1].metric("Average Happiness", insight.get("average_happiness", "N/A"))

                    st.subheader("🧠 Overall")
                    st.write(insight.get("summary", "No summary available."))

                    if insight.get("performance_assessment"):
                        st.subheader("🎯 Performance Assessment")
                        st.write('\n'.join(['- ' + item for item in insight["performance_assessment"]]))

                    if insight.get("flight_risk_indicators"):
                        st.subheader("🎯 Flight Risk Indicators")
                        st.write('\n'.join(['- ' + item for item in insight["flight_risk_indicators"]]))

                    if insight.get("development_opportunities"):
                        st.subheader("🎯 Development Opportunities")
                        st.write('\n'.join(['- ' + item for item in insight["development_opportunities"]]))

                    if insight.get("feedback_for_next_1on1"):
                        st.subheader("🎯 Feedback for Next 1-on-1")
                        st.write('\n'.join(['- ' + item for item in insight["feedback_for_next_1on1"]]))

                    if insight.get("notable_trends"):
                        st.subheader("🎯 Notable Trends")
                        st.write('\n'.join(['- ' + item for item in insight["notable_trends"]]))

                    if insight.get("other_observations"):
                        st.subheader("🎯 Other Observations")
                        st.write('\n'.join(['- ' + item for item in insight["other_observations"]]))

                    if insight.get("manager_action_suggestions"):
                        st.subheader("🎯 Manager Action Suggestions")
                        st.write('\n'.join(['- ' + item for item in insight["manager_action_suggestions"]]))

                    if "additional" in insight:
                        st.subheader("📌 Additional Insights")
                        st.write(insight["additional"])

                    if insight.get("mood_plot"):
                        st.image(insight["mood_plot"])
                    if insight.get("flight_risk"):
                        st.error("⚠️ Potential Flight Risk")

                    display_team_member_chat(person)



def display_team_member_chat(person):
    ####################################
    # --- Chat component for each person ---
    st.divider()
    st.subheader(f"💬 Chat about {person}")
    agent_type = f"team_insight_{person}"
    chat_history = load_memory(agent_type)

    # Load context: project updates and 1-1s for this person
    # Project updates
    try:
        with open(os.path.join(config.ROOT_FOLDER, 'data', 'parsed_data', 'project_updates.json')) as f:
            project_updates = [u for u in json.load(f) if u.get("person") == person]
    except Exception:
        project_updates = []
    # 1-1s
    try:
        with open(os.path.join(config.ROOT_FOLDER, 'data', 'parsed_data', 'team_1on1.json')) as f:
            one_on_ones = [m for m in json.load(f) if m.get("meeting_participants") == person]
    except Exception:
        one_on_ones = []

    # manager updates
    try:
        with open(os.path.join(config.ROOT_FOLDER, 'data', 'parsed_data', 'people_updates.json')) as f:
            manager_updates = [m for m in json.load(f) if m.get("person") == person]
    except Exception:
        manager_updates = []

    # Display chat history
    for entry in chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["message"])

    # Chat input
    if prompt := st.chat_input(f"Chat with agent about {person}..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        save_message(agent_type, "user", prompt)

        # Compose context for agent
        context = {
            "person": person,
            "project_updates": project_updates,
            "one_on_ones": one_on_ones,
            "manager_updates": manager_updates,
            "chat": chat_history + [{"role": "user", "message": prompt}]
        }

        # Call MCP agent
        try:
            response = requests.post(
                f"{config.MCP_APP_HOST}/mcp/tasks",
                json={
                    "type": "team_insight_chat",
                    "context": context
                }
            )
            response.raise_for_status()
            result = response.json()["data"]
            
            agent_reply = result
            
        except Exception as e:
            agent_reply = f"⚠️ Error: {e}"

        save_message(agent_type, "agent", agent_reply)
        with st.chat_message("agent"):
            st.markdown(agent_reply)

def main():
    st.title("👥 Team Insight")
    data_config()
    display_team_insight()
    


if __name__=="__main__":
    
    main()