#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''rewards.py

Generate reports of work performance and rewards for one person or a team
'''

import time

start = time.time()

import pandas as pd
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import czech_holidays
from urllib import request
import settings
import os.path
from redmine import Redmine
from tabulate import tabulate
import wget
import json
from termcolor import colored
import math
from trans import trans

def read_payroll():
    '''Read the data about the users from the payroll file'''

    link=settings.GITHUB_PAYROLL
    target_file='.cache/payroll.csv'
    safe_download(link, target_file)


    df = pd.read_csv(target_file, header=0)
    # payroll has not index, since the only unique field should be the contract url fragment

    df['Začátek'] = pd.to_datetime(df['Začátek'])
    df['Konec'] = pd.to_datetime(df['Konec'])
    return df

def read_other_incomes():
    '''Read the data about the users from the payroll file'''

    link=settings.GITHUB_OTHERINCOMES
    target_file='.cache/otherincomes.csv'
    safe_download(link, target_file)

    df = pd.read_csv(target_file, header=0)
    df['Začátek'] = pd.to_datetime(df['Začátek'])
    df['Konec'] = pd.to_datetime(df['Konec'])
    return df

def last_day(month):
    '''Return the last day in the given month'''

    year, month = month.split('-', 2)
    startDate = date(int(year), int(month), 1)
    endDate = (startDate + relativedelta(months=+1)) - timedelta(days=1)
    return endDate


def business_days(startDate, endDate):
    '''Number of business days starting with the first day and
    ending with the last day'''

    if not isinstance(startDate, date) or not isinstance(endDate, date):
        TypeError

    holidays = [ ]
    # get the complete list of holidays in range
    for myyear in range(startDate.year, endDate.year + 1):
        holidays.extend( [date(holiday.year, holiday.month, holiday.day)
        for holiday in czech_holidays.Holidays(int(myyear))])

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


def safe_download(link, target_file):
    '''Download given link in a safe manner and save under the target_file'''

    if not os.path.isfile(target_file):
        print('Downloading file '+target_file)
        filename = wget.download(link)
        print("\n")
        fp = open(filename)
        s = fp.read()
        if s.startswith(u'\ufeff'): # zkurvenej bom
            s = s[1:]
        f = open(target_file,'w+')
        f.write(s)
        f.close()
        os.remove(filename)


def get_data_chunk(startDate,endDate,user_ids):

    link=create_link(startDate,endDate,user_ids)
    target_file='.cache/data.csv'
    safe_download(link, target_file)

    df = pd.read_csv(target_file, header=0, encoding='utf-8', engine='c')
    df = df[ df['Refundace'] != 'neproplácet' ]
    return df


def find_project_by_name(name):
    try:
        number = projects_register[ projects_register['name'] == name ].index.values[0]
        #projects_register[ projects_register.name == name ]['identifier'].iloc[0]
        return int(number)
    except:
        raise IndexError

def find_project_by_identifier(identifier):
    try:
        name = projects_register[ projects_register['identifier'] == identifier ]['name'].iloc[0]
        # number = projects_register[ projects_register['identifier'] == name ].index.values[0]
        #projects_register[ projects_register.name == name ]['identifier'].iloc[0]
        return name
    except:
        raise IndexError


def build_projects_register():
    '''Retrieve the list of project names, shortlinks indexed by id'''
    # after that we can use projects_register.loc['6','identifier']
    # or with lookup as in find_project_by_name


    if not os.path.isfile('.cache/filtered_projects.json'):
        link=settings.REDMINE_URL+'/projects.json?limit=100'
        target_file='.cache/projects.json'
        safe_download(link, target_file)

        easylist = json.loads(open(target_file).read())
        if easylist['total_count']>100:
            raise NotImplementedError('To many project in the database. Needs more coding.')
            # This is not yet finished...
        projects = easylist['projects']

        easylist = { project['id'] : { 'name': project['name'],
                                       'identifier': project['identifier'] }
                     for project in projects }
        with open('.cache/filtered_projects.json', 'w+') as f:
            json.dump(easylist, f)
        os.remove(target_file)
    else:
        easylist = json.loads(open('.cache/filtered_projects.json').read())
    df = pd.DataFrame
    df = df.from_dict(easylist, orient='index')
    return df


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


def pretty_tasks(this_user_id,user_projects, user_issues):

    total_hours = user_projects['Hodiny'].sum()
    user_projects['Hodiny']=user_projects['Hodiny'].round(1)
    user_issues['Hodiny']=user_issues['Hodiny'].round(1)

    projects = user_projects['Projekt']
    # get the project numbers print(projects)

    new_table = pd.DataFrame(columns=['Úkol', 'Hodiny'])
    links = '\n\n'

    for project in projects:
        number = str(find_project_by_name(project))
        new_table = new_table.append({
            'Úkol': '**['+project.capitalize()+'][p'+str(number)+']**',
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
    new_table = new_table.append({
        'Úkol': '**Celkem v uvedených projektech**',
        'Hodiny': total_hours
        }, ignore_index=True)


    output = tabulate(new_table.as_matrix(), headers=['Projekt/úkol', 'Počet hodin'], tablefmt="pipe", floatfmt=".1f")

    return (output, links)

def create_work_report(project, user_id):

    payee = payroll[ (payroll['Id'] == int(user_id)) & (payroll['Tým'] == project) ].iloc[0].copy()
    # one person can have only one valid contract so this should be unique
    # for check - refer to check_payroll function

    user_name   = payee['Jméno a příjmení']
    user_filter = payee['Filtr']
    user_role = payee['Funkce']

    user_report = data_chunk[ data_chunk['Uživatel'] == user_name ].copy()

    #print(user_name)
    #print(user_filter)
    #if math.isnan(user_filter): print("Není žádný filtr")


    # Apply the filter in payroll
    # Each contract can have more projects as filters (separated by colon :)
    # but one project can be used only once as a filter - that is tasks from
    # one project can be atributed to one contract at most
    # there can be at most one valid contract for one person that has no filter
    # (otherwise it would not be clear to which contract we would atribute it)
    justification=''
    if isinstance(user_filter, str):
        # restricted report, the filter is given as a string
        filters = user_filter.split(':')
        user_report = user_report.loc[ user_report['Projekt'].isin(filters) ].copy()

        if len(filters) == 1:
            justification += '\nSmlouva se vztahuje pouze na čas vykázaný v rámci projektu {0}. '.format(user_filter)
        else:
            justification += '\nSmlouva se vztahuje pouze na čas vykázaný v rámci projektů {0}. '.format(', '.join(filters))
        justification += 'Čas vykázaný v jiných projektech není v tomto výkazu zahrnut, ale může být ve výkazu daného týmu. \n'
    else:
        # the full report - should also take into account all refunds, except
        # the "neproplácet" - since they are relevant to money
        # the filter is given as nan - float

        # find all projects that have been solved separatelly
        # we need to remove these time_entries from the user_report

        vysl = payroll.loc[ (payroll['Id'] == int(user_id) ) & payroll['Filtr'].notnull(), ['Filtr']  ]

        # if we found filter, we will use them

        if len(vysl.index) != 0:

            filters = [ vysledek[0] for vysledek in vysl.as_matrix() ]
            filters = ':'.join(filters)
            filters = filters.split(':')
            print(filters)
            user_report = user_report.loc[~user_report['Projekt'].isin(filters) ].copy()

            justification = 'Smlouva se vztahuje na všechny projekty. Výjimkou '
            if len(filters) == 1:
                justification += 'je pouze oddělený projekt '
            else:
                justification += 'jsou pouze oddělené projekty '
            justification += ', '.join(filters) + '. Oddělené projekty ovšem mohou být odměňovány podle zvláštní smlouvy.'

        else: justification = 'Smlouva se vztahuje na všechny projekty. '

    # print(user_report)

    user_projects = user_report.groupby('Projekt', as_index=False).sum().sort_values(by='Hodiny',ascending=0)
    user_issues = user_report.groupby(['Úkol','Projekt'], as_index=False).sum()
    user_issues = user_issues[ user_issues.Hodiny > 3.0 ].sort_values(by=['Hodiny'],ascending=[0])

    table, links = pretty_tasks(user_id,user_projects, user_issues)

    # now we will calculate the required input data for money!  $$$
    # actual_party_salary(month, actual_party_hours, actual_total_hours,
    #   daily_norm, agreed_fixed_money, agreed_workload_money, agreed_task_money)

    refunded_hours = user_report.loc[ user_report['Refundace'].notnull(), 'Hodiny' ].sum()


    actual_party_hours = user_report.loc[ ~user_report['Refundace'].notnull(), 'Hodiny' ].sum()

    agreed_fixed_money = payee['Základ']
    agreed_variable_money = payee['Bonus']
    agreed_workload_money = payee['Bonus']/5
    actual_business_days = business_days(month+'-01',month+'-'+last_day(month))
    agreed_monthly_norm = daily_norm * actual_business_days
    percentage = actual_total_hours/agreed_monthly_norm * 100.0
    hourly_reward = agreed_fixed_money/agreed_monthly_norm
    moneycomment = 'Podle smlouvy činila pevná složka dohodnuté odměny {0} Kč. '.format(agreed_fixed_money) + \
    'Protože v měsíci {0} bylo {1} dnů, činila hodinová sazba částku {2}. '.format(month, actual_business_days, hourly_reward)

    if actual_party_hours >= agreed_monthly_norm:
        actual_fixed_money = agreed_fixed_money
        overtime_hours = actual_party_hours - agreed_monthly_norm
        overtime_money = hourly_reward*overtime_hours
        moneycomment += 'Došlo k překročení dohodnutého počtu hodin. ' + \
        'Vyplácí se tedy pevná složka odměny ve výši {0} Kč '.format(agreed_fixed_money)
        'a dále za {0} hodin přesčas náleží odměna {1} Kč. '.format(overtime_hours, overtime_money)
    else:
        actual_fixed_money = hourly_reward*actual_party_hours
        overtime_money = 0.0
        moneycomment += 'Nedošlo k překročení dohodnutého počtu hodin. ' + \
        'Za {0} hodin náleží pevná složka odměny ve výši {1} Kč. '.format(actual_party_hours, actual_fixed_money)

    if percentage>=100.0:
        actual_workload_money=agreed_workload_money
    else:
        actual_workload_money=percentage**2/10.0 * agreed_workload_money

    user_path = project_path
    os.makedirs(project_path, exist_ok=True)

    # VARIABLES ASSIGNATION FOR TEMPLATE
    TMPTEAM=payee['Tým']
    TMPFUNCTION=user_role
    TMPCONTRACT=settings.CONTRACTS_PREFIX+payee['Smlouva']+settings.CONTRACTS_SUFFIX
    TMPTIMERANGE=month
    TMPTASKS=table+'\n\n'+justification
    TMPPARTYHOURS=actual_party_hours
    TMPCITYHOURS=refunded_hours
    TMPTOTALHOURS=actual_party_hours+refunded_hours
    TMPNORM=agreed_monthly_norm
    TMPPERCENTAGE=percentage
    TMPMONEYRANGE=str(agreed_fixed_money)+'–'+str(agreed_fixed_money+agreed_variable_money)+' Kč'
    TMPCONSTMONEY=actual_fixed_money
    TMPTASKSMONEY=0
    TMPWORKLOADMONEY=actual_workload_money
    TMPVARMONEY=TMPTASKSMONEY+TMPWORKLOADMONEY
    TMPOVERTIMEMONEY=overtime_money
    TMPSANCTIONS=0
    TMPPARTYMONEY=TMPCONSTMONEY+TMPVARMONEY+TMPOVERTIMEMONEY-TMPSANCTIONS
    TMPMONEYCOMMENT=moneycomment
    TMPREFUNDS=refundation_overview(user_role, refunded_hours)



def check_payroll():
    '''The integrity checks for the payroll. Please refer to create_work_report documentation.'''
    raise NotImplementedError


def date_range(row):
    '''Return boolean value whether the given row is has time intersect with dates'''
    alfa=datetime.strptime(startDate, '%Y-%m-%d').date()
    omega=datetime.strptime(endDate, '%Y-%m-%d').date()

    alfa=max(row['Začátek'].date(), alfa)

    if not pd.isnull(row['Konec']):
        omega=min(row['Konec'].date(), omega)

    if omega<alfa:
        return False
    else:
        return True


def validate_contracts(payroll):
    '''Return payroll in the given period.'''

    mask = payroll.apply(date_range, axis=1)
    return payroll[ mask ]


def refundation_overview(role, hours):
    '''This will print part of the report of other incomes of the person
    in the given month, so that we can adjust the party salary.'''

    this_other_incomes = other_incomes[ other_incomes['Funkce'] == role ].copy()
    justification = '### Přehled refundací \n\n'

    if len(this_other_incomes) != 0:

        this_other_incomes['Měsíční částka'] = 0

        hourly = this_other_incomes [ this_other_incomes['Výpočet'] == 'hodinově' ]['Výše příjmu'].iloc[0]


        if hourly: this_other_incomes.loc [ this_other_incomes['Výpočet'] == 'hodinově' , 'Měsíční částka'] = hours*hourly

        monthly = this_other_incomes [ this_other_incomes['Výpočet'] == 'měsíčně' ]['Výše příjmu'].iloc[0]
        if monthly: this_other_incomes.loc [ this_other_incomes['Výpočet'] == 'měsíčně' , 'Měsíční částka'] = monthly

        justification += role.capitalize()+' má dále z titulu své funkce za tento měsíc nárok na následující příjmy:\n\n'

        this_other_incomes['Sazba'] = this_other_incomes['Výše příjmu'].map(str)+' Kč '+this_other_incomes['Výpočet'].map(str)
        this_other_incomes = this_other_incomes[['Typ příjmu', 'Sazba', 'Měsíční částka' ]]
        this_other_incomes=this_other_incomes.rename(columns = {'Měsíční částka':'Měsíční částka (Kč)'})

        justification += tabulate(this_other_incomes.as_matrix(), headers=['Typ příjmu', 'Sazba', 'Měsíční částka (Kč)'], tablefmt="pipe", floatfmt=".1f")
    else:
        justification += 'U této osoby nejsou evidovány žádné příjmy, na které by měla nárok v souvislosti s funkcí.'
    return justification

#########################################################################

#             CONFIGURATION - SHOULD BE FROM COMMAND LINE

month=''
teams='praha medialni-odbor'

#########################################################################
#                       PROGRAM INTERNALS
# first we have to find out who are the members of the team and what is the
# time scale

# then we shall download all necessary information for the reports
# for all team members included in one big chunk

redmine = Redmine(settings.REDMINE_URL, key=settings.REDMINE_KEY, version=settings.REDMINE_VERSION)


if not month: # if month is not a valid time, use last month

    today = date.today()
    first = today.replace(day=1)
    lastMonth = first - timedelta(days=1)
    month = str(lastMonth.strftime("%Y-%m"))

startDate=month+'-01'
endDate=str(last_day(month))

os.makedirs('.cache', exist_ok=True)

projects_register = build_projects_register()
year, monthalone = month.split('-')
payroll = read_payroll()
# filter only contracts, that are valid in some of the range given
payroll = validate_contracts(payroll)
other_incomes=read_other_incomes()
other_incomes = validate_contracts(other_incomes) # show only in the given time

#print(payroll)
used_projects = payroll['Tým'].unique()
if teams:
    teams = teams.split(' ')
    used_projects = map(find_project_by_identifier, teams)


user_ids = payroll['Id'].copy().astype(str).tolist()
data_chunk = get_data_chunk(startDate,endDate,user_ids)

for project in used_projects:
    identifier = projects_register.loc[str(find_project_by_name(project)),'identifier']
    project_path = identifier+'/'+year+'/'+monthalone+'/'
    os.makedirs(project_path, exist_ok=True)

    # one person can have only one role in a given project
    print('\n\n'+colored('printing project '+project, 'blue'))
    project_users = payroll[ payroll['Tým'] == project ].copy()
    user_ids = project_users['Id'].astype(str).tolist()

    print (user_ids)

    # we shall create report for one user from now on

    for user_id in user_ids:
        print('printing for user '+user_id)
        report = create_work_report(project, user_id)
        #break
    #break

end = time.time()
print('Time elapsed: {0:.3f} seconds. '.format(end - start))

'''
print(user_projects)
print(user_issues)
print(projects_register)
'''
