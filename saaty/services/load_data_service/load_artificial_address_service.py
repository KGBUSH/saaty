# -*- coding: utf-8 -*-

"""

@author: zhenfengjiang

@contact: zhenfengjiang@imdada.cn

@file: load_artificial_address_service.py

@time: 2019/9/6 14:24

@desc:

"""

import time
import MySQLdb
from core import db
from core import sentry


def _get_conn(bind_key):
    origin_engine = db.get_engine(bind=bind_key)
    engine = db.create_engine(origin_engine.url)
    sqlalchemy_conn = engine.raw_connection()
    conn = sqlalchemy_conn.connection
    conn.autocommit(False)
    return conn


def load_artificial_address_data(batch_size=2000):
    conn_get = _get_conn('dw_api_db')
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = _get_conn('saaty_db')
    cursor_set = conn_set.cursor()

    select_sql = 'select * from artificial_difficult_address'
    cursor_get.execute(select_sql)
    print("start artificial_difficult_address ")
    i = 0
    while True:
        rows = cursor_get.fetchmany(batch_size)
        if not rows:
            if 0 == i:
                print('dw_api.artificial_difficult_address data error!')
                sentry.captureException()
            break

        i += 1
        format_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for row in rows:
            row['update_time'] = format_time

        print('length rows = ', len(rows))
        cursor_set.executemany(insert_sql_artificial_difficult_address, rows)
        conn_set.commit()

    cursor_get.close()
    cursor_set.close()
    conn_get.close()
    conn_set.close()

    print("complete artificial_difficult_address")


insert_sql_artificial_difficult_address = '''
insert into artificial_difficult_address 
                                (lng,
                                lat, 
                                address, 
                                geohash, 
                                create_time, 
                                update_time,
                                is_del) VALUES  
                                (%(lng)s, 
                                %(lat)s,
                                %(address)s, 
                                %(geohash)s, 
                                %(create_time)s, 
                                %(update_time)s,
                                %(is_del)s 
                                ) ON duplicate KEY UPDATE  
                                lng = VALUES (lng), 
                                lat = VALUES (lat), 
                                address = VALUES  (address), 
                                geohash = VALUES (geohash), 
                                create_time = VALUES (create_time), 
                                update_time = VALUES (update_time),
                                is_del = VALUES (is_del)
                                '''
