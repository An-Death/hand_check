#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import requests

from collections import defaultdict
from datetime import datetime, date
from time import time, mktime

from source.calendar_parcer import get_supporters
from source.dbconnect import get_projects  # , update_table, check_after_update
from source.send_mail import send_email, prepare_data_to_send
from source import source

# todo Придуть/создать CLI

UNIX_NOW = int(time())
TEST = False


def send_telegramm(who, message):
    """
    :param who: chat_id
    :param message:
    :return:
    """
    token = source.TELEGRAMM_TOKEN
    url = 'https://api.telegram.org/bot{}/'.format(token)

    pass


def overdue(projects):
    """
    Создаём дикт с задержками
        old = 1 day
        too_old = 3 day
    :return:
        delays = {
        old: list,
        too_old: list
        }
    """
    unix_now = UNIX_NOW
    too_old = []
    old = []
    delays = {
        'too_old': too_old,
        'old': old
    }
    unix_td = 259200  # 3 дня
    # todo ?? Сделать нормальное сравнение в днях
    for project in projects:
        tm_diff = unix_now - project['time']
        if tm_diff > unix_td:
            too_old.append(project)
        elif project['time'] < unix_now:
            old.append(project)
            # if len(delays['old'] + delays['too_old']) != 0:
            #     send_controller('telegram', delays)
    return delays


def empty_shifts(supporters):
    """
    Определяем пустые смены в dict_shifts
    :return:
        Отправляем в телеграмм пустую смену
        Или False если ничего нет потом переделаем
    """
    if not supporters['day']:
        pass
    elif not supporters['night']:
        pass  # todo Дописать обработку отсутствия людей на смене

    return supporters


def get_problems(condition, projects, supporters):
    """
    Собираем все существующие проблемы:
    1. Пустые смены - отправляем в телеграмм
    2. Не выполненые рп - пищем в лог, более 3х дней пишем на почту
    3. Просрочки > 3х дней
    4. Выводим проблемы в терминал (Опционально argparse)
    condition :
        empty_shifts - После запроса отправляем пустые смены в телеграм, если такие есть
        overdue - Отправляем просрочки по проверкам в телеграм
        non_check - Отправляем не назначенные проверки в телеграм
        all -  всё выше перечисленное, если что-то есть
    """
    # projects = get_projects()
    # supporters = get_supporters()

    if condition == 'shift':
        return empty_shifts(supporters)
    if condition == 'project':
        return overdue(projects)
    elif condition == 'all':
        d = dict(shift=empty_shifts(supporters), delays=overdue(projects), projects=projects)
        return d


def write_old(projects):
    """Записываем просрочки в лог

    :param projects:
    :return:
    """
    if projects:
        olds = []
        for i, p in enumerate(projects, start=1):
            old = '[OLD] {} Project : {p_n} : {p_t} supporter: {s_n}'.format(i,
                                                                             p_n=p.get('name'),
                                                                             p_t=datetime.fromtimestamp(p.get('time')),
                                                                             s_n=p.get('sup')
                                                                             )
            olds.append(old)
        old = '\n'.join(olds)
    else:  # Если None
        old = '[OLD] All projects was checked!'

    source.add_log(old, file=source.LOG_FILE)


def write_updates(up_list):
    """Записывам в лог что на кого назначаем

    :param
        up_list: list of
            {prj_time:int,
            prj_name:str,
            prj_id":int,
            sup_id:int,
            sup_name:str
            }
    :return
        Write to log_file
    """
    for up in up_list:
        text = '[UPDATE] Project : {p_n} : set time : {p_t} set supporter: {s_n}'.format(
            p_n=up.get('prj_name'),
            p_t=datetime.fromtimestamp(up.get('prj_time')),
            s_n=up.get('sup_name')
        )
        source.add_log(text, file=source.LOG_FILE)


def grade_count(shift_list):
    grade = defaultdict(int)

    for sup_name in shift_list:
        sup_dict = shift_list[sup_name]
        grade[sup_dict.get('grade')] += 1
    return grade


