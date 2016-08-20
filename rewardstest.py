#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Unit test for rewards.py'''

import rewards
import unittest
import pandas as pd
from datetime import date

class KnownValues(unittest.TestCase):

    known_values = (
        (17,  'jméno a příjmení',  'Mikuláš Ferjenčík'),
        (7,   'denní počet hodin', 4) ,
        (164, 'právní postavení',  'dodavatel strany')
      )

    def test_known_payrol(self):
        '''reading the payroll should give the expected values'''


        known_payroll = rewards.read_payroll('tests/test_payroll.csv')

        for row, col, val in self.known_values:
            read_value = known_payroll[col][row]
            self.assertEqual(read_value,val)

    reference_business_days = (
        (date(2016,1,1),    date(2016,1,31),  20),
        (date(2016,1,1),    date(2016,12,31),  252),
        (date(2016,7,1),    date(2016,7,24),   14),
        (date(2015,12,20),  date(2016,1,7),    11)
      )

    def test_business_days(self):
        '''The bussiness days should be like those on the web
        http://kalendar.beda.cz/pracovni-kalkulacka '''

        for startDate, endDate, number in self.reference_business_days:
            self.assertEqual(number, rewards.business_days(startDate,endDate))

    reference_month_last_day = (
        ('2016-02',29),
        ('2015-01',31),
        ('2017-02',28),
        ('2016-12',31),
        ('2016-11',30)
      )

    def test_last_month(self):
        '''Check the number of the last day in month.'''

        for month, day in self.reference_month_last_day:
            self.assertEqual(month+'-'+str(day), str(rewards.last_day(month)))

    startDate='2016-06-01'
    endDate='2016-06-30'
    user_ids=['3','4','16','17']
    reference_link='https://redmine.pirati.cz/time_entries.csv?c[]=project&c[]=user&c[]=activity&c[]=issue&c[]=hours&c[]=cf_16&c[]=spent_on&f[]=spent_on&f[]=user_id&f[]=&op[spent_on]=><&op[user_id]==&utf8=%E2%9C%93&v[spent_on][]=2016-06-01&v[spent_on][]=2016-06-30&v[user_id][]=3&v[user_id][]=4&v[user_id][]=16&v[user_id][]=17'

    def test_download_link(self):
        '''Test the download link for '''

        tested_link = rewards.create_link(self.startDate,self.endDate,self.user_ids,'csv')
        self.assertEqual(tested_link, self.reference_link)

    reference_project_pairs = (
      ('34', 'parlamentní tým'),
      ('15', 'zastupitelstvo hl. m. Prahy')
    )

    def test_project_lookup(self):
        '''Test the project number lookup'''

        for number, name in self.reference_project_pairs:
            self.assertEqual(str(number), str(rewards.find_project_number(name)))

if __name__ == '__main__':
    unittest.main()
