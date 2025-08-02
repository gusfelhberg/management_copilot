from notion_client import Client
from dotenv import load_dotenv
import requests 
from tqdm import tqdm
from dateutil import parser
import config

load_dotenv()

notion = Client(auth=config.NOTION_API_KEY)

headers = {'Authorization': f"Bearer {config.NOTION_API_KEY}", 
           'Content-Type': 'application/json', 
           'Notion-Version': '2022-06-28'}

def query_database(database_id):
    results = []
    next_cursor = None

    while True:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=next_cursor,
            page_size=100
        )
        results.extend(response['results'])

        if response.get("has_more"):
            next_cursor = response["next_cursor"]
        else:
            break

    return results

def get_project_ids(meeting_page):
    project_ids = []
    for key in meeting_page['properties'].keys():
        if "Project" in key:
            project_ids = [project['id'] for project in meeting_page['properties'][key]['relation']]
    return project_ids

def get_project_names(project_ids):
    project_names = []
    for project_id in project_ids:
        p_name = notion.pages.retrieve(page_id=project_id)['properties']['Name']['title'][0]['plain_text']
        project_names.append(p_name)
    return project_names

def get_block_content(block_id, content_list=None):

    valid_text_types = ['heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'paragraph']

    if not content_list:
        content_list = []
    blocks_response = requests.get(f"https://api.notion.com/v1/blocks/{block_id}/children", headers=headers).json()['results']
    for block in blocks_response:
        block_id = block['id']
        text_type = list(block.keys())[-1]

        if text_type in valid_text_types and 'rich_text' in block[text_type]:
            if len(block[text_type]['rich_text']) > 0:
                block_text = block[text_type]['rich_text'][0]['plain_text']
                content_list.append(block_text)
            
        if block['has_children'] is True:
            content_list = get_block_content(block_id, content_list)

    return content_list


def get_1_on_1_data(meeting_pages):

    meetings_data = []
    for meeting_page in tqdm(meeting_pages):
        meeting_type = meeting_page['properties']['Meeting Type']['select']['name'] if meeting_page['properties']['Meeting Type']['select'] else None

        if meeting_type == '1-1':
            meeting_id = meeting_page['id']
            meeting_name = meeting_page['properties']['Name']['title'][0]['plain_text']
            meeting_date_start = str(parser.parse(meeting_page['properties']['Meeting Date']['date']['start']).date())
            meeting_date_end = str(parser.parse(meeting_page['properties']['Meeting Date']['date']['end']).date()) if meeting_page['properties']['Meeting Date']['date']['end'] else None
            meeting_participant = meeting_name.split(' - ')[1]
            stress = meeting_page['properties']['Stress']['number']
            happiness = meeting_page['properties']['Happiness']['number']
            professional_development = meeting_page['properties']['Professional Development']['rich_text'][0]['plain_text'] if len(meeting_page['properties']['Professional Development']['rich_text']) > 0 else None
            topics_to_discuss = meeting_page['properties']['Topics to Discuss']['rich_text'][0]['plain_text'] if len(meeting_page['properties']['Topics to Discuss']['rich_text']) > 0 else None
            challenges_roadblocks = meeting_page['properties']['Challenges and Roadblocks']['rich_text'][0]['plain_text'] if len(meeting_page['properties']['Challenges and Roadblocks']['rich_text']) > 0 else None
            stress_details = meeting_page['properties']['Stress Details']['rich_text'][0]['plain_text'] if len(meeting_page['properties']['Stress Details']['rich_text']) > 0 else None
            happiness_details = meeting_page['properties']['Happiness Details']['rich_text'][0]['plain_text'] if len(meeting_page['properties']['Happiness Details']['rich_text']) > 0 else None


            meetings_data.append({
                'meeting_page_id': meeting_id,
                'meeting_date_start': meeting_date_start,
                'meeting_date_end': meeting_date_end,
                'meeting_participant': meeting_participant,
                'meeting_type': meeting_type,
                'stress': stress,
                'stress_details': stress_details,
                'happiness': happiness,
                'happiness_details': happiness_details,
                'professional_development': professional_development,
                'topics_to_discuss': topics_to_discuss,
                'challenges_roadblocks': challenges_roadblocks,
            })
    return meetings_data

def get_meetings_data(meeting_pages, meeting_types=[]):

    meetings_data = []
    for meeting_page in tqdm(meeting_pages):
        meeting_type = meeting_page['properties']['Meeting Type']['select']['name'] if meeting_page['properties']['Meeting Type']['select'] else None

        if meeting_type and (meeting_types == [] or (meeting_types != [] and meeting_type in meeting_types)):
            meeting_id = meeting_page['id']
            meeting_name = meeting_page['properties']['Name']['title'][0]['plain_text']
            meeting_date_start = str(parser.parse(meeting_page['properties']['Meeting Date']['date']['start']).date())
            meeting_date_end = str(parser.parse(meeting_page['properties']['Meeting Date']['date']['end']).date()) if meeting_page['properties']['Meeting Date']['date']['end'] else None
            meeting_participants = [name['title'][0]['plain_text'] for name in meeting_page['properties']['PersonName']['rollup']['array']]
            if len(meeting_participants) == 1:
                meeting_participants = meeting_participants[0]
            stress = meeting_page['properties']['Stress']['number']
            happiness = meeting_page['properties']['Happiness']['number']
            meeting_project_names = get_project_names(get_project_ids(meeting_page))
            meeting_content = "\n".join(get_block_content(meeting_id))

            meetings_data.append({
                'meeting_page_id': meeting_id,
                'meeting_name': meeting_name,
                'meeting_date_start': meeting_date_start,
                'meeting_date_end': meeting_date_end,
                'meeting_participants': meeting_participants,
                'meeting_type': meeting_type,
                'stress': stress,
                'happiness': happiness,
                'meeting_project_names': meeting_project_names,
                'meeting_content': meeting_content
            })
    return meetings_data

def get_project_updates_data(project_updates_pages):
    project_updates_data = []
    for update_page in tqdm(project_updates_pages):
        if len(update_page['properties']['Name']['title']) > 0:
            update_summary = update_page['properties']['Name']['title'][0]['plain_text']
            update_project = get_project_names(get_project_ids(update_page))[0]
            update_next_steps = update_page['properties']['Next Steps']['rich_text'][0]['plain_text'] if len(update_page['properties']['Next Steps']['rich_text']) > 0 else None
            update_person = [notion.pages.retrieve(page_id=person_id['id'])['properties']['Name']['title'][0]['plain_text'] for person_id in update_page['properties']['Reported by']['relation']][0]
            update_date = update_page['properties']['Update Date']['date']['start']
            update_type = update_page['properties']['Update Type']['select'].get('name') if update_page['properties']['Update Type']['select'] else None

            project_updates_data.append({
                'summary': update_summary,
                'date': update_date,
                'next_steps': update_next_steps,
                'person': update_person,
                'update_type': update_type,
                'project': update_project
            })
    return project_updates_data

def get_people_updates(people_updates):
    people_updates_data = []
    for update in tqdm(people_updates):
        try:
            update_date = update['properties']['Date']['date']['start']
            update_person = notion.pages.retrieve(page_id=update['properties']['People DB']['relation'][0]['id'])['properties']['Name']['title'][0]['plain_text']
            update_details = update['properties']['Details']['rich_text'][0]['plain_text'] if len(update['properties']['Details']['rich_text']) > 0 else None
            
            people_updates_data.append({
                'date': update_date,
                'person': update_person,
                'details': update_details
            })
        except:
            pass
    return people_updates_data



def get_team_members():

    people = query_database(config.PEOPLE_DATABASE_ID)
    return sorted([person['properties']['Name']['title'][0]['plain_text'] for person in people if person['properties']['DataMLTeam']['checkbox']])