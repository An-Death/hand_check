#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from sqlalchemy import Column, Integer, String, DateTime, TIMESTAMP, DECIMAL, ForeignKey
# from sqlalchemy.orm import relationships     # uselist=false Клюь чтобы возвращать 1 значение. Надо протетстить
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from source import SECURE

Base = declarative_base()


def engine(basename):
    """

    :return: engine
    """
    db = SECURE.get('db')
    def get_port(bn):
        if bn == "mantis" or bn == 'cb':
            return db[bn].get('port')
        else:
            return None

    user = db[basename].get('user')
    password = db[basename].get('password')
    host = '192.168.0.100' if basename is not "test" else '127.1'
    bname = basename if basename is not "test" else 'mantis_hand_check'
    port = get_port(basename)
    engine_str = 'mysql://{u}:{p}@{h}{port}/{b_name}?charset=utf8&use_unicode=0'.format(
        u=user,
        p=password,
        h=host,
        port='' if port is None else ':' + str(port),
        b_name=bname
    )
    engine = create_engine(engine_str, convert_unicode=True, echo=False)
    return engine


class Mantis_project_check_table(Base):
    __tablename__ = 'mantis_project_check_table'

    id = Column('id', Integer, ForeignKey('mantis_project_table.id'), primary_key=True, nullable=False)
    need = Column('need', Integer)
    user = Column('user', Integer, ForeignKey('mantis_user_table.id'))
    time = Column('time', Integer)

    def __repr__(self):
        return "<mantis_project_check_table({},{},{},{})>".format(self.id, self.need, self.user, self.time)

class Mantis_project_table(Base):
    __tablename__ = 'mantis_project_table'

    id = Column('id', Integer, ForeignKey('mantis_project_check_table.id'), primary_key=True, nullable=False,
                autoincrement=True)
    name = Column('name', String(128), ForeignKey('cb_data42.f435'))
    status = Column('status', Integer)
    enabled = Column('enabled', Integer)
    view_state = Column('view_state', Integer)
    access_min = Column('access_min', Integer)
    file_path = Column('file_path', String(250))
    description = Column('description', String)
    category_id = Column('category_id', Integer)
    inherit_global = Column('inherit_global', Integer)
    priority = Column('priority', Integer)
    network_id = Column('network_id', Integer)

    def __repr__(self):
        return ("<mantis_project_table({},{},{},{},{},{},{},{},{},{},{},{})>".format
            (
            self.id,
            self.name,
            self.status,
            self.enabled,
            self.view_state,
            self.access_min,
            self.file_path,
            self.description,
            self.category_id,
            self.inherit_global,
            self.priority,
            self.network_id
        ))


class Mantis_user_table(Base):
    __tablename__ = 'mantis_user_table'

    id = Column('id', Integer, ForeignKey('mantis_project_check_table.user'), primary_key=True, nullable=False,
                autoincrement=True)
    username = Column('username', String(32))
    realname = Column('realname', String(64))
    email = Column('email', String(64), ForeignKey('cb_user.e_mail'))
    password = Column('password', String(32))
    enabled = Column('enabled', Integer)
    protected = Column('protected', Integer)
    access_level = Column('access_level', Integer)
    login_count = Column('login_count', Integer)
    lost_password_request_count = Column('lost_password_request_count', Integer)
    failed_login_count = Column('failed_login_count', Integer)
    cookie_string = Column('cookie_string', String(64))
    last_visit = Column('last_visit', Integer)
    date_created = Column('date_created', Integer)

    def __repr__(self):
        return ("<mantis_project_table({},{},{},{},{},{},{},{},{},{},{},{},{},{})>".format
            (
            self.id,
            self.username,
            self.realname,
            self.email,
            self.password,
            self.enabled,
            self.protected,
            self.access_level,
            self.login_count,
            self.lost_password_request_count,
            self.failed_login_count,
            self.cookie_string,
            self.last_visit,
            self.date_created
        ))


