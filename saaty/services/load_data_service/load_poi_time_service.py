# -*- coding: utf-8 -*-

import urlparse
import MySQLdb
import time
from core import app
from core import sentry

__all__ = [
    "load_poi_time_supplier_data",

]

CONN_DICT = dict()


def get_conn(conn_str):
    conn = CONN_DICT.get(conn_str)
    try:
        conn.ping()
    except:
        url = urlparse.urlparse(conn_str)
        conn = MySQLdb.connect(host=url.hostname, user=url.username,
                               passwd=url.password,
                               db=url.path[1:],
                               port=url.port if url.port else 3306,
                               charset='utf8', use_unicode=True)
        conn.autocommit(False)
        CONN_DICT[conn_str] = conn
    return conn


def load_poi_time_supplier_data(batch_size=2000):
    conn_get = get_conn(app.config['SQLALCHEMY_BINDS']['dw_api_db'])
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = get_conn(app.config['SQLALCHEMY_BINDS']['saaty'])
    cursor_set = conn_set.cursor()

    select_sql = 'select * from poi_supplier_time_difficulty'
    cursor_get.execute(select_sql)
    print("start load_poi_time_supplier_data ")
    i = 0
    while True:
        rows = cursor_get.fetchmany(batch_size)
        if not rows:
            if 0 == i:
                print('dw_api.poi_supplier_time_difficulty data error!')
                sentry.captureException()
            break

        i += 1
        format_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for row in rows:
            row['update_time'] = format_time

        print('length rows = ', len(rows))
        cursor_set.executemany(insert_sql_pickup_time_difficulty, rows)
        conn_set.commit()

    cursor_get.close()
    cursor_set.close()
    conn_get.close()
    conn_set.close()

    print("complete load_poi_time_supplier_data")


insert_sql_receiver_time_difficulty = '''insert into 
poi_supplier_time_difficulty (receiver_lng, 
                                receiver_lat, 
                                city_id, 
                                poi_value, 
                                create_time, 
                                update_time) VALUES  
                                (%(supplier_id)s, 
                                %(supplier_lng)s, 
                                %(supplier_lat)s,
                                %(city_id)s, 
                                %(poi_value)s, 
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                receiver_lng = VALUES (receiver_lng), 
                                receiver_lat = VALUES (receiver_lat), 
                                city_id = VALUES  (city_id), 
                                poi_value = VALUES (poi_value), 
                                create_time = VALUES (create_time), 
                                update_time = VALUES (update_time)'''



insert_sql_pickup_time_difficulty = '''insert into poi_supplier_time_difficulty 
                                (supplier_id, 
                                supplier_lng, 
                                supplier_lat, 
                                city_id, 
                                poi_value, 
                                create_time, 
                                update_time) VALUES  
                                (%(supplier_id)s, 
                                %(supplier_lng)s, 
                                %(supplier_lat)s,
                                %(city_id)s, 
                                %(poi_value)s, 
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                supplier_id = VALUES (supplier_id), 
                                supplier_lng = VALUES (supplier_lng), 
                                supplier_lat = VALUES (supplier_lat), 
                                city_id = VALUES  (city_id), 
                                poi_value = VALUES (poi_value), 
                                create_time = VALUES (create_time), 
                                update_time = VALUES (update_time)'''

