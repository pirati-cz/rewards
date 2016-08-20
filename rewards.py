#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''rewards.py

Generate reports of work performance and rewards for one person or a team
'''

import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import czech_holidays
from urllib import request
import settings
import os.path
from redmine import Redmine
from tabulate import tabulate
import wget
import json


def read_payroll(myfile='files/payroll.csv'):
    '''Read the data about the users from the payroll file'''

    df = pd.read_csv(myfile, header=0, index_col='Redmine')
    return df

def last_day(month):
    '''Return the last day in the given month'''

    year, month = month.split('-',2)
    startDate = date(int(year),int(month),1)
    endDate = (startDate + relativedelta(months=+1) ) - timedelta(days=1)
    return endDate

def business_days(startDate, endDate):
    '''Number of business days starting with the first day and
    ending with the last day'''

    if not isinstance(startDate, date) or \
       not isinstance(endDate, date): TypeError

    holidays = [ ]
    # get the complete list of holidays in range
    for myyear in range(startDate.year, endDate.year + 1):
        holidays.extend(
               [ date(holiday.year, holiday.month, holiday.day)
                 for holiday in czech_holidays.Holidays(int(myyear)) ])

    business_days=[ ]
    thisDate=startDate
    while thisDate<=endDate:
       if thisDate.weekday() not in [5,6]: # not saturday of sunday
           business_days.append(thisDate)
       thisDate += timedelta(days=1)

    business_days = set(business_days) - set(holidays)
    # print( [str(day) for day in business_days if day not in holidays ] )
    return len(business_days)

def create_link(startDate,endDate,user_ids,query='time_entries.csv'):
    '''Creates link for downloading the csv data chunk or for printing the link
    '''

    link  = settings.REDMINE_URL+'/'+query

    cs  = ['project','user','activity','issue','hours', 'cf_16', 'spent_on']
    link += '?c[]='+'&c[]='.join(cs)

    fs  = ['spent_on', 'user_id', '']
    link += '&f[]='+'&f[]='.join(fs)

    ops = [ ('spent_on', '><'), ('user_id', '=') ]
    semiproduct = [ 'op['+pair[0]+']='+pair[1] for pair in ops ]
    link += '&'+'&'.join(semiproduct)

    link += '&utf8=%E2%9C%93'

    link += '&v[spent_on][]='+startDate+'&v[spent_on][]='+endDate
    link += '&v[user_id][]=' + '&v[user_id][]='.join(user_ids)

    return link

def get_data_chunk(startDate,endDate,user_ids):
    if not os.path.isfile('.cache/data.csv'):
        link = create_link(startDate,endDate,user_ids)
        filename = wget.download(link)
        print("\n")

        fp = open('timelog.csv')
        s = fp.read()
        if s.startswith(u'\ufeff'): # zkurvenej bom
            s = s[1:]
        f = open('.cache/data.csv','w+')
        f.write(s)
        f.close()
        os.remove('timelog.csv')

    df = pd.read_csv('.cache/data.csv', header=0, encoding='utf-8', engine='c')
    return df

def build_projects_register():
    '''Retrieve the list of project names, shortlinks indexed by id'''

    if not os.path.isfile('.cache/projects.json'):
        mylist = list(redmine.project.all().values('id','name'))
        easylist = { project['id'] : project['name'] for project in mylist }
        with open('.cache/projects.json', 'w+') as f:
            json.dump(easylist, f)
    else:
        easylist = json.loads(open('.cache/projects.json').read())
    return easylist

def find_project_number(project):
    '''Return the number of the project with given name'''
    for key, value in projects_register.items():
        if value == project:
            return key
    raise IndexError

def issue_label_split(label):
    '''Split issue label to meaningful parts'''

    # Input: Úkol #3296: Zasedání zastupitelstva 16. 6. 2016
    # Output: [3296,Zasedání zastupitelstva 16. 6. 2016]

    first, name = label.split(': ')
    tracker, number = first.split(' #')
    number = str(int(number))
    return (number,name)

def issue_label(row):
    '''Return the line for printing the issue'''

    # Input: Úkol #3296: Zasedání zastupitelstva 16. 6. 2016
    # Output: [#3296 Zasedání zastupitelstva 16. 6. 2016][t3296]

    number, name = issue_label_split(row['Úkol'])
    line = '  [#'+number+' '+name+'][t'+number+']'
    return line

def print_tasks(user_projects, user_issues):

    user_projects['Hodiny']=user_projects['Hodiny'].round(1)
    user_issues['Hodiny']=user_issues['Hodiny'].round(1)

    projects = user_projects['Projekt']
    # get the project numbers print(projects)

    new_table = pd.DataFrame(columns=['Úkol', 'Hodiny'])
    links = '\n\n'

    for project in projects:
        number = find_project_number(project)
        new_table = new_table.append({
            'Úkol': '**['+project+'][p'+str(number)+']**',
            'Hodiny': user_projects[ user_projects.Projekt == project]['Hodiny']
            }, ignore_index=True)

        links += '[p'+number+']: '+create_link(startDate,endDate,this_user_id)+'&f[]=project_id&op[project_id]==&v[project_id][]='+number+'\n\n'

        these_issues = user_issues[user_issues.Projekt == project].copy().drop('Projekt', 1)

        for this_issue in these_issues['Úkol']:
            number, name = issue_label_split(this_issue)
            links += '[t'+number+']: '+create_link(startDate,endDate,this_user_id,'issues/'+number+'/time_entries')+'\n\n'

        if len(these_issues):
            these_issues['Úkol'] = these_issues.apply(issue_label, axis=1)
            new_table = pd.concat([new_table, these_issues])



    # grafical prep

    output = tabulate(new_table.as_matrix(), headers=['Projekt/úkol', 'Počet hodin'], tablefmt="pipe", floatfmt=".1f")
    output += links

    print(output)


#########################################################################

# first we have to find out who are the members of the team and what is the
# time scale

# then we shall download all necessary information for the reports
# for all team members included in one big chunk

redmine = Redmine(settings.REDMINE_URL, key=settings.REDMINE_KEY, version=settings.REDMINE_VERSION)


startDate='2016-06-01'
endDate='2016-06-30'
user_ids=['3','4','16','17']
user_name = 'Jakub Michálek'
this_user_id=['4']

os.makedirs('.cache', exist_ok=True)
projects_register = build_projects_register()
# print(df)

# we shall create report for one user from now on

df = get_data_chunk(startDate,endDate,user_ids)
user_report = df[ df.Uživatel == user_name ].copy()
# print(user_report)

user_projects = user_report.groupby('Projekt', as_index=False).sum().sort_values(by='Hodiny',ascending=0)
user_issues = user_report.groupby(['Úkol','Projekt'], as_index=False).sum()
user_issues = user_issues[ user_issues.Hodiny > 3.0 ].sort_values(by=['Hodiny'],ascending=[0])

print_tasks(user_projects, user_issues)



'''
print(user_projects)
print(user_issues)
print(projects_register)
'''
