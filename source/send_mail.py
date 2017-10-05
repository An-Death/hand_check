#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import base64
import datetime
import httplib2

from googleapiclient import errors
from apiclient import discovery
from operator import itemgetter

import calendar_parcer
import source
from monitoring_sheet_parcer import parse_sheet
from email.mime.text import MIMEText


SCOPES = source.SCOPES.get('email')
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

    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def send_message(service, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    user_id = 'me'
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

    eqw_list = source.EQW_LIST
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
    monitoring = parse_sheet()  # todo Вынести переменную чтобы постоянно не обращаться к файлу?
    prj_shortcut = get_shortcut(project_name)
    try:
        url = monitoring[prj_shortcut].get('URL')
        return url
    except KeyError:
        log = '[ERROR] Cannon get url for this Project: {} Return MONITORING_SHEET'.format(project_name)
        source.add_log(log, file=source.LOG_FILE)
        return source.MON_REF


def prepare_data_to_send(supporters, projects, update_list):
    """Возвращаем Мету для почты


    :param supporters:
    :param projects:
    :param update_list:
    :return:
    """

    dict_after_check = {}
    sup_data = {}  # Дикт с именам саппортеров для складирования проектов

    for update in update_list:
        project_name = update.get('prj_name')
        project_time = datetime.datetime.fromtimestamp(update.get('prj_time'))
        supporter_name = update.get('sup_name')
        supporter_id = update.get('sup_id')
        supporter_dict = supporters['day'].get(supporter_name) if supporter_name in supporters['day'] else supporters['night'].get(supporter_name)
        email = supporter_dict.get('email')
        if supporter_name not in sup_data:
            sup_data[supporter_name] = [] # Создаём лист с именем сапортера
        for project in projects:
            if project.get('name') == project_name and project.get('supporter')['id'] == supporter_id:
                ref = get_ref(project_name)
                data_tuple = (project_time, ref.split('\n')[0], project_name) # Всегда берём первую ссылку и Monitoring
                sup_data[supporter_name].append(data_tuple) # добавляем назначенные на него проекты
                dict_after_check[supporter_name] = {
                    'email': email,
                    'data': sup_data[supporter_name]
                } # Запихивыем в дикт запись типа : 'Симуськов': {email, и лист из кортежей с проектами}
                break
    return dict_after_check


def send_email(letters):
    """Заглавная функция в ней и происходит подготовка и отправка письма

    :param letters
    :return:
    """
    from hand_check import TEST

    sender = 'me'
    subject = 'Назначены ручные проверки на {}'.format(str(source.TODAY))
    for s_n in letters:
        name = s_n
        to = source.EMAIL_FOR_TEST if TEST else letters[s_n].get('email')
        data = letters[s_n].get('data')
        data = sorted(data, key=itemgetter(0))  # sorted by Time
        letter_text = []
        for d in data:
            text = '<li>Ко времени <b>{}</b> Проект: <a href="{}">{}</a><br></li>'.format(*d)
            letter_text.append(text)
        main_text = ''.join(letter_text)
        message = """
        <html>
            <head></head>
            <body>
                <p>
                    Здравствуйте.<br>
                </p>
                <p>
                    На вас назначены проверки по следующим проектам:<br>
                    <ol>
                        {list}
                    </ol>
                </p>
                <p>
                    Не забывайте отмечать выполенные проверки!
                    <br>
                    Доступ можно получить по ссылке - 
                    <a href={pc}>Ручные проверки</a>.
                    <br>
                </p>
                <p>
                Параметры доступа к мониторингу можно получить в таблице
                 <a href={monitoring}>
                 Мониторинг</a>.
                </p>
            </body>
        </html>    
        """.format(name=name, list=main_text, monitoring=source.MON_REF, pc=source.PC_REF)

        message = create_message(sender, to, subject, message.encode('utf-8'))
        send_message(service, message)


def main():
    print(get_ref(''))


if __name__ == '__main__':
    main()