def update_table_quere(problems):
    """
    Создаём лист с
    update = {
        'prj_id': id,
        'prj_name': str,
        'prj_time': unix_time,
        'sup_id': id,
        'sup_name'
    }
    Из функции вызываем функцию для апдейта базы dbconnect.update_table()
    
    :param problems: Лист с проблемапи from get_problems
    :return: None
    
    """

    update_list = []
    # for ordinary projects
    cache_1 = {'day': defaultdict(int), 'night': defaultdict(int)}
    # for projects with addition tasks
    cache_2 = {'day': defaultdict(int), 'night': defaultdict(int)}
    supporters = problems['shift']
    projects = problems['projects']
    problem = problems['delays']
    grade_list = {'day': grade_count(supporters['day']), 'night': grade_count(supporters['night'])}

    def sup_iterator(supporters, project, grade_list):
        """
        Проворачивает внутри себя магию и на выходе возвращает Саппортера на которого надо назначить проверку.
        :param grade_list:
        :type supporters: object
        :param supporters: project, grade_list
        :param project:
        :return:
            support_name
        """

        def set_all(n, one_supporter_on_shift=True):
            def re_user(sp):
                user_name = sp.get('login')
                user_id = sp.get('id')
                return {'id': user_id, 'name': user_name}

            for name, supporter in supporters[shift].items():  # keys of dict
                # Проверяем грэйд
                if supporter.get('grade') != n:
                    continue
                # Проверяем смену
                if not supporter.get('end') > p_time > supporter.get('start'):
                    continue
                if one_supporter_on_shift:
                    # Если на смене только один сап - всё на него
                    return re_user(supporter)
                else:
                    # Если на смене больше одного саппортера
                    # Если проект с доп заданием - использует отдельный кэш
                    cache = cache_2[shift] if project.get('con') else cache_1[shift]
                    len_cache = len(cache.keys())
                    if name not in cache:
                        # Если на сапа нету в кэше, мы добавляем запись в дикт с именем сапа
                        # И присвыиваем значение назначенных проектов =1
                        # todo Добавить логирования.
                        cache[name] += 1
                        return re_user(supporter)
                    elif len_cache != gl.get(n):
                        # переходим к следующему саппортеру
                        continue
                    elif len_cache == gl.get(n):
                        # если кл-во сапортеров равно количеству сапов в грейде,
                        # то сравниваем сапортеров по кол-ву назначенных на них проектов
                        last_sup = sorted(cache.items(), key=lambda x: x[1], reverse=True)[-1]
                        cache[last_sup[0]] += 1
                        return re_user(supporters[shift].get(last_sup[0]))

        user_data = (None, None)  # Default assign to None
        p_time = project.get('time')  # unix time int
        shift = project.get('shift')  # string (day/night)
        source.add_log('[INFO] Project {} shift {}'.format(project.get('name'), shift))
        gl = grade_list[shift]
        grade = sorted(gl.keys(), reverse=False)[-1]  # Get highest grade from list
        if gl.get(grade) == 1:
            user_data = set_all(grade)
        elif gl.get(grade) > 1:
            user_data = set_all(grade, one_supporter_on_shift=False)
        source.add_log('[INFO] For project {} was chosen supporter {} at shift [{}]'.format(project.get('name'),
                                                                                            user_data.get('name'),
                                                                                            shift))
        return user_data if user_data else None

    # 1. Если проект уже назначен, пропускаем его
    # 2. Подчищаем проекты от too_old
    # 3. Обновляем время в просреченных проктах, те что менее 3 дней
    for project in projects:
        if project['supporter'].get('id') != 0 and project.get('time') > UNIX_NOW:
            continue
        elif project in problem.get('too_old'):
            projects.remove(project)
            old_log_str = '{time} : [ERROR] : The project " {p_n} " is too old and was removed from tasks'.format(
                time=datetime.today().date(),
                p_n=project.get('name')
            )
            source.add_log(old_log_str, file=source.LOG_FILE)  # Print too old in log
            continue
        elif project in problem.get('old'):  # Update time for old
            time_from_table = datetime.fromtimestamp(project['time']).time()
            update_time = datetime.combine(date.today(), time_from_table)
            project['time'] = (int(mktime(update_time.timetuple()))
                               if project.get('shift') == 'day' else
                               int(mktime(update_time.timetuple())) + 86400)  # update for Night shift projects

        prj_id = project.get('id')
        prj_name = project.get('name')
        prj_time = project.get('time')
        sup_data = sup_iterator(supporters, project, grade_list)
        if sup_data:
            update = {
                'prj_id': prj_id,
                'prj_name': prj_name,
                'prj_time': prj_time,
                'sup_id': sup_data.get('id', 0),
                'sup_name': sup_data.get('name', None)
            }
            update_list.append(update)
        else:
            source.add_log('[ERROR] Cannot get supporter data for project  [ {} ] and shift and time : '.format(
                prj_name))  # , project.get('shift'), prj_time))# todo Add info to error!!!
            continue
            # exit(1)

    return update_list


def htmlrequest(list_for_update):
    """Обновление таблицы пост запросом.

    :params
       list_for_update: dict{sup+prj}
    :return :
        Update Table

    """
    mantis = source.SECURE['mantis_http']
    username = mantis.get('user')
    password = mantis.get('password')
    data = {'username': username, 'password': password}
    s = requests.Session()
    url = mantis.get('url')
    login = s.post(mantis.get('login_url'), data=data)  # just login to mantis
    for update in list_for_update:
        prj_id = update.get('prj_id')
        user = 'user_' + str(prj_id)
        user_id = update.get('sup_id')
        need = 'need_' + str(prj_id)
        date_must_prj = 'datereport_must_' + str(prj_id)
        date_must = datetime.fromtimestamp(update.get('prj_time')).strftime('%Y-%m-%d %H:%M:%S')
        update = {'project': prj_id,
                  user: user_id,
                  need: 'true',
                  date_must_prj: date_must,
                  'crc_data': int(UNIX_NOW)
                  }
        update = s.post(url, data=update)

        # return update


def main():
    if TEST is False:
        # ============Получаем основные переменные===============
        supporters = get_supporters()  # +
        projects = get_projects()  # +
        problems = get_problems('all', projects, supporters)  # +
        list_for_update = update_table_quere(problems)  # +
        # =======================================================

        # =====Сохраняем проекты и саппортеров в json======
        source.write_json('log/projects.json', projects, 3)
        source.write_json('log/shifts.json', supporters, 4)
        # =================================================

        # send_controller(supporters, projects, problems) -
        # send_controller(supporters, projects, problems, after_update=True) -

        # =============Записываем в лог================
        write_old(problems['delays'].get('old', None))
        write_updates(list_for_update)
        # =============================================

        # =======Отправляем запрос на обновление в POST=========
        htmlrequest(list_for_update)  # +
        # ======================================================

        projects_after_update = get_projects()
        # todo def send_unassigned_projects_to_mail()
        letters = prepare_data_to_send(supporters, projects_after_update, list_for_update)
        send_email(letters)

        # отправляем запрос наобновление в базу
        # update_table(list_for_update)
        # print(check_after_update(UNIX_NOW))
    else:
        from source.source import EMAIL_FOR_TEST
        letters = {
            'me': {
                'email': EMAIL_FOR_TEST,
                'data': [('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ('2017-01-01 01:01:01', 'some_ref', 'some_project_name'),
                         ]
            }
        }

        send_email(letters)


if __name__ == '__main__':
    main()
