from typing import Any, Dict
import requests
from valispace import API
from .settings import EPSILON3_API_KEY, EPSILON3_TEAM_KEY
import datetime
from datetime import datetime

# set the API endpoint URL
e3_endpoint = {
    "runs": 'https://api.epsilon3.io/v1/runs',
    "commands": 'https://api.epsilon3.io/v1/commands',
    "procedures": 'https://api.epsilon3.io/v1/procedures/summary'
    }

VALISPACE = {
    "domain": "http://valispace",  # Base URL for the Valispace instance, if the deployment is an onprem deployment this should be set to "hhtp://valispace"
    "warn_https": False,  # Disable HTTPS warnings if set to False
}

# Define project id
project_id = 24

# ---------------------------------------------

def initialize_api(temporary_access_token) -> API:
    """
    Initialize the Valispace API.

    Returns:
        API: Initialized Valispace API object.
    """
    # Initialize and return the Valispace API with the domain and temporary access token
    return API(
        url=VALISPACE["domain"],
        session_token=temporary_access_token,
        warn_https=VALISPACE.get("warn_https", False)
    )

def fetch_vm_id(api, project_id):
    """
    Fetches the ID of the Verification Method with the name 'Epsilon3 Test' from the given project.
    If it doesn't exist, creates it and returns the new ID.

    Parameters:
    api (object): The API client instance to make requests.
    project_id (int): The ID of the project from which to fetch or create the Verification Method.

    Returns:
    int: The ID of the 'Epsilon3 Test' Verification Method.
    """
    # Fetch all verification methods for the project
    response = api.request("POST", 'requirements/verification-methods/search/', {
        "query_filters": {"project_id": project_id},
        "size": -1
    })

    # Extract the list of verification methods
    verification_methods = response.get("data", [])

    # Search for the verification method with the name 'Epsilon3 Test'
    for vm in verification_methods:
        if vm.get("name") == "Epsilon3 Test":
            return vm.get("id")

    # If not found, create a new verification method with the name 'Epsilon3 Test'
    create_response = api.request("POST", 'requirements/component-vms/', {
        "project": project_id,
        "name": "Epsilon3 Test"
    })

    # Return the ID of the newly created verification method
    return create_response.get("id")

def create_e3_run(api, run_url, procedure_id, run_name):
    # set the request headers with the API key for authentication
    headers = {
        'Authorization': 'Basic ' + EPSILON3_API_KEY
    }

    # set the request body with the procedure ID and variables
    body = {
        'procedure_id': procedure_id
        # 'variables': variables
    }

    # send the POST request to create a new run
    e3_run_response = requests.post(run_url, auth=(EPSILON3_API_KEY,''), json=body)

    print(e3_run_response)

    e3_run = e3_run_response.json()

    print(e3_run)

    # check the response status code
    if e3_run_response.status_code == 200:
        # print the response body, which contains the run ID
        print(e3_run_response.json())
    else:
        # print an error message if the request was not successful
        print('Error creating new run: ' + e3_run_response.text)

    create_e3_run_file = api.post("files/create-empty/",{
        "name": run_name,
        "link": f"https://app.epsilon3.io/app/team/{EPSILON3_TEAM_KEY}/runs/{e3_run['run_id']}",
        "file_type":2,
        "project": project_id})

    return create_e3_run_file

def categorize_e3files(api, file_list):
    files_response = api.request("POST", "files/search/", {"query_filters": {"id__in": file_list}})
    files = files_response["data"]

    e3_files= {
        "procedures": [],
        "runs": []
    }

    # Iterate through the provided list of dictionaries
    for file_dict in files:
        name = file_dict.get('name', '')
        file_id = file_dict.get('id')

        # Check the prefix in the name and add the id to the respective category
        if name.startswith('[P]'):
            e3_files["procedures"].append(file_id)
        elif name.startswith('[R]'):
            e3_files["runs"].append(file_id)

    return e3_files

