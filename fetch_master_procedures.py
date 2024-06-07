import requests
from valispace import API
from typing import Dict, Any
from .settings import EPSILON3_API_KEY, EPSILON3_TEAM_KEY


# set the API endpoint URL
run_url = 'https://api.epsilon3.io/v1/runs'
commands_url = 'https://api.epsilon3.io/v1/commands'
procedures_url = 'https://api.epsilon3.io/v1/procedures/summary'


# ---------------------------------------------
# Configuration Section
# Change the following values based on your specific use case

VALISPACE = {
    "domain": "http://valispace",  # Base URL for the Valispace instance, if the deployment is an onprem deployment this should be set to "hhtp://valispace"
    "warn_https": False,  # Disable HTTPS warnings if set to False
}

# Define project id
project_id = 24


# set the request headers with the API key for authentication
headers = {
    'Authorization': 'Basic ' + EPSILON3_API_KEY
}

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

def extract_procedures(test_response):
    """
    Extracts 'code' and '_id' from each test in the response data and builds a dictionary.

    :param test_response: The response object from a web request.
    :return: A dictionary with the 'code' as keys and '_id' as values.
    """
    # Parse the JSON content of the response to a dictionary
    data_dict = test_response.json()
    
    # Extract the list associated with the 'data' key
    data_list = data_dict['data']
    
    # Initialize an empty dictionary to hold our extracted values
    code_id_dict = {}
    
    # Iterate over each item in the data list
    for item in data_list:
        code = item.get('code')  # Use .get() to avoid KeyError if 'code' is missing
        name = item.get('name')  # Use .get() to avoid KeyError if 'name' is missing
        _id = item.get('_id')    # Use .get() to avoid KeyError if '_id' is missing
        
        # Only add to dictionary if 'code', 'name' and '_id' are present
        if code and name and _id:
            code_id_dict[f"[P] {code} - {name}"] = f"https://app.epsilon3.io/app/team/{EPSILON3_TEAM_KEY}/procedures/"+_id
    
    return code_id_dict

def fetch_files_and_compare(valispace_api, project_id, test_dict):
    """
    Fetches a list of files from a Valispace deployment project and checks if the file names match the keys in 'test_dict'.

    :param valispace_api: A configured Valispace API object.
    :param project_id: The ID of the Valispace deployment project.
    :param test_dict: A dictionary with 'code - name' as keys and '_id' as values.
    :return: A dictionary with file names as keys and a boolean as values indicating if there is a match in 'test_dict'.
    """
    # Fetch the list of files from Valispace
    files_list = valispace_api.get("files/?project="+str(project_id))
    
    # Initialize an empty dictionary to hold our comparison results
    comparison_dict = {}

    # Iterate over each file in the list
    for file in files_list:
        # Assume file['name'] gives us the file name
        file_name = file['name']
        
        # Check if the file name is in the test_dict keys
        comparison_dict[file_name] = file_name in test_dict

    return comparison_dict

import requests

def create_missing_procedures_in_valispace(valispace_api, procedures_list, procedures_in_valispace, project_id):
    """
    Checks if procedures from Epsilon3 exist in Valispace, and if not, creates them.

    :param valispace_api: Authentication session for Valispace API.
    :param procedures_list: List of procedures from Epsilon3 with corresponding keys and values.
    :param procedures_in_valispace: Dictionary of procedures and their existence in Valispace.
    """

    # Iterate over procedures_list
    for procedure_name, procedure_info in procedures_list.items():
        # If the procedure does not exist in Valispace, create it
        if not procedures_in_valispace.get(procedure_name):
            payload = {
                "file_type": 2,
                "contenttype": 171,
                "name": procedure_name,
                "project": project_id,
                "link": procedure_info
            }
            
            # Make the POST request to create a new file in Valispace
            try:
                response = valispace_api.post(
                    "files/create-empty/",
                    payload
                )
                print(f"File for procedure '{procedure_name}' created successfully.")
            except:
                print(f"Failed to create file for procedure '{procedure_name}'.")



def main(**kwargs) -> Dict[str, Any]:
    # print("Main Function Starts")
    """
    Main function to execute the script.
    
    Args:
        **kwargs: Additional arguments passed to the script.

    Returns:
        Dict[str, Any]: Result data to be sent back to Valispace.
    """
    #initialize the api
    api = initialize_api(kwargs['temporary_access_token'])
    
    # send the POST request to fetch all procedures
    response = requests.get(procedures_url, auth=(EPSILON3_API_KEY,''))
    
    # create a dict with the available procedures on Epsilon3
    procedures_list = extract_procedures(response)
    
    # check files in Valispace and checks whether they already contain Epsilon3 procedures
    procedures_in_Valispace = fetch_files_and_compare(api,project_id,procedures_list)
    
    # creates missing procedures in Valispace as symbolic files which link directly to Epsilon3 procedures
    created_procedures = create_missing_procedures_in_valispace(api,procedures_list,procedures_in_Valispace, project_id)

if __name__=='__main__':
    main()

print('END')
