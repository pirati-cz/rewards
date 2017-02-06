#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''rewards.py

Generate reports of work performance and rewards for one person or a team
'''

import time

start = time.time()

import settings
import pandas as pd
import os.path
import wget
import json
from redmine import Redmine

redmine = Redmine(settings.REDMINE_URL, key=settings.REDMINE_KEY, version=settings.REDMINE_VERSION)

''' FUNCTIONS '''

def find_activity_number(activity):
    return int(activities_register[ activities_register['name'] == activity ]['id'])

def build_activities_register():
    '''Retrieve the list of activities types indexed by id'''
    target_file='time_entry_activities.json'
    if not os.path.isfile(target_file):
        link=settings.REDMINE_URL+'/enumerations/time_entry_activities.json'
        wget(link)

    easylist = json.loads(open(target_file).read())
    activities = easylist['time_entry_activities']

    easylist = { activity['id'] : activity
                 for activity in activities }
    df = pd.DataFrame
    df = df.from_dict(easylist, orient='index')
    return df

''' MAIN PROGRAM '''

activities_register = build_activities_register()

target_file = 'vykaz.tsv'
df = pd.read_csv(target_file, header=0, sep='\t').fillna('')

for index, row in df.iterrows():
    my_time_entry ={'issue_id': row['Č.'],
                    'spent_on' : row['Datum'],
                    'hours': float(row['Doba'].replace(',', '.')),
                    'activity_id': find_activity_number( row['Aktivita'] ),
                    'custom_fields' : [{'id': 16, 'value': row['Refundace'] }],
                    'comments' : row['Komentář'] }
    print("\nUkládá se následující záznam:")
    print(my_time_entry)
    print("\nZapsáno jako záznam (time_entry) číslo:")
    resource = redmine.time_entry.create(**my_time_entry)
    print(resource)
    print("\n\n")

end = time.time()
print('Time elapsed: {0:.3f} seconds. '.format(end - start))