def create_run_and_replace(api, procedures, run_url, vm_id):
    """
    Iterates through the list of procedures and creates runs in E3, 
    places them in Valispace symbolic files and replaces these files
    as close-out references in the "Epsilon3 Test" VMs.
    """
    def replace_prefix(s):
        if s.startswith('[P]'):
            return '[R]' + s[3:]
        return s

    def extract_procedure_id(file_info):
        download_url = file_info.get('download_url', '')
        # Split the URL on 'procedures/' and get the last part
        parts = download_url.split('procedures/')
        if len(parts) > 1:
            # Further split to avoid any additional parameters or paths
            procedure_id = parts[-1].split('/')[0]
            return procedure_id
        return None
    
    switch = []

    for procedure in procedures:
        file_info = api.get(f"files/{procedure}")

        file_name = replace_prefix(file_info["name"])

        # Get the current timestamp
        timestamp = datetime.now()

        # Format the timestamp as a string
        # You can customize the format as you like, here it is year-month-day hour:minute:second
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Append the formatted timestamp to your original string
        new_file_name = file_name + "_" + timestamp_str

        e3_procedure_id = extract_procedure_id(file_info)

        e3_run = create_e3_run(api, run_url,e3_procedure_id,new_file_name) 

        procedure_cvm = api.request("POST",'requirements/component-vms/search/',{"query_filters": {"object_id": procedure},"includes":["id","verification_method"]})
        
        # for cvm in procedure_cvm["data"]:
        
        #     switch.append(api.request("PATCH",f'requirements/component-vms/{cvm["id"]}',{"object_id": e3_run['id']}))
        for cvm in procedure_cvm["data"]:
            if cvm["verification_method"]==vm_id:
                try:
                    response = api.request("PATCH", f'requirements/component-vms/{cvm["id"]}/', {"object_id": e3_run['id']})
                    switch.append(response)
                except Exception as e:
                    print(f"An error occurred when updating CVM with id {cvm['id']}: {e}")

    return switch        


def check_run_status(api, runs):
    print("hello!")

    def categorize_runs(file_info, e3_runs):
        """
            Nested function for categorizing runs by State.
        """
        run_ids = {}
        
        for file in file_info:
            run_ids[file['id']] = file['link'].split('/runs/')[-1]

        # Initialize dictionaries for each run state
        runs_categorized = {
            'running': {},
            'paused': {},
            'completed': {}
        }

        # Loop through each run in the e3_runs list
        for run_id in run_ids:
            for run in e3_runs:
                if run['_id'] == run_ids[run_id]:
                    # Use run_id as the key instead of the run's '_id'
                    run_key = run_id

                    # Categorize the run based on its state
                    if run['state'] == 'running':
                        runs_categorized['running'][run_key] = run
                    elif run['state'] == 'paused':
                        runs_categorized['paused'][run_key] = run
                    elif run['state'] == 'completed':
                        runs_categorized['completed'][run_key] = run

        return runs_categorized

    file_info = []

    for run in runs:
        file_info.append(api.get(f"files/{run}"))

    e3_runs_json = requests.get(
        url='https://api.epsilon3.io/v1/runs/summary',
        auth=(EPSILON3_API_KEY, ''),
        params={
          "run-state": ["running", "paused", "completed"],
        }
    )

    e3_runs_data = e3_runs_json.json()

    e3_runs = e3_runs_data['data']

    categorized_runs = categorize_runs(file_info, e3_runs) # Puts runs inside a categorized Dict of Dicts for Running, Paused, Completed.

    return categorized_runs

