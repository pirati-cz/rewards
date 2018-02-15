#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''rewards.py

Generate reports of work performance and rewards for one person or a team
'''

import time

start = time.time()

import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import czech_holidays
from urllib import request
import settings
import os.path
# from redmine import Redmine
from tabulate import tabulate
import wget
import json
from termcolor import colored
import math
from trans import trans
from gsheets import Sheets
import math
import requests
from github import Github

'''
         PARSING
'''

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action="store_true")

# subparsers = parser.add_subparsers(help='sub-command help')
# parser_report = subparsers.add_parser('teams', help='create or update report of work', aliases=['team'])

#parser.add_argument('-t', '--teams', nargs='*', help="project short name from redmine, such as 'praha'")
parser.add_argument('-m', '--month', help='month such as 2016-02')
parser.add_argument('-c', '--cache', action="store_true", help='use cache (do not download)')

#parser_remind = subparsers.add_parser('remind', help='remind the team members to fill in the rewards', aliases=['mail'])
#parser_remind.add_argument('-t', '--teams', nargs='*', help="project short name from redmine, such as 'praha'")
#parser_remind.add_argument('-m', '--month', help='month such as 2016-02')
#parser_remind.add_argument('number', help='the number for first and second reminder')

args = parser.parse_args()

usecache = True
# after debug set to args.cache

'''
         FUNCTIONS
