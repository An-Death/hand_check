# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
import json
import datetime
with codecs.open('secure/secure.json', 'r', encoding='utf-8') as fd:
    SECURE = json.load(fd)

SCOPES = SECURE.get('scopes')
APPLICATION_NAME = SECURE.get('application_name')


# todo Создать возможность добавлять, удалять календари из переменной
CALENDARS = SECURE.get('calendars')

CLIENT_SECRET_FILE = 'secure/client_secret.json'

LG_LIST = SECURE.get('lg_list')
EQW_LIST = SECURE.get('eqw_list')
MON_REF = SECURE.get('mon_ref')
PC_REF = SECURE.get('pc_ref')

JSLIST = "log/calendars.json"
LOG_FILE = "log/hand_check.log"
MOT_TABLE = "log/monitoring_data.json"

TASK = SECURE.get('project_with_tasks') # Проекты с доп задачами: Сводки, Статусы

TODAY = datetime.datetime.today().date()

def write_json(file, data, indent=4, rw='w'):
    with codecs.open(file, rw, encoding='utf-8') as wf:
        wf.write(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=indent))


def read_json(file):
    with codecs.open(file, 'r', encoding='utf-8') as fd:
        calendars_list = json.load(fd)
        return calendars_list


def return_fd(path_to_file):
    fd = codecs.open(path_to_file, 'a', encoding='utf-8')
    return fd


def add_log_mantis(update_dict, file_descriptor):
    file_descriptor.write(
        '{dt} <d>{u}</d>: update admin information: set need=1, user={sup}, time next check set to {up_date} for '
        'project <d>{p_name}</d> \n'.format(
            dt=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            u="Bot",
            sup=update_dict.get('sup_name'),
            up_date=datetime.datetime.fromtimestamp(update_dict.get('prj_time')),
            p_name=update_dict.get('prj_name')
        ))


def close_fd(file_descriptor):
    file_descriptor.close()


def add_log(data, file=LOG_FILE):
    with codecs.open(file, 'a', encoding='utf-8') as fd:
        log_data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + data
        fd.write(log_data)