def update_run_status(api, current_run_status, current_cvms):
    """
    Batch updates the CVMs Verification status based on the Epsilon3 Run status.

    Args:
        api: Valispace API
        current_run_status: Dictionary with key each status for runs, value is Dictionaries with key the Run File id ('object_id') in Valispace and the value a dictionary with Epsilon3 json info of the corresponding run.   
        current_cvms: List of dicts with relevant CVMs to be updated.

    Returns:
        0
    """

    # Payload mapping
    # A decision was taken here to map to currently defined VM statuses to the default Espilon3 State and Status run result. The payloads are named with {valispaceStatus}_{epsilon3StateStatus_1, epsilon3StateStatus_2,...}.
    # Other mappings can be customized later depending on a deployment's configuration.

    def get_runningAndPaused_cvms(runningAndPaused_files, current_cvms):
        # Create a dictionary from current_cvms for quick lookup
        cvm_dict = {cvm['object_id']: cvm['id'] for cvm in current_cvms if 'object_id' in cvm and 'id' in cvm}

        # Initialize the list to store the matching ids
        result_ids = []

        # Iterate over each object_id in the runningAndPaused_files
        for object_id in runningAndPaused_files:
            # Check if the object_id exists in the cvm_dict and append the corresponding id to the result list
            if object_id in cvm_dict:
                result_ids.append(cvm_dict[object_id])

        return result_ids

    def categorize_completed(completed_runs, current_cvms):
        # Convert current_cvms list to a dictionary for quick lookup
        cvm_dict = {cvm['object_id']: cvm['id'] for cvm in current_cvms if 'object_id' in cvm and 'id' in cvm}

        # Initialize the dictionary to categorize runs by status
        categorized_completed = {
            'success': [],
            'abort': [],
            'failure': []
        }

        # Iterate through the provided completed runs
        for key, run in completed_runs.items():
            # Extract the status of the run
            status = run['status']

            # Check if the status is one of the expected categories and if the key matches any object_id in cvm_dict
            if status in categorized_completed and key in cvm_dict:
                # Add the corresponding cvm id to the appropriate status category
                categorized_completed[status].append(cvm_dict[key])

        return categorized_completed

    runningAndPaused_files = list(current_run_status['running'].keys()) + list(current_run_status['paused'].keys())

    runningAndPaused_cvms = get_runningAndPaused_cvms(runningAndPaused_files, current_cvms)

    categorized_completed_cvms = categorize_completed(current_run_status['completed'], current_cvms)


    payload_inProgress_runningAndPaused = {
        "ids": runningAndPaused_cvms,
         "data":{"status":4}
    }

    payload_verified_success = {
        "ids": categorized_completed_cvms['success'],
        "data":{"status":2}
    }

    payload_notVerified_abortFailed = {
        "ids": categorized_completed_cvms['abort']+categorized_completed_cvms['failure'],
        "data":{"status":1}
    }

    payloads = [payload_verified_success, payload_inProgress_runningAndPaused, payload_notVerified_abortFailed]

    for payload in payloads:
        update_cvms = api.request("PATCH","requirements/component-vms/bulk-update/?save_history=true", payload)
        print(update_cvms)


    return 0

def main(**kwargs):
    """
    Main function to execute the script.

    Args:
        **kwargs: Additional arguments passed to the script.

    Returns:
        Dict[str, Any]: Result data to be sent back to Valispace.
    """

    # Authenticate with the API using the provided temporary access token from kwargs
    api = initialize_api(kwargs['temporary_access_token'])

    vm_id = fetch_vm_id(api, project_id)

    print(f"vm_id: {vm_id}")

    # Fetch all close-out reference files belonging to an "Epsilon3 Test" Verification Method
    e3_closeout_files_all = api.request("POST",'requirements/component-vms/search/',{
    "query_filters": {"content_type": 171, "method__method_id": vm_id, "method__requirement__specification__project_id": project_id},
    "includes": ["object_id"],
    })

    e3_closeout_files = e3_closeout_files_all['data']

    print(e3_closeout_files)

    files_list = []

    for file in e3_closeout_files:
        files_list.append(file['object_id'])

    e3_files = categorize_e3files(api, files_list)

    # set the API endpoint URL
    run_url = e3_endpoint["runs"]

    created_runs = create_run_and_replace(api, e3_files["procedures"], run_url, vm_id)

    if created_runs:
        for created_run in created_runs:
            e3_files['runs'].append(created_run['object_id'])

    current_run_status = check_run_status(api,e3_files['runs'])

    current_cvms_request = api.request("POST",'requirements/component-vms/search/',{
        "query_filters": {"object_id__in": e3_files['runs']},
        "includes": [],
        }
        )
    
    current_cvms = current_cvms_request["data"]
    
    updated_run_status = update_run_status(api, current_run_status, current_cvms)


    # TODO: Return all the data you want to send back to Valispace
    return {
        "result": "Hello World!",
    }

if __name__=='__main__':
    main()

print('END')