'''

def num2datestr(number):
    ref_date = date(1900, 1, 1)   # referential date since the dates are returned starting 1899-12-30

    if isinstance(number, float) and not math.isnan(number):
        return (ref_date + timedelta(days=number - 2)).isoformat()
    else:
        return ""

def read_payroll():
    '''Read the data about the users from the payroll file'''


#    link=settings.GITHUB_PAYROLL
#    target_file='.cache/payroll.csv'
#    safe_download(link, target_file)

    tymy_df = pd.read_csv('.cache/Týmy.csv', header=0)

    #print(tymy_df)

    lide_df = pd.read_csv('.cache/Lidé.csv', header=0, dtype={'Id': np.int32} )

    #print(lide_df)

    target_file = '.cache/Smlouvy.csv'
    df = pd.read_csv(target_file, header=1, dtype={'Id': np.int32, 'týdně': np.float32, 'Paušál': np.float32,
                                                   'Kč/hod': np.float32, 'Úkolovka': np.float32, 'Odpočet': np.float32,
                                                   'Úkol': str, 'Platí od': np.float32, 'Platí do': np.float32,
                                                   'Začátek': str, 'Konec': str, 'Zatřídění':str})
    # payroll has not index, since the only unique field should be the contract url fragment

    #print(df)

    # referential date since the dates are returned starting 1899-12-30
    df['Začátek'] = df['Platí od'].apply(num2datestr)
    df['Konec'] = df['Platí do'].apply(num2datestr)

    #print (df)
    # now join the other tables
    df = pd.merge(df, lide_df, how='inner' )
    df = pd.merge(df, tymy_df, how='inner' ).sort_values('Příjmení')
    df['Jméno a příjmení'] = df['Jméno'] + ' ' + df['Příjmení']


    df.update(df[['týdně', 'Paušál', 'Kč/hod', 'Úkolovka', 'Odpočet']].fillna(0.0))
    df.update(df[[ 'Začátek', 'Konec', 'Úkol']].fillna(""))

    res = df[['Zkratka', 'Tým', 'Id', 'Jméno a příjmení','Typ' ,'Funkce', 'týdně', 'Paušál', 'Kč/hod',
              'Úkolovka', 'Max','Odpočet', 'Smlouva', 'Úkol', 'Začátek', 'Konec', 'Filtr', 'Zodpovídá',
              'Zatřídění']].copy()
    return res

def read_other_incomes():
    '''Read the data about the users from the payroll file'''

    link=settings.GITHUB_TRANSPARENCY_REPO_RAW+settings.GITHUB_OTHERINCOMES
    target_file='.cache/otherincomes.csv'
    safe_download(link, target_file)

    df = pd.read_csv(target_file, header=0)
    df['Začátek'] = pd.to_datetime(df['Začátek']).astype(str)
    df['Konec'] = pd.to_datetime(df['Konec']).astype(str)
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

    link += '&v[spent_on][]='+str(startDate)+'&v[spent_on][]='+str(endDate)
    link += '&v[user_id][]=' + '&v[user_id][]='.join(user_ids)

    return link


def safe_download(link, target_file):
    """Download given link in a safe manner and save under the target_file"""

    if not (os.path.isfile(target_file) and usecache):
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
    #print(user_ids)
    target_file='.cache/data.csv'
    #print(link)
    safe_download(link, target_file)

    df = pd.read_csv(target_file, header=0, encoding='utf-8', engine='c', dtype={'Refundace': np.object_ } )
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
    """Retrieve the list of project names, shortlinks indexed by id"""
    # after that we can use projects_register.loc['6','identifier']
    # or with lookup as in find_project_by_name


    if not os.path.isfile('.cache/filtered_projects.json'):
        link=settings.REDMINE_URL+'/projects.json?limit=100'
        target_file='.cache/projects.json'
        safe_download(link, target_file)

        easylist = json.loads(open(target_file).read())

        total_count = easylist['total_count']

        projects = easylist['projects']

        easylist = { project['id'] : { 'name': project['name'],
                                       'identifier': project['identifier'] }
                     for project in projects }

        if total_count > 100:
            for offset in range(100,total_count,100):
                safe_download(link+'&offset='+str(offset), target_file)
                easylist2 = json.loads(open(target_file).read())
                projects = easylist2['projects']
                easylist2 = {project['id']: {'name': project['name'],
                                            'identifier': project['identifier']}
                            for project in projects}
                easylist = {**easylist, **easylist2}

        with open('.cache/filtered_projects.json', 'w+') as f:
            json.dump(easylist, f)
        os.remove(target_file)

    easylist = json.loads(open('.cache/filtered_projects.json').read())
    df = pd.DataFrame
    df = df.from_dict(easylist, orient='index')


    tymy_df = pd.read_csv('.cache/Týmy.csv', header=0)
    tymy_df['name'] = tymy_df['Tým']

    df = pd.merge(df, tymy_df, how='left', on=['name'])
    return df

def issue_label_split(label):
    '''Split issue label to meaningful parts'''

    # Input: Úkol #3296: Zasedání zastupitelstva 16. 6. 2016
    # Output: [3296,Zasedání zastupitelstva 16. 6. 2016]

    first, name = label.split(': ',1)
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

        links += '[p'+number+']: '+create_link(startDate,endDate,this_user_id,'time_entries')+'&f[]=project_id&op[project_id]==&v[project_id][]='+number+'\n\n'

        these_issues = user_issues[user_issues.Projekt == project].copy().drop('Projekt', 1)

        for this_issue in these_issues['Úkol']:
            number, name = issue_label_split(this_issue)
            links += '[t'+number+']: '+create_link(startDate,endDate,this_user_id,'issues/'+number+'/time_entries')+'\n\n'

        if len(these_issues):
            these_issues['Úkol'] = these_issues.apply(issue_label, axis=1)
            new_table = pd.concat([new_table, these_issues])

    links += '\n\n[tasklist]: '+create_link(startDate,endDate,[this_user_id],query='time_entries')
    # TODO: filter by projects - filters may apply...

    # grafical prep
    new_table = new_table.append({
        'Úkol': '**Celkem v uvedených projektech**',
        'Hodiny': total_hours
        }, ignore_index=True)


    output = tabulate(new_table.as_matrix(), headers=['Projekt/úkol', 'Počet hodin'], tablefmt="pipe", floatfmt=".2f")

    return (output, links)

def create_work_report(project, user_id,project_path):

    payee = payroll[ (payroll['Id'] == int(float(user_id))) & (payroll['Tým'] == project) ].iloc[0].copy()
    # one person can have only one valid contract so this should be unique


    user_name   = payee['Jméno a příjmení']
    user_filter = payee['Filtr']
    user_role = payee['Funkce']

    user_rm = settings.REDMINE_URL+'/issues/'+str(payee['Úkol'])


    zkratka = str(projects_register.loc[find_project_by_name(project),'Zkratka'])


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

        vysl = payroll.loc[ (payroll['Id'] == int(float(user_id)) ) & payroll['Filtr'].notnull(), ['Filtr']  ]

        # if we found filter, we will use them

        if len(vysl.index) != 0:

            filters = [ vysledek[0] for vysledek in vysl.as_matrix() ]
            filters = ':'.join(filters)
            filters = filters.split(':')
            # print(filters)
            user_report = user_report.loc[~user_report['Projekt'].isin(filters) ].copy()

            justification = 'Smlouva se vztahuje na všechny projekty. Výjimkou '
            if len(filters) == 1:
                justification += 'je pouze oddělený projekt '
            else:
                justification += 'jsou pouze oddělené projekty '
            justification += ', '.join(filters) + '. Oddělené projekty ovšem mohou být odměňovány podle zvláštní smlouvy.'

        else:
            justification = 'Smlouva se vztahuje na všechny projekty. '




    user_projects = user_report.groupby('Projekt', as_index=False).sum().sort_values(by='Hodiny',ascending=0)
    user_issues = user_report.groupby(['Úkol','Projekt'], as_index=False).sum()
    user_issues = user_issues[ user_issues.Hodiny > 3.0 ].sort_values(by=['Hodiny'],ascending=[0])


    table, links = pretty_tasks(user_id,user_projects, user_issues)

    # now we will calculate the required input data for money!  $$$
    # actual_party_salary(month, actual_party_hours, actual_total_hours,
    #   daily_norm, agreed_fixed_money, agreed_task_money)

    skutecna_refundovana_prace = user_report.loc[ user_report['Refundace'].notnull(), 'Hodiny' ].sum()
    skutecna_prace = user_report.loc[ ~user_report['Refundace'].notnull(), 'Hodiny' ].sum()
    skutecne_hodiny_celkem = skutecna_prace+skutecna_refundovana_prace



    # SLOVNÍČEK

    smluvni_pausal = payee['Paušál']     # PAUŠÁL
    smluvni_hodinovka = payee['Kč/hod']  # HODINOVKA
    smluvni_ukolovka = payee['Úkolovka'] # ÚKOLOVKA
    smluvni_odpocet = payee['Odpočet']   # ODPOČET

    smluvni_hodiny = payee['týdně']

    skutecny_pausal=smluvni_pausal

    skutecna_hodinovka = skutecna_prace*smluvni_hodinovka

    try:
        bonus_line = bonuses[(bonuses['Jméno a příjmení'] == user_name) & (bonuses['Zkratka'] == zkratka)].iloc[0].copy()
        skutecna_ukolovka = bonus_line['Skutečná odměna']
        skutecny_odpocet = bonus_line['Odpočet']
    except:
        skutecna_ukolovka = 0.0
        skutecny_odpocet = 0.0

    smluvni_odhad_mesicne = smluvni_hodiny/5.0 * actual_business_days

    if smluvni_odhad_mesicne:
        skutecne_procento = skutecne_hodiny_celkem/smluvni_odhad_mesicne * 100.0
    else:
        skutecne_procento = 100.0

    if skutecna_prace >= smluvni_odhad_mesicne:
        skutecna_hodinovka_pod = smluvni_odhad_mesicne*smluvni_hodinovka
        skutecna_hodinovka_nad = (skutecna_prace-smluvni_odhad_mesicne) * smluvni_hodinovka
    else:
        skutecna_hodinovka_pod = skutecna_prace*smluvni_hodinovka
        skutecna_hodinovka_nad = 0.0

    links += '\n\n[smlouva]: '+str(payee['Smlouva'])
    refund_comment,refund_total_money = refundation_overview(user_role, skutecna_refundovana_prace)

    skutecna_mimoradna_odmena = 0.0


    if float(skutecna_ukolovka) > float(smluvni_ukolovka):
        skutecna_mimoradna_odmena = skutecna_ukolovka-smluvni_ukolovka
        skutecna_ukolovka = smluvni_ukolovka

    skutecna_odmena_celkem = float(skutecny_pausal)+float(skutecna_hodinovka)+float(skutecna_mimoradna_odmena)+float(skutecna_ukolovka)-float(skutecny_odpocet)

    pretty_date = datetime.strptime(payee['Začátek'], '%Y-%m-%d')
    trans_user=trans(user_name.replace(' ','-').lower())

    max_odmena = float(payee['Max'])
    if skutecna_odmena_celkem > max_odmena > 0.0:
        skutecny_odpocet = skutecny_odpocet + skutecna_odmena_celkem - max_odmena
        skutecna_odmena_celkem = max_odmena


    # VARIABLES ASSIGNATION FOR TEMPLATE
    placeholder = {}
    placeholder['TMPNAME']=user_name
    placeholder['TMPTRANSLIT'] = trans_user
    placeholder['TMPTEAM']=payee['Tým']
    placeholder['TMPZKRATKA']=zkratka
    placeholder['TMPFUNCTION']=user_role
    placeholder['TMPCONTRACT']='[smlouva ze dne {0}'.format(pretty_date.strftime("%-d. %-m. %Y"))+'][smlouva]'
    placeholder['TMPTIMERANGE']=month
    placeholder['TMPTASKS']=table+'\n\n'+justification

    placeholder['TMP_SMLUVNI_HODINY']=float(smluvni_hodiny)
    placeholder['TMP_SMLUVNI_ODHAD_MESICNE']=float(smluvni_odhad_mesicne)
    placeholder['TMP_SKUTECNA_PRACE']=float(skutecna_prace)
    placeholder['TMP_SKUTECNA_REFUNDOVANA_PRACE']=float(skutecna_refundovana_prace)
    placeholder['TMP_SKUTECNE_HODINY_CELKEM']=float(skutecne_hodiny_celkem)
    placeholder['TMP_SKUTECNE_PROCENTO']=float(skutecne_procento)

    placeholder['TMP_SMLUVNI_PAUSAL']=float(smluvni_pausal)
    placeholder['TMP_SMLUVNI_HODINOVKA']=float(smluvni_hodinovka)
    placeholder['TMP_SMLUVNI_UKOLOVKA']=float(smluvni_ukolovka)
    placeholder['TMP_SMLUVNI_ODPOCET']=float(smluvni_odpocet)

    placeholder['TMP_SKUTECNY_PAUSAL']=float(skutecny_pausal)
    placeholder['TMP_SKUTECNA_HODINOVKA_POD']=float(skutecna_hodinovka_pod)
    placeholder['TMP_SKUTECNA_HODINOVKA_NAD']=float(skutecna_hodinovka_nad)
    placeholder['TMP_SKUTECNA_UKOLOVKA']=float(skutecna_ukolovka)
    placeholder['TMP_SKUTECNA_MIMORADNA_ODMENA']=float(skutecna_mimoradna_odmena)
    placeholder['TMP_SKUTECNY_ODPOCET']=float(skutecny_odpocet)
    placeholder['TMP_SKUTECNA_ODMENA_CELKEM']=float(skutecna_odmena_celkem)
    placeholder['TMP_SKUTECNA_REFUNDACE']=float(refund_total_money)


    placeholder['TMPREFUNDS']=refund_comment
    placeholder['TMPLINKS']=links
    placeholder['TMP_HODNOCENI']=user_rm

    placeholder['TMP_ZATRIDENI']=payee['Zatřídění']
    placeholder['TMP_TYP']=payee['Typ']


    user_path = project_path+trans_user+'/'
    os.makedirs(user_path, exist_ok=True)
    target_file=user_path+'README.md'
    user_report.to_csv(user_path+'user_report.csv', sep=',', encoding='utf-8')


    fp = open('templates/user_template.md')
    template = fp.read()
    template = template.format(**placeholder)

    f = open(target_file,'w+')
    f.write(template)
    f.close()
    #os.remove(filename)

    df = pd.DataFrame([placeholder])

    return df

def normalized_date(mydate):
    """Take a string as 2013-02-01 or zero string a and return a normalized date including infinity"""

    try:
        return datetime.strptime(mydate, '%Y-%m-%d').date()
    except ValueError:
        return datetime.max.date()

def date_range(row):
    """Return boolean value whether the given row has time intersect with dates."""
    t1start=startDate
    t1end=endDate

    t2start = normalized_date(row['Začátek'])
    t2end = normalized_date(row['Konec'])

    return (t1start <= t2start <= t1end) or (t2start <= t1start <= t2end)


def validate_contracts(payroll):
    """Return payroll in the given period."""

    mask = payroll.apply(date_range, axis=1)
    return payroll[mask]

def refundation_overview(role, hours):
    '''This will print part of the report of other incomes of the person
    in the given month, so that we can adjust the party salary.'''

    this_other_incomes = other_incomes[ other_incomes['Funkce'] == role ].copy()
    justification = ''

    if len(this_other_incomes) != 0:

        this_other_incomes['Měsíční částka'] = 0

        hourly = this_other_incomes [ this_other_incomes['Výpočet'] == 'hodinově' ]['Výše příjmu'].iloc[0]


        if hourly: this_other_incomes.loc [ this_other_incomes['Výpočet'] == 'hodinově' , 'Měsíční částka'] = hours*hourly

        monthly = this_other_incomes [ this_other_incomes['Výpočet'] == 'měsíčně' ]['Výše příjmu'].iloc[0]
        if monthly: this_other_incomes.loc [ this_other_incomes['Výpočet'] == 'měsíčně' , 'Měsíční částka'] = monthly

        justification += role.capitalize()+' má dále z titulu své funkce za tento měsíc nárok na následující příjmy:\n\n'

        this_other_incomes['Sazba'] = this_other_incomes['Výše příjmu'].map(str)+' Kč '+this_other_incomes['Výpočet'].map(str)
        this_other_incomes = this_other_incomes[['Typ příjmu', 'Sazba', 'Měsíční částka' ]]
        total = this_other_incomes['Měsíční částka'].sum()
        this_other_incomes=this_other_incomes.rename(columns = {'Měsíční částka':'Měsíční částka (Kč)'})
        justification += tabulate(this_other_incomes.as_matrix(), headers=['Typ příjmu', 'Sazba', 'Měsíční částka (Kč)'], tablefmt="pipe", floatfmt=".1f")

        justification += '\n\nČástky vyplácené jinými subjekty jsou uvedeny v přibližné výši.'
    else:
        justification += 'U této osoby nejsou evidovány žádné příjmy, na které by měla nárok v souvislosti s funkcí.'
        total = 0
    return (justification,total)

def download_sheet():

    target_files = [ 'Lidé', 'Smlouvy', 'Týmy' ]

    files_exist = True

    for myfile in target_files:
        if not os.path.isfile('.cache/'+myfile+'.csv'):
            files_exist = False
            break


    if not files_exist or not usecache:
        sheets = Sheets.from_files('client_id.json', 'storage.json')
        os.makedirs('.cache', exist_ok=True)
        url = settings.PAYROLL_SHEET
        s = sheets.get(url)
        csv_name = lambda title, sheet, dialect: '.cache/%s.csv' % (sheet)
        s.to_csv(make_filename=csv_name)


def create_monthly_bonus_table(payroll):
    """Create a table from the payroll for the given month"""

    # postup: otestujeme existenci, pokud existuje, sloučíme, pokud ne, vytvoříme a odešleme
    mypath = 'odmeny/' + year + '/' + monthalone + '/odmeny.tsv'
    mylink = settings.GITHUB_TRANSPARENCY_REPO_RAW+mypath
    r = requests.get(mylink)

    target_cache_file='.cache/monthly_bonuses.tsv'


    if r.status_code == requests.codes.ok:
        print('The file already exist on the server. You can find it on the address:')
        print(settings.GITHUB_TRANSPARENCY_REPO+mypath)
     # NOT FINISHED:
     #   if prompt('Do you wish to UPDATE the file from the current payroll?'):
     #       # we will update the github file with google file
     #       github_payroll = pd.read_csv(target_cache_file, sep='\t', encoding='utf-8', header=0)
     #       df = pd.merge(df, lide_df, how='inner')
     #       gh = Github(GITHUB_USER, GITHUB_PASS)
     #       repository = gh.repository('organization-name', 'repository-name')
     #   else:
     #       return None
    else:  # file does not exist and will be created form google payroll

        payroll = payroll[payroll['Úkolovka']>0.0].sort_values('Zodpovídá')

        payroll[payroll['Úkolovka']==0.0]['Skutečná odměna']=0.0

        payroll.to_csv(target_cache_file, sep='\t', encoding='utf-8',
            columns=['Zkratka', 'Zodpovídá', 'Jméno a příjmení', 'Funkce', 'Úkolovka', 'Skutečná odměna', 'Odpočet'], index=False)

        fp = open(target_cache_file)
        file_contents = fp.read()

        g = Github(settings.GITHUB_USER, settings.GITHUB_PASS)

        org = g.get_organization(settings.GITHUB_ORG)
        repo = org.get_repo(settings.GITHUB_REPO)
        print(repo)
        print(file_contents)
        repo.create_file("/"+mypath, 'Vzdálené vytvoření souboru s bonusy za '+month, file_contents)


def report_time(start):
    print('Time elapsed: {0:.3f} seconds. '.format(time.time() - start))


def load_bonuses(month):
    """Given the month as string (such as 2017-02), return the pandas dataframe with the bonuses (variable part of
    income) """

    mypath = 'odmeny/' + year + '/' + monthalone + '/odmeny.tsv'
    mylink = settings.GITHUB_TRANSPARENCY_REPO_RAW+mypath
    r = requests.get(mylink)

    target_cache_file='.cache/monthly_bonuses.tsv'

    if r.status_code == requests.codes.ok:
        safe_download(mylink, target_cache_file)
    else:  # file does not exist and has to be created first
        FileNotFoundError('The file with bonuses does not yet exist. You have to create it first with command ...')

    df = pd.read_csv(target_cache_file, header=0, sep='\t', encoding='utf-8', dtype={'Skutečná odměna': np.float32,
                                                   'Úkolovka': np.float32, 'Odpočet': np.float32})

    df.update(df[['Odpočet', 'Skutečná odměna']].fillna(0.0))

    return df

def generate_project_files(project):
    """Create all the contract work files for the given project"""

    target_cache_file='.cache/monthly_bonuses.tsv'


    mypath = 'odmeny/' + year + '/' + monthalone + '/odmeny.tsv'
    mylink = settings.GITHUB_TRANSPARENCY_REPO_RAW + mypath

    zkratka = str(projects_register.loc[find_project_by_name(project),'Zkratka'])

    project_path = 'odmeny/tymy/'+ zkratka + '/' + year + '/' + monthalone + '/'
    os.makedirs(project_path, exist_ok=True)

    # one person can have only one role in a given project
    print('\n' + colored('processing project ' + project, 'blue'))
    project_users = payroll[payroll['Tým'] == project].copy()
    user_ids = project_users['Id'].astype(str).tolist()

    # task_reward_file = project_path + 'task_rewards.csv'
    # second_run = os.path.isfile(task_reward_file)

    #if second_run:
        # read the tasks data
    tasks_data = bonuses[ bonuses['Zkratka'] == zkratka ].fillna(0.0)

        # print(tasks_data)
    # print (user_ids)

    # we shall create report for one user from now on

    project_summary = pd.DataFrame()

    links = '\n\n'

    for user_id in user_ids:
        # print('printing for user '+user_id)
        placeholder = create_work_report(project, user_id,project_path)
        project_summary = pd.concat([project_summary,placeholder], ignore_index=True)
        # user_name, trans_user, refund_total_money, max_task_money, party_money
        # break
    project_summary = project_summary.round(0)



    # 3. create a project report

    project_summary['Link'] = '[' + project_summary['TMPNAME'] + '](' + project_summary['TMPTRANSLIT'] + '/)'
    team_table = tabulate(project_summary[['Link', 'TMP_SKUTECNA_ODMENA_CELKEM']].as_matrix(), headers=['Jméno a příjmení', 'Odměna od strany (Kč)'],
                          tablefmt="pipe", floatfmt=".2f")

    placeholder = {}
    placeholder['TMPTEAM'] = project
    placeholder['TMPTIMERANGE'] = month
    placeholder['TMPTEAMTABLE'] = team_table

    target_file = project_path + 'README.md'

    fp = open('templates/team_template.md')
    template = fp.read()
    template = template.format(**placeholder)

    f = open(target_file, 'w+')
    f.write(template)
    f.close()

    # project_summary[['TMPTEAM', 'TMPNAME', 'TMPFUNCTION', 'TMP_SKUTECNY_PAUSAL', 'TMP_SKUTECNA_HODINOVKA_POD','TMP_SKUTECNA_HODINOVKA_NAD',
    #                 'TMP_SKUTECNA_UKOLOVKA', 'TMP_SKUTECNA_MIMORADNA_ODMENA', 'TMP_SKUTECNY_ODPOCET', 'TMP_SKUTECNA_REFUNDACE', 'TMP_SKUTECNA_ODMENA_CELKEM']]
    return project_summary

#########################################################################



#########################################################################
#                       PROGRAM INTERNALS
# first we have to find out who are the members of the team and what is the
# time scale

# then we shall download all necessary information for the reports
# for all team members included in one big chunk

# redmine = Redmine(settings.REDMINE_URL, key=settings.REDMINE_KEY, version=settings.REDMINE_VERSION)


# dates are always gonna be date types
# month is goint to be simple string such as '2016-02'

# RESOLVING THE CORRECT MONTH(S)

try:
    month=args.month
except AttributeError:
    # if month is not a valid time, use last month
    today = date.today()
    first = today.replace(day=1)
    lastMonth = first - timedelta(days=1)
    month = str(lastMonth.strftime("%Y-%m"))

#month='2017-01'

startDate=datetime.strptime(month+'-01', '%Y-%m-%d').date()
endDate=last_day(month)
actual_business_days = business_days(startDate,endDate)


os.makedirs('.cache', exist_ok=True)

download_sheet()
projects_register = build_projects_register()
print(projects_register)
year, monthalone = month.split('-')
payroll = read_payroll()

#print(payroll)
#print(payroll)

payroll = validate_contracts(payroll) # filter only contracts, that are valid in some of the range given

#print(payroll)

other_incomes=read_other_incomes()
other_incomes = validate_contracts(other_incomes) # show only in the given time

used_projects = payroll['Tým'].unique()

#try:
#    teams=args.teams
#    teams = map(find_project_by_identifier, teams)  # convert to project ids
#except AttributeError:

teams = used_projects

# print(teams)

#print(payroll)

user_ids = payroll['Id'].copy().astype(str).tolist()
data_chunk = get_data_chunk(startDate,endDate,user_ids)

create_monthly_bonus_table(payroll) # should be linked to command line parameters

bonuses = load_bonuses(month)

# print(bonuses)

project_summary = pd.DataFrame()

for project in used_projects:
    placeholder=generate_project_files(project)
    project_summary = pd.concat([project_summary, placeholder], ignore_index=True)


project_summary['Link'] = '[' + project_summary['TMPNAME'] + '](../../tymy/'+ project_summary['TMPZKRATKA']+\
                          '/'+year+'/'+monthalone +'/'+ project_summary['TMPTRANSLIT'] + '/)'
summary = project_summary[['TMPZKRATKA','TMPTEAM', 'TMPNAME', 'TMP_SKUTECNE_PROCENTO','TMP_TYP', 'TMP_SKUTECNA_ODMENA_CELKEM', 'Link', 'TMP_ZATRIDENI']].copy()
summary['name']=summary['TMPTEAM']

summary = pd.merge(summary, projects_register, how='left', on=['name'])


org_table = tabulate(summary[['TMPZKRATKA','Link', 'TMP_SKUTECNE_PROCENTO', 'TMP_SKUTECNA_ODMENA_CELKEM']].as_matrix(),
                      headers=['Tým','Jméno a příjmení', 'Nasazení (%)', 'Odměna od strany (Kč)'],
                      tablefmt="pipe", floatfmt=".2f")

org_table_display = tabulate(summary[['TMPZKRATKA','TMPNAME', 'TMP_SKUTECNE_PROCENTO', 'TMP_SKUTECNA_ODMENA_CELKEM']].as_matrix(),
                      headers=['Tým','Jméno a příjmení', 'Nasazení (%)', 'Odměna od strany (Kč)'],
                      tablefmt="plain", floatfmt=".0f")

mydir = 'odmeny' + '/'+year+'/'+monthalone
os.makedirs(mydir, exist_ok=True)

myheader=['Tým', 'Jméno a příjmení', 'Typ', 'Odměna']
summary.loc[ summary['TMP_TYP'] != 'IČO' ,['TMPZKRATKA','TMPNAME', 'TMP_TYP', 'TMP_SKUTECNA_ODMENA_CELKEM']].to_csv(mydir + '/zamestnanci.tsv', header=myheader, sep="\t",index=False)
summary.loc[ summary['TMP_TYP'] == 'IČO' ,['TMPZKRATKA','TMPNAME', 'TMP_TYP','TMP_SKUTECNA_ODMENA_CELKEM']].to_csv(mydir + '/dodavatele.tsv', header=myheader, sep="\t", index=False)

# project_summary[['TMPTEAM', 'TMPNAME', 'TMPFUNCTION', 'TMP_SKUTECNY_PAUSAL', 'TMP_SKUTECNA_HODINOVKA_POD','TMP_SKUTECNA_HODINOVKA_NAD',
#                 'TMP_SKUTECNA_UKOLOVKA', 'TMP_SKUTECNA_MIMORADNA_ODMENA', 'TMP_SKUTECNY_ODPOCET', 'TMP_SKUTECNA_REFUNDACE', 'TMP_SKUTECNA_ODMENA_CELKEM']]

placeholder = {}
placeholder['TMPTIMERANGE'] = month
placeholder['TMPORGTABLE'] = org_table
print(org_table_display)

target_file = mydir + '/README.md'

teams_summary = summary.groupby(['Rozpočtová jednotka','TMP_ZATRIDENI'])['TMP_SKUTECNA_ODMENA_CELKEM'].sum().reset_index()

myheader=['Rozpočet','Položka', 'Náklady']
teams_summary_pretty = tabulate(teams_summary[['Rozpočtová jednotka','TMP_ZATRIDENI', 'TMP_SKUTECNA_ODMENA_CELKEM']].as_matrix(),
                      headers=myheader,
                      tablefmt="pipe", floatfmt=".2f")

teams_summary[['Rozpočtová jednotka','TMP_ZATRIDENI', 'TMP_SKUTECNA_ODMENA_CELKEM']].to_csv(mydir + '/cerpani_rozpoctu.tsv', header=myheader, sep="\t", index=False)

placeholder['TMPAGREGATEDTABLE'] = teams_summary_pretty

fp = open('templates/organization_template.md')
template = fp.read()
template = template.format(**placeholder)

f = open(target_file, 'w+')
f.write(template)
f.close()


'''
print(user_projects)
print(user_issues)
print(projects_register)
'''
