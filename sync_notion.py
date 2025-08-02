import json


import os

from config import ROOT_FOLDER
import sys
sys.path.append(ROOT_FOLDER)

from notion_client_helper import (
    query_database, get_meetings_data, get_1_on_1_data,
    get_project_updates_data, get_people_updates
)
from notion_config import (
    TEAM_1ON1_DATABASE_ID,
    PROJECT_UPDATES_DATABASE_ID,
    PEOPLE_UPDATES_DATABASE_ID
)

def save_to_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def sync_team_1on1():
    pages = query_database(TEAM_1ON1_DATABASE_ID)
    meetings_data = get_1_on_1_data(pages)
    save_to_json(meetings_data, os.path.join(ROOT_FOLDER, "data/parsed_data/team_1on1.json"))

def sync_project_updates():
    pages = query_database(PROJECT_UPDATES_DATABASE_ID)
    project_updates_data = get_project_updates_data(pages)
    save_to_json(project_updates_data, os.path.join(ROOT_FOLDER, "data/parsed_data/project_updates.json"))

def sync_people_updates():
    pages = query_database(PEOPLE_UPDATES_DATABASE_ID)
    people_updates_data = get_people_updates(pages)
    save_to_json(people_updates_data, os.path.join(ROOT_FOLDER, "data/parsed_data/people_updates.json"))

    

if __name__ == "__main__":
    print("🔄 Syncing Notion data...")
    print("📅 Syncing Team 1-on-1 meetings...")
    sync_team_1on1()
    print("📊 Syncing Project Updates...")
    sync_project_updates()
    print("👥 Syncing People Updates...")
    sync_people_updates()
    print("✅ Notion sync complete.")