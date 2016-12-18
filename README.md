Byro-reward
===========

How to use
----------

In general:

```
rewards.py [-n|-f|-a] [-u USER] [-t TIME] [-wd NUM] [--all]
```

Workflow:

```
# STEP 1
# rewards.py praha/zastupitele   # create a local report template for all team members for last month
# rewards.py 3                   # create a local report template for user number 3 on redmine for last month
# rewards.py 3 2015-08           # -||- for month 2015-08
#
# STEP 2
# review the summary file and fill in the data to the common table of the team (rewards)
#
# STEP 3
#
# rewards.py submit    # fill in the common table data to the local reports, send them to the github server
#                      # generate an accounting data lines and submit them to the server, generate a redmine task for the
#                      # superior to pay the requested amounts
```

Install
-------

Ubuntu:


```
sudo -H pip3 install pandas czech_holidays tabulate termcolor trans
```

Scheme
------

STEP 1

- [X] get a list of users from payrol
- [ ] apply to all users, download big chunk of data for the given month
- [ ] apply to one user, find his reward_model and its parameters
- [ ] calculate all the variables
- [ ] if the file for the 
- [ ] graph data
- [ ] create local report template
- [ ] create the summary for all users
- [ ] send all the team members an e-mail reminder of the meeting and tasks due


STEP 2

- [ ] review the team report and fill in the data to the file ''

STEP 3

- [ ] generate an accounting data lines (open data)
- [ ] send the created data to remote git server
- [ ] generate a redmine task for the superior to pay the requested amounts

Other tasks

- [ ] integration into byro

Author: Jakub Michálek, Česká pirátská strana
License: GNU GPL v3

Rules
-----

* It should be simple enough for users to make minimum mistakes -> no refunds are the basic
* Who wants to see how the hours spent for non paid, can use "neproplácet" refund (not expected)
* Everybody can be asked to help in a different team on a task of his
  expertise and is expected to do so, provided that the team leaders agree
  on conditions
* The ambition is to use this in the whole Czech Pirate Party for
  people who are rewarded on a monthly basis. For this purpose we have
  to contact the following teams:

  - [ ] The deputies of Prague Assembly (Jakub)
  - [ ] The Prague Chamber (Ondra)
  - [ ] The department for medias (Mikuláš)
  - [ ] The presidium (Jakub/Vojta)
  - [ ] The personal department (Kuba Nepejchal)
  - [ ] The newly elected regional assemblies (Jakub)

https://redmine.pirati.cz/projects/kspraha/wiki/Odm%C4%9B%C5%88ov%C3%A1n%C3%AD
