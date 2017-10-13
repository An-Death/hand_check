#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os

import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from datetime import datetime, timedelta, date, time
from time import mktime

import dbconnect
import source

flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

SCOPES = source.SCOPES.get('calendar')


def get_credentials(scopes, credential_file_name):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   credential_file_name)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(source.CLIENT_SECRET_FILE, scopes)
        flow.user_agent = source.APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_calendar_json():
    """Если файла не существует или он старше 30 дней, создаётся новый"""
    # todo добавить try чтобы отлавливать ошибки при подключегнии к google.com

    json_dict = {}
    credentials = get_credentials(SCOPES, 'calendar-python.json')
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

    for calendar in calendar_list['items']:
        json_dict[calendar['summary']] = calendar

    source.write_json(source.JSLIST, json_dict)


def calendars_lists():
    """ Раз в месяц обновляет json с календарями"""

    if not os.access(source.JSLIST, os.F_OK):
        create_calendar_json()

    ctf = os.stat(source.JSLIST).st_ctime  # time of last update file
    last_update = datetime.fromtimestamp(ctf)  # string time format
    now = datetime.now()
    dif = now - last_update
    delta = timedelta(days=30)

    if dif > delta:
        os.remove(source.JSLIST)
        create_calendar_json()

    return source.read_json(source.JSLIST)


def parse_calendar(item):
    """Возвращает ID календаря, item = имя календаря из CALENDARS """

    calendars = calendars_lists()
    calendar_id = calendars[item].get('id')
    return calendar_id


def time_master(n):
    """Возвращает время Мин и Макс текущего дня"""

    today_day = date.today()  # текущее число
    default_time = (time(8, 0, 0), time(23, 0, 0), time(20, 00, 00))
    t = datetime.combine(today_day, default_time[n]).isoformat()
    return t


def to_unix_time(dts):
    """
    Переводим время из ответа Google в unix.type для сравнения в питоне
    dts = datetime_string, лишнее обрезаем
    """
    if dts is not None:
        unix_time = mktime(datetime.strptime(dts[:19], "%Y-%m-%dT%H:%M:%S").timetuple())
        return int(unix_time)


def support_sort(schedule, name):
    """Добавляет grade в name"""
    grade_list = source.CALENDARS
    if name in source.LG_LIST:
        grade = 99
        return grade
    else:
        for l in grade_list:
            if schedule == l[0]:
                grade = l[1]
                return grade
            elif schedule == 'RRT расписание':
                return 1


def out_of_office(name, outs):
    """
    Проверяем входит ли саппортер в ранее сформированный список отсутствующих
    Принимаем строку с именем и проверём на вхождение в листе outs
    """
    for event in outs:
        if name in event:
            return True
        else:
            continue


def get_supporters():
    """Возвращает словарь с листами дневных смен, ночных смен и отпусков."""

    # todo добавить try чтобы отлавливать ошибки при подключегнии к google.com

    shifts = {'day': {},
              'night': {},
              'out_of_office': []
              }

    credentials = get_credentials(SCOPES, 'calendar-python.json')  # todo move to special func
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    start_day = time_master(0) + '+0300'  # Время 8:00 MSK // + Z is default UTC timezone. requared for request
    end_day = time_master(1) + '+0300'  # Время 23:00 MSK
    mid_day = to_unix_time(time_master(2) + '+0300')  # Время 20:00 MSK converted to unix_time
    for calendar in source.CALENDARS:
        calendarId = parse_calendar(calendar[0])
        eventsResult = service.events().list(
            calendarId=calendarId, timeMin=start_day, timeMax=end_day, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            # todo Отлавливать ошибку пустых эвентосов
            pass
        for event in events:
            start = to_unix_time(event['start'].get('dateTime'))  # переводим в unix_time
            end = to_unix_time(event['end'].get('dateTime'))  # переводим в unix_time
            name = event['summary']
            schedule = event['organizer'].get('displayName')
            grade = support_sort(schedule, name)
            # location = event  # todo event['location']
            outs = shifts['out_of_office']
            shift = 'day' if start < mid_day else 'night'

            if calendar == 'Отпуска службы сопровождения':
                outs.append(name)
            elif name.count(" ") > 0:
                # todo Тупое условие. если в описании есть пробелы, значит эвент будет отбрасываться
                outs.append(name)
            elif out_of_office(name, outs):
                continue
            # todo Добиться от Макса корректно отмечать в Календаре отсутствующих, тоогда придумаем как парсить
            # elif location is "out":
            #     continue
            else:
                user_info = dbconnect.get_user_info(name)  # from dbconnect return dict{email, login, id}
                if user_info:
                    email = user_info.get('email')
                    login = user_info.get('login')
                    sup_id = user_info.get('id')
                else:
                    email, login, sup_id = (None, ) * 3  # if did't find any data in DB

                supporter_data = {
                    'id': sup_id,
                    'name': name,
                    'organizer': schedule,
                    'grade': grade,
                    'start': start,
                    'end': end,
                    'email': email,
                    'login': login
                }
                dict_shift = shifts[shift]
                dict_shift[supporter_data.get('login')] = supporter_data

    return shifts


def main():
    shift = get_supporters()

    source.write_json('log/shifts_test.json', shift, indent=4)


if __name__ == '__main__':
    main()
