import streamlit as st
import requests
from datetime import date, datetime
import config
import json
import os

st.set_page_config(page_title="Project Digest", layout="wide")
st.title("🗂️ Project Digest")

start_date = st.sidebar.date_input("Start Date", date(2025, 1, 1))
end_date = st.sidebar.date_input("End Date", date.today())


def load_data(filepath):
    with open(filepath) as f:
        return json.load(f)

def filter_project_updates(start_date, end_date):
    project_updates = load_data(os.path.join(config.ROOT_FOLDER, 'data', 'parsed_data', 'project_updates.json'))

    filtered = []

    for entry in project_updates:
        # print(entry)
        date_str = entry.get("date")
        if date_str:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            # print(date, start_date, end_date)
            if (not start_date or date >= start_date) and (not end_date or date <= end_date):
                filtered.append(entry)
    return filtered


if st.sidebar.button("🔁 Re-run Agent"):
    try:
        project_updates = filter_project_updates(start_date, end_date)
        print(len(project_updates))
        response = requests.post(
            f"{config.MCP_APP_HOST}/mcp/tasks",
            json={
                "type": "project_digest",
                "context": {
                    # "start_date": str(start_date),
                    # "end_date": str(end_date),
                    "projects": project_updates
                }
            }
        )
        response.raise_for_status()
        result = response.json()["data"]
        st.session_state["project_digest"] = result
    except Exception as e:
        st.error(f"❌ Failed to contact MCP server: {e}")

digest = st.session_state.get("project_digest", {})
digest = digest.get('result')

if digest:
    project_names = sorted(digest.keys())

    for project in project_names:
        report = digest[project]
        st.subheader(project)
        st.write(f"👤 **Contributors:** {', '.join(report.get('contributors', []))}")
        st.write("📝 **Summary:**")
        st.write(report.get("summary", "No summary available."))
        with st.expander("📂 Raw Updates"):
            for u in report.get("updates", []):
                st.markdown(f"- [{u['date']}] **{u['person']}**: {u['summary']}")
else:
    st.info('Run the agent to get project insights')