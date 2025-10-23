import json, os

DATA_FILE = "project_data.json"

def load_last_project_data(project_name):
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return data.get(project_name)

def save_project_data(project_name, form_data):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data[project_name] = form_data
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
