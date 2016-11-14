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

def get_image(compute, project, imageName):

    return compute.images().get(project=project, image=imageName).execute()

def get_instanceTemplate(compute, project, instanceTemplate):

    return compute.instanceTemplates().get(project=project, instanceTemplate=instanceTemplate).execute()

def get_instanceGroupManager(compute, project, zone, instanceGroup):

    return compute.instanceGroupManagers().get(project=project, zone=zone, instanceGroupManager=instanceGroup).execute()

def get_instanceGroup(compute, project, zone, instanceGroup):

    return compute.instanceGroups().get(project=project, zone=zone, instanceGroup=instanceGroup).execute()

def get_snapshot(compute, project, snapshot_name):

    return compute.snapshots().get(project=project, snapshot=snapshot_name).execute()

def get_disk(compute, project, zone, disk):

    return compute.disks().get(project=project, zone=zone, disk=disk).execute()

def change_instanceGroup_Template(compute, project, zone, instanceGroup, instanceTemplate):

    config = {
        'instanceTemplate': instanceTemplate
    }

    return compute.instanceGroupManagers().setInstanceTemplate(
        project=project, 
        zone=zone, 
        instanceGroupManager=instanceGroup, 
        body=config).execute()

def copy_instance_template(compute, project, instanceTemplateObj):

    config = instanceTemplateObj

    return compute.instanceTemplates().insert(
        project=project,
        body=config).execute()

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
def main (project, zone, disk, instanceGroup, wait=True):
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

#    print('Creating snapshot from disk ' + disk)
#    randomName = randomword(8)
#    snapshot_name = disk + '-' + randomName  + '-tmp'
#    operation = create_snapshot(compute, project, zone, disk, snapshot_name)
#    wait_for_operation(compute, project, zone, operation['name'])
#
    randomName = 'eaevwksh'
    snapshot_name = 'test-li4l-eaevwksh-tmp'
    snapshotObj = get_snapshot(compute, project, snapshot_name)
#    print('Creating disk from snapshot ' + snapshot_name)
#    operation = create_disk(compute, project, zone, disk, snapshotObj)
#    wait_for_operation(compute, project, zone, operation['name'])
#
    diskObj = get_disk(compute, project, zone, snapshotObj['name'])
##    pprint(diskObj)
#    print('Creating image from disk ' + diskObj['name'])
#    operation = create_image(compute, project, diskObj)
#    wait_for_operation(compute, project, 'global', operation['name'])
    imageObj = get_image(compute, project, diskObj['name'])

    instanceGroupManagerObj = get_instanceGroupManager(compute, project, zone, instanceGroup)

    instanceTemplateObj = get_instanceTemplate(compute, project, instanceGroupManagerObj['baseInstanceName'])
    instanceTemplateObj['properties']['disks'][0]['initializeParams']['sourceImage'] = imageObj['selfLink']
    instanceTemplateObj['name'] = instanceTemplateObj['name'] + '-' + randomName  + '-tmp'

    operation = copy_instance_template(compute, project, instanceTemplateObj)
    wait_for_operation(compute, project, 'global', operation['name'])

    instanceTemplateObj = get_instanceTemplate(compute, project, instanceTemplateObj['name'])

    print instanceTemplateObj['selfLink']
    operation = change_instanceGroup_Template(compute, project, zone, instanceGroup, instanceTemplateObj['selfLink'])
    wait_for_operation(compute, project, zone, operation['name'])
    pprint(operation)

#gcloud compute --project "advance-state-858" instance-groups managed recreate-instances  "test" --zone "europe-west1-d" --instance "test-li4l"
#InstanceGroupManagers: recreateInstances

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

    main(args.project_id, args.zone, args.disk, args.instance_group)
# [END run]
