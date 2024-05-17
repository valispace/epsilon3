# epsilon3
Script files for Valispace&lt;->Epsilon3 integration through their respective APIs.

---

# Valispace/Epsilon3 Integration

This repository holds the integration scripts for connecting Valispace and Epsilon3 by leveraging each tool's APIs. These scripts are designed to be run from the Valispace Scripting module but can also be adapted for use from a user's desktop environment.

## Table of Contents
1. [Overview](#overview)
2. [Integration Files](#integration-files)
3. [Usage](#usage)
4. [Integration Setup](#integration-setup)
5. [Customization](#customization)
6. [Limitations](#limitations)
7. [Support](#support)

## Overview
This integration facilitates the synchronization of Master Procedures from Epsilon3 to Valispace and automates the verification process within Valispace using these procedures.

## Integration Files
The integration consists of two main Python scripts:
1. `fetch_master_procedures.py`
2. `create_check_run.py`

## Usage

### `fetch_master_procedures.py`
This script logs into Epsilon3 and fetches the Master Procedures. It then recreates these procedures as symbolic files in Valispace with the format `[P] {Procedure Code} - {Procedure Title}`.

#### Steps:
1. Run `fetch_master_procedures.py` to login to Epsilon3 and fetch Master Procedures.
2. Procedures will be recreated in Valispace as symbolic files with the format `[P] {Procedure Code} - {Procedure Title}`.
3. Add these procedure files as a close-out reference for a Verification Method "Epsilon3 Test" applied to a Valispace requirement.

### `create_check_run.py`
This script checks each "Epsilon3 Test" verification method for a procedure file. If found, it creates a run for that procedure in Epsilon3, creates a run file with the format `[R] {Procedure Code} - {Procedure Title}_{Date and Time Stamp}`, and replaces the procedure file with the corresponding run file as a close-out reference.

#### Steps:
1. Trigger `create_check_run.py`.
2. The script will check for each "Epsilon3 Test" verification method and create a corresponding run in Epsilon3.
3. If the close-out reference is already a run file, the script checks for the current state and status in Epsilon3 and updates the verification status in Valispace.

## Integration Setup
These scripts are intended to run on specific projects and should be set up once per Valispace project.

### Prerequisites:
1. Create a custom Verification Method "Epsilon3 Test" in Valispace with "Upload" as the close-out reference.
2. Create user secrets in Valispace:
   - `EPSILON3_API_KEY`: Key generated in Epsilon3.
   - `EPSILON3_TEAM_KEY`: Key in the Epsilon3 deployment's URL following the "team/" part of the URL.

### Steps:
1. Clone this repository.
2. Create the user secrets as described above.
3. Edit the scripts to point to the correct Valispace and Epsilon3 deployment base URLs.

## Customization
Users are encouraged to create their own branches of this repository and customize the scripts to better suit their Valispace and Epsilon3 workflows.

## Limitations
- These scripts currently only work with the original Valispace Requirements Verification Methods.
- They are not yet compatible with the new Verification & Validations Module workflow.

## Support
For further assistance, please refer to the [Epsilon3 helpdesk](https://support.epsilon3.io/en/articles/9300456-valispace-integration) or contact Valispace Support at [support@valispace.com](mailto:support@valispace.com).
