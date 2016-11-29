#!/usr/bin/env python

# import section
import argparse, os, time
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from pprint import pprint

# functions

def get_instanceGroup(service, project,zone, instanceGroup):
    """
    Returns instance group object.
    """
    try: 
        result = service.instanceGroups().get(project=project, zone=zone, instanceGroup=instanceGroup).execute()
    except Exception as error:
        print("Error getting instance group: %s." % str(error.message))
        exit(1)
    return result

def get_instanceGroupManager(service, project,zone, instanceGroup):
    """
    Return instance group manager object.
    """
    try:
        result = service.instanceGroupManagers().get(project=project, zone=zone, instanceGroupManager=instanceGroup).execute()
    except Exception as error:
        print("Error getting instance group manager: %s." % str(error.message))
        exit(1)
    return result


def resize_instanceGroup(service, project, zone, instanceGroup, instances_num):
    """
    Resize instanceGroup manager to instances_num. Usually returns immediatly.
    """
    operation = service.instanceGroupManagers().resize(project=project, zone=zone, instanceGroupManager=instanceGroup, size=instances_num).execute()
    try:
        result = wait_for_operation(service, project, zone, operation)
    except Exception as error:
        print("Error executing resize: %s." % str(error.message))
        exit(1)
    return result

def wait_instanceGroupManager(service, project, zone, instanceGroup, timeout=None):
    """
    Checks and waits for any operation on an instance group until complete. Consider use of timeout.
    """
    n = 0
    all_actions = 1
    while all_actions > 0:
        result = get_instanceGroupManager(service, project, zone, instanceGroup)
        all_actions = sum(result['currentActions'].values()) - result['currentActions']['none']
        if timeout != None and n > timeout:
            print("Timeout while checking for finish actions on instance group manager")
            exit(1)
        n+=1
        time.sleep(1)

def wait_for_operation(service, project, zone, operation):
    """
    Keep waiting for an operation object to finish on gcp to complete.
    """
    print('Waiting for operation to finish...')
    while True:
        result = service.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation['name']).execute()
        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result.error)
            return result
        print("progress: %i" % (operation.progress))
        time.sleep(1)


# main

def main(project_id, zone, credentials_file, instance_group, instances_num):
    # start credentials, service
    scopes = ['https://www.googleapis.com/auth/compute']
    if credentials_file is not None:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scopes)
    else:
        credentials = GoogleCredentials.get_application_default()
    service = discovery.build('compute', 'v1', credentials=credentials)
    # do resize
    instancegroup = get_instanceGroup(service, project_id, zone, instance_group)
    print("Got instance group")
    instancegroup_resize = resize_instanceGroup(service, project_id, zone, instance_group, instances_num)
    wait_instanceGroupManager(service, project_id, zone, instance_group, 100)
    print("Instance group resize successfuly. %s intances on %s group." % (instances_num, instance_group))

if __name__ == '__main__':
    """ Script for resizing an Instance Group on GCP.
        Example: gce_resize.py --project_id=<project> --instance_group=<instance_group_name> --instance_num=<int> [--zone=<gce_zone>] [--credentials_file=json_gcp_application_credentials>]

        Arguments:
           --project_id
           --instance_group
           --instance_num
           [--zone]
           [--credentials_file]
        
    """
    parser = argparse.ArgumentParser( description =__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-p', '--project_id', help='Your Google Cloud project ID.', required=True)
    parser.add_argument('-i', '--instance_group', help='Instance Group to resize.', required=True)
    parser.add_argument('-n', '--instances_num', help='Number of instances to grow or shrink instance group to.', required=True)
    parser.add_argument('-z', '--zone', default='europe-west1-d', help='Compute Engine zone to deploy to.', required=False)
    parser.add_argument('-c', '--credentials_file', default=None, help='Optional service credentials from json file.', required=False)
    args = parser.parse_args()
    main(project_id=args.project_id, zone=args.zone, credentials_file=args.credentials_file, instance_group=args.instance_group, instances_num=args.instances_num)

