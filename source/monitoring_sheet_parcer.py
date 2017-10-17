#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import os
import httplib2
from apiclient import discovery
from datetime import datetime, timedelta

import source
from calendar_parcer import get_credentials


SCOPES = source.SECURE['scopes'].get('sheet')
CLIENT_SECRET_FILE = source.CLIENT_SECRET_FILE
SHEET_ID = '1TtPEa9F4Hlw1gb6LHIaKkILOCFdFtAZj5C7YBdyWS4M'


def parse_from_google():
    d = {}
    credentials = get_credentials(SCOPES, 'sheets.googleapis.com-python.json')
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = SHEET_ID
    rangeHeadTable = 'A3:S41'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeHeadTable).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
    else:
        for row in values:
            row_len_max = 19
            while len(row) < row_len_max:
                row.append(None)
            mysql_rows = {"port on gate": row[7], "login": row[8], "password": row[9], "database": row[10]}
            table_dict = {"Сервак": row[0],
                          "network": row[1],
                          "name": row[2],
                          "vpn": row[3],
                          "dns name/server/cred": row[4],
                          "auth": row[5],
                          "URL": row[6],
                          "mysql": mysql_rows,
                          "monitoring": row[11],
                          "v": row[12],
                          "adminka": row[13],
                          "witsml": row[14],
                          "клиентский dashboard": row[15],
                          "GBOX ssh": row[16],
                          "reporting": row[17],
                          "Itillium": row[18]
                          }
            d[table_dict['name']] = table_dict

    source.write_json(source.MOT_TABLE, d, 3)
    # with codecs.open(MOT_TABLE, 'w', encoding='utf-8') as fd:
    #     fd.write(json.dumps(d, ensure_ascii=False))
    return d


def parse_sheet():
    if not os.access(source.MOT_TABLE, os.F_OK):
        return parse_from_google()

    ctf = os.stat(source.MOT_TABLE).st_ctime  # time of last update file
    last_update = datetime.fromtimestamp(ctf)  # string time format
    now = datetime.now()
    dif = now - last_update
    delta = timedelta(days=30)

    if dif > delta:
        os.remove(source.MOT_TABLE)
        return parse_from_google()

    return source.read_json(source.MOT_TABLE)


def main():
    print(parse_sheet())


if __name__ == '__main__':
    main()
