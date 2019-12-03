# -*- coding: utf-8 -*-

import time
import MySQLdb
from core import db
from core import sentry


__all__ = [
    "load_supplier_history_data",
    "load_transporter_history_data",
]


def _get_conn(bind_key):
    origin_engine = db.get_engine(bind=bind_key)
    engine = db.create_engine(origin_engine.url)
    sqlalchemy_conn = engine.raw_connection()
    conn = sqlalchemy_conn.connection
    conn.autocommit(False)
    return conn


def load_supplier_history_data(batch_size=2000):
    conn_get = _get_conn('dw_api_db')
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = _get_conn('saaty_db')
    cursor_set = conn_set.cursor()

    select_sql = 'select * from api_algo_supplier_delivery_history'  # dw_api_db是 api_前缀
    cursor_get.execute(select_sql)
    i = 0
    while True:
        rows = cursor_get.fetchmany(batch_size)
        if not rows:
            if 0 == i:
                sentry.captureException()
            break

        i += 1
        format_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for row in rows:
            row['update_time'] = format_time

        cursor_set.executemany(insert_sql_supplier_history_data, rows)
        conn_set.commit()

    cursor_get.close()
    cursor_set.close()
    conn_get.close()
    conn_set.close()


def load_transporter_history_data(batch_size=2000):
    conn_get = _get_conn('dw_api_db')
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = _get_conn('saaty_db')
    cursor_set = conn_set.cursor()

    select_sql = 'select * from api_algo_transporter_delivery_history'
    cursor_get.execute(select_sql)
    i = 0
    while True:
        rows = cursor_get.fetchmany(batch_size)
        if not rows:
            if 0 == i:
                sentry.captureException()
            break

        i += 1
        format_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for row in rows:
            row['update_time'] = format_time

        cursor_set.executemany(insert_sql_transporter_history_data, rows)
        conn_set.commit()

    cursor_get.close()
    cursor_set.close()
    conn_get.close()
    conn_set.close()


insert_sql_transporter_history_data = '''
insert into algo_transporter_delivery_history 
                                (transporter_id, 
                                history_order_num, 
                                avg_a1_time, 
                                avg_a2_time, 
                                city_id,
                                create_time, 
                                update_time) VALUES  
                                (%(transporter_id)s, 
                                %(history_order_num)s, 
                                %(avg_a1_time)s,
                                %(avg_a2_time)s, 
                                %(city_id)s,
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                transporter_id = VALUES (transporter_id), 
                                history_order_num = VALUES (history_order_num), 
                                avg_a1_time = VALUES (avg_a1_time), 
                                avg_a2_time = VALUES  (avg_a2_time), 
                                city_id = VALUES (city_id),
                                update_time = VALUES (update_time)
                                '''

insert_sql_supplier_history_data = '''
insert into algo_supplier_delivery_history 
                                (supplier_id, 
                                history_order_num, 
                                avg_a1_time, 
                                avg_a2_time, 
                                city_id,
                                create_time, 
                                update_time) VALUES  
                                (%(supplier_id)s, 
                                %(history_order_num)s, 
                                %(avg_a1_time)s,
                                %(avg_a2_time)s, 
                                %(city_id)s,
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                supplier_id = VALUES (supplier_id), 
                                history_order_num = VALUES (history_order_num), 
                                avg_a1_time = VALUES (avg_a1_time), 
                                avg_a2_time = VALUES  (avg_a2_time), 
                                city_id = VALUES (city_id),
                                update_time = VALUES (update_time)
                                '''
