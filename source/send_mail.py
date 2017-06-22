#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import httplib2
import datetime

from googleapiclient import errors
from apiclient import discovery
from operator import itemgetter
import calendar_parcer
from source import TODAY, add_log, LOG_FILE, SCOPES, EQW_LIST
from monitoring_sheet_parcer import parse_sheet

SCOPES = SCOPES.get('email')
credentials = calendar_parcer.get_credentials(SCOPES, 'gmail-python.json')
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    import base64
    from email.mime.text import MIMEText

    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print(
            'Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def get_shortcut(project_name):
    """Возвращаем устаявшиеся сокращения проектов
    """
    # todo Переписать на соответствии network_id

    eqw_list = EQW_LIST
    for prj in eqw_list:
        if prj[0] == project_name:
            return prj[1]


def get_ref(project_name):
    """Достаём из таблички мониторинг сслыку на сам Мониторинг

    :param:
        project_name:
        monitoring:
            dict from Monitoring table with key = project_name
    :return:
    """
    monitoring = parse_sheet()
    prj_shortcut = get_shortcut(project_name)
    try:
        url = monitoring[prj_shortcut].get('URL')
        return url
    except KeyError:
        log = ' [ERROR] Cannon get url for this Project: {} Return MONITORING_SHEET'.format(project_name)
        add_log(log, file=LOG_FILE)
        return 'https://docs.google.com/a/tetra-soft.ru/spreadsheets/d/1TtPEa9F4Hlw1gb6LHIaKkILOCFdFtAZj5C7YBdyWS4M/edit?usp=sharing'


def get_metadata(supporters, projects, update_list):
    """Возвращаем Мету для почты


    :param supporters:
    :param projects:
    :param update_list:
    :return:
    """
    dict_after_check = {}
    sup_data = {}  # Дикт с именам саппортеров для складирования проектов

    for update in update_list:
        p_n = update.get('prj_name')  # project_name
        p_t = datetime.datetime.fromtimestamp(update.get('prj_time'))  # project time
        s_n = update.get('sup_name')  # supporter_name
        s_id = update.get('sup_id')  # supporter id
        supporter_dict = supporters['day'].get(s_n) if supporters['day'].has_key(s_n) else supporters['night'].get(s_n)
        email = supporter_dict.get('email')
        if not sup_data.has_key(s_n):
            sup_data[s_n] = []
        for project in projects:
            if project.get('name') == p_n and project.get('supporter')['id'] == s_id:
                ref = get_ref(p_n)
                data_tuple = (p_t, ref.split('\n')[0], p_n)
                sup_data[s_n].append(data_tuple)
                dict_after_check[s_n] = {
                    'email': email,
                    'data': sup_data[s_n]
                }
                break
    return dict_after_check


def send_email(supporters, projects, list_for_update):
    """Заглавная функция в ней и происходит подготовка и отправка письма

    :param supporters:
    :param projects:
    :param list_for_update:
    :return:
    """
    from hand_check import TEST
    meta = get_metadata(supporters, projects, list_for_update)
    sender = 'me'
    subject = 'Назначены ручные проверки на ' + str(TODAY)
    for supporter in meta:
        name = supporter
        to = 'a.simuskov@tetra-soft.ru' if TEST else meta[supporter].get('email')
        data = meta[supporter].get('data')
        data = sorted(data, key=itemgetter(0))
        main_text = ''
        for d in data:
            text = '<li>Ко времени <b>{}</b> Проект: <a href="{}">{}</a><br></li>'.format(*d)
            main_text = main_text + text
        message = """
        <html>
            <head></head>
            <body>
                <p>
                    Здравствуйте.<br>
                </p>
                <p>
                    На вас назначены проверки по следующим проектам:<br>
                    <legend>
                            {list}
                    </legend>
                </p>
                <p>
                    Не забывайте отмечать выполенные проверки!
                    <br>
                    Доступ можно получить по ссылке - 
                    <a href='http://192.168.0.4/mantis/plugin.php?page=Adamant/util&id=projects_check'>Ручные проверки</a>.
                    <br>
                </p>
                <p>
                Параметры доступа к мониторингу можно получить в таблице
                 <a href='https://docs.google.com/a/tetra-soft.ru/spreadsheets/d/1TtPEa9F4Hlw1gb6LHIaKkILOCFdFtAZj5C7YBdyWS4M/edit?usp=sharing'>
                 Мониторинг</a>.
                </p>
            </body>
        </html>    
        """.format(name=name, list=main_text)

        message = create_message(sender, to, subject, message.encode('utf-8'))
        send_message(service, to, message)


def main():
    print(get_ref(""))


if __name__ == '__main__':
    main()