class Cb_data42(Base):
    __tablename__ = 'cb_data42'

    id = Column('id', Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column('user_id', Integer)
    add_time = Column('add_time', TIMESTAMP)
    status = Column('status', Integer)
    f435 = Column('f435', String(255), ForeignKey('mantis_project_table.name'))  # Name
    f438 = Column('f438', Integer)  # -hz
    f439 = Column('f439', String(255))  # description
    f440 = Column('f440', String(255))  # address
    f441 = Column('f441', String(255))  # telphone
    f442 = Column('f442', String(255))  # email
    f443 = Column('f443', Integer)  # -hz
    f444 = Column('f444', String)  # www.site
    f445 = Column('f445', String)  # company way description/ additional information
    f446 = Column('f446', String(255))  # -EMPTY
    f552 = Column('f552', String(43))  # company typo (Подрядчик/Поставщик оборудования)
    f770 = Column('f770', String(255))  # type of service description/ short info
    f772 = Column('f772', String(35))  # type of service (ГТИ/ЗТС)
    f884 = Column('f884', String(255))  # -EMPTY
    f895 = Column('f895', Integer)  # -hz
    f1040 = Column('f1047', String(255))  # mail index + address
    f1056 = Column('f1056', String(255))  # INN ?
    f1057 = Column('f1057', String(255))  # -hz
    f1058 = Column('f1058', String(255))  # bank account
    f1059 = Column('f1059', String(255))  # bank account too ?
    f1060 = Column('f1060', String(255))  # bank comment
    f1061 = Column('f1061', String(255))  # -hz
    f1062 = Column('f1062', String(255))  # some names (who cares??)
    f1063 = Column('f1063', String(255))  # same names
    f1064 = Column('f1064', String)  # -hz
    f1065 = Column('f1065', String(255))  # bank name
    f1088 = Column('f1088', Integer)  # -hz
    f1089 = Column('f1089', String(6))  # -hz (boolean)
    f1460 = Column('f1460', Integer)  # -hz
    f1470 = Column('f1470', String(255))  # -EMPTY
    f1480 = Column('f1480', Integer)  # -hz
    f3441 = Column('f3441', String(255))  # short name / shortcut
    f4271 = Column('f4271', String)  # some files (contracts)
    f4620 = Column('f4620', String)  # other docs
    f5090 = Column('f5090', String)  # logo jpg
    f5970 = Column('f5970', String)  # address again
    f6410 = Column('f6410', Integer)  # -hz
    f8340 = Column('f8340', DECIMAL(10, 0))  # -hz
    f8360 = Column('f8360', TIMESTAMP)  # date of last Hand check
    f8650 = Column('f8650', Integer)  # -hz
    f8690 = Column('f8690', String)  # -hz some official doc BKE
    f8700 = Column('f8700', String)  # -hz continue doc
    f10760 = Column('f10760', Integer)  # -hz
    f10910 = Column('f10910', String)  # HTML + CSS code of main paige with ref's
    f10930 = Column('f10930', String)  # doc's again
    f10940 = Column('f10940', String)  # -EMPTY
    f13120 = Column('f13120', String(255))  # name of charge
    f13130 = Column('f13130', String(255))  # charge position (director)
    f14050 = Column('f14050', String)  # TP ref's
    r = Column('r', Integer)  # -hz
    u = Column('u', Integer)  # -hz
    uniq_qst = Column('uniq_qst', String(255))  # -hz


class Cb_users(Base):
    __tablename__ = 'cb_users'

    id = Column('id', Integer, primary_key=True, nullable=False, autoincrement=True)
    fio = Column('fio', String(255))
    e_mail = Column('e_mail', String(255), ForeignKey('mantis_user_table.email'))
    phone = Column('phone', String(255))
    login = Column('login', String(255))
    paswword = Column('password', String)
    code = Column('code', String(255))
    date_registr = Column('date_registr', DateTime)
    arc = Column('arc', Integer)
    group_id = Column('group_id', Integer)
    lang = Column('lang', String(30))
    time_zone = Column('time_zone', String(255))
    window_scroll = Column('window_scroll', Integer)
    default_page = Column('default_page', String(30))
    developer_mode = Column('developer_mode', Integer)
    user_hash = Column('user_hash', String(255))
    last_time = Column('last_time', DateTime)
    last_event = Column('last_event', DateTime)
    last_ip = Column('last_ip', String(255))
    ot_key = Column('ot_key', String)
    crypt_mode = Column('crypt_mode', String(255))
    t = Column('t', Integer)
    sound_on = Column('sound_on', Integer)
    cut_notify_text = Column('cut_notify_text', Integer)
    oktell_login = Column('oktell_login', String(255))
    oktell_password = Column('oktell_password', String(255))
    oktell_use_handsfree = Column('oktell_use_handsfree', Integer)
    asterisk_login = Column('asterisk_login', String(255))
    asterisk_password = Column('asterisk_password', String(255))
    asterisk_use_handsfree = Column('asterisk_use_handsfree', Integer)
    asterisk_number = Column('asterisk_number', String(255))
    display_notification_on = Column('display_notification_on', Integer)

