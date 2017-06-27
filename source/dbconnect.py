#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from time import mktime
from datetime import datetime, time
from sqlalchemy import and_
from sqlalchemy.orm import Session

import source
from dbsource import Cb_users as user_table, Cb_data42 as pr_data
from dbsource import engine
from dbsource import (Mantis_project_check_table as mct,
                      Mantis_user_table as mut,
                      Mantis_project_table as mpt)

MAN = Session(bind=engine('mantis'))
CB = Session(bind=engine('cb'))
#TEST = Session(bind=engine('test'))
LOG = []

def get_shift_by_time(project_time):
    """
    Compare time to sort projects by shifts
    for all project where check_time is less then 8:00 AM - shift = Night
    :param project_time: int
    :return: str(day/night)
    """

    pt = datetime.fromtimestamp(project_time).time()
    start_day = time(8, 0, 0)
    end_day = time(20, 0, 0)
    return 'day' if end_day > pt > start_day else 'night'

def get_projects2():
    """Возвращаем лист с диктами projects
    Больше не используется
    :return: projects
    """

    MANTIS = engine('mantis')
    CLIENT_BASE = engine('cb')
    # todo Переписакть под Session > DONE
    projects = []
    with MANTIS.begin() as man:
        row_projects = man.execute(
            'select mct.id as id, mpt.name as project, need, mct.user, mut.username, mct.time from\
            mantis_project_check_table mct left outer join mantis_project_table mpt on (mct.id=mpt.id)\
            left outer join mantis_user_table mut on (mut.id=mct.user)\
            where mct.need >0 ;'
        )
    for project in row_projects:
        name = unicode(project['project'], 'utf-8')
        shift = get_shift_by_time(project['time'])
        con = True if name in source.TASK else False
        with CLIENT_BASE.begin() as cb:
            select_last_date = "select UNIX_TIMESTAMP(f8360) from cb_data42 where f435='{}';".format(name)
            last_check = cb.execute(select_last_date)
            last_check = last_check.fetchone()[0]
        project = {
            'id': project['id'],
            'name': name,
            'supporter': (project['user'], project['username']),
            'time': project['time'],
            'last_check': last_check,
            'shift': shift,
            'con': con
        }
        projects.append(project)

    source.write_json('log/projects.json', projects, 3)

    return projects


def get_projects():
    """Get dict with projects from DB

    :return
        dict = projects
    """

    projects = []
    row_projects = MAN.query(mct.id, mpt.name, mct.need, mct.user, mut.username, mct.time).\
        outerjoin(mpt, mpt.id == mct.id).\
        outerjoin(mut, mut.id == mct.user).\
        filter(mct.need > 0).\
        all()
    for pr in row_projects:
        shift = get_shift_by_time(pr.time)
        con = True if pr.name in source.TASK else False
        last_check = CB.query(pr_data.f8360).filter(pr_data.f435 == pr.name).one()
        project = {
            'id': pr.id,
            'name': pr.name,
            'supporter': dict(id=pr.user, name=pr.username),
            'time': pr.time,
            'last_check': int(mktime(last_check[0].timetuple())),
            'shift': shift,
            'con': con
        }
        projects.append(project)
    return projects

def get_user_info(summary):
    """
    Получаем email и логин нужного пользователя из мантиса
    На основе summary из календаря
    :return: dict with email , mantis_login , supporter_id
    """

    l_name = r'%{}%'.format(summary)
    try:
        request = CB.query(user_table.e_mail).filter(user_table.fio.like(l_name))
        result = request.first()
        email = result[0]
        login = email.split('@', 1)[0] if email != 'maxim@tetra-soft.ru' else 'm.pavlov'
        sup_id = MAN.query(mut.id).filter_by(username=login).one()[0]
        # fio = result[1] # Можно получать фио
        return {'email': email,
                'login': login,
                'id': sup_id
                #'fio':fio
                }
    except TypeError:
        raise NameError(' [ERROR] Modul : " {} " : User with this summary: "{}" does not exist! '.format('get_user_info()' ,summary))


def update_table(list_for_update):
    """Not useful anymore

    :param list_for_update:
    :return:
    """
    fd = source.return_fd(source.LOG_FILE)
    for up in list_for_update:
        q = MAN.query(mct).get(up.get('prj_id'))
        q.user = MAN.query(mut.id).filter_by(username=up.get('sup_name')).one()[0]
        q.time = up.get('prj_time')
        MAN.commit()
        source.add_log_mantis(up, fd)
    source.close_fd(fd)

def check_after_update(UNIX_NOW):
    """Not ready

    :param UNIX_NOW:
    :return:
    """
    quere = MAN.query(mct).filter(and_(mct.need > 0, mct.user == 0, mct.time < UNIX_NOW ))
    result  = quere.all()
    return result

def main():
    # get_projects2()
    print(get_user_info("Павлов"))
    # query = MAN.query(mct.id, mpt.name, mct.need, mct.user, mut.username, mct.time).outerjoin(
    #     mpt, mpt.id == mct.id
    # )
    # query = query.outerjoin(mut, mut.id == mct.user)
    # rec = query.all()

if __name__ == '__main__':
    main()
