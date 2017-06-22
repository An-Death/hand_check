#!/bin/python
#-*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import codecs
"""
Необходимо заполнить все пустые поля
"""


secure = {
    'mantis_http': {
        'user': '',
        'password': '',
        'url':'',
        'login_url':''
    },
    'db':{
        'mantis':{
            'name':'',
            'user':'',
            'password':'',
            'host':'',
            'port':''
        },
        'cb':{
            'name':'',
            'user':'',
            'password':'',
            'host':'',
            'port':''},
        'test':{
            'name': '',
            'user':'',
            'password':'',
            'host':'',
            'port':''
        }
    },
    'scopes':{
        'calendar':'https://www.googleapis.com/auth/calendar.readonly',
        'sheet':'https://www.googleapis.com/auth/spreadsheets.readonly',
        'email':'https://www.googleapis.com/auth/gmail.compose'
    },
    'application_name':'',
    'calendars':[
        ('Отпуска службы сопровождения', 0),
        ('Расписание 2/2', 2),
        ('Смены 24 на 7', 3),
        ('Расписание 5/2', 1)
        ],
    'lg_list':(),
    'project_with_tasks':(
    ),
    'eqw_list': [
    ]
}
with codecs.open('secure/secure.json', 'w', encoding='utf-8') as wf:
    wf.write(json.dumps(secure, ensure_ascii=False, sort_keys=True, indent=3))