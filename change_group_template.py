#!/usr/bin/env python

import argparse
import os
import time

from pprint import pprint

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import random, string

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def get_snapshot(compute, project, snapshot_name):

    return compute.snapshots().get(project=project, snapshot=snapshot_name).execute()

def get_disk(compute, project, zone, disk):

    return compute.disks().get(project=project, zone=zone, disk=disk).execute()

def create_image(compute, project, diskObj):

    config = {
        'name': diskObj['name'],
        'sourceDisk': diskObj['selfLink']
    }
    
    return compute.images().insert(
        project=project,
        body=config).execute()


def create_disk(compute, project, zone, disk, snapshotObj):

    config = {
        'name': snapshotObj['name'],
        'sourceSnapshotId': snapshotObj['name'],
        'sizeGb': snapshotObj['diskSizeGb']
        
    }

    return compute.disks().insert(
        project=project,
        zone=zone,
        body=config).execute()

# [START create snapshot]
def create_snapshot(compute, project, zone, disk, snapshot_name):
    
    config = {
        'name': snapshot_name
    }

    return compute.disks().createSnapshot(
        project=project,
        zone=zone,
        disk=disk,
        body=config).execute()
# [END create snapshot]

# [START wait_for_operation]
def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
            
        if zone == 'global':
            result = compute.globalOperations().get(
            project=project,
            operation=operation).execute()
        else:
            result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
# [END wait_for_operation]

# [START run]
def main (project, zone, disk, wait=True):
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    print('Creating snapshot from disk ' + disk)
    snapshot_name = disk + '-' + randomword(8)  + '-tmp'
    operation = create_snapshot(compute, project, zone, disk, snapshot_name)
    wait_for_operation(compute, project, zone, operation['name'])

    #snapshot_name = 'test-li4l-wudzsrjv-tmp'
    snapshotObj = get_snapshot(compute, project, snapshot_name)
    print('Creating disk from snapshot ' + snapshot_name)
    operation = create_disk(compute, project, zone, disk, snapshotObj)
    wait_for_operation(compute, project, zone, operation['name'])

    diskObj = get_disk(compute, project, zone, snapshotObj['name'])
#    pprint(diskObj)
    print('Creating image from disk ' + diskObj['name'])
    operation = create_image(compute, project, diskObj)
#    pprint(operation)
    wait_for_operation(compute, project, 'global', operation['name'])
    #pprint(compute.zoneOperations().list(project=project, zone=zone).execute())

    print('DONE')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description =__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument('disk', help='Disk to generate the image template.')
    parser.add_argument('instance_group', help='Instance Group to substitute the image.')
    parser.add_argument(
        '--zone',
        default='europe-west1-d',
        help='Compute Engine zone to deploy to.')

    args = parser.parse_args()

    main(args.project_id, args.zone, args.disk)
# [END run]
