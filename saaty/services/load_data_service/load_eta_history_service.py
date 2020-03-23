# -*- coding: utf-8 -*-

import time
import MySQLdb
from core import db
from core import sentry


__all__ = [
    "load_supplier_history_data",
    "load_transporter_history_data",
    "load_poi_statistics_data",
    "load_transporter_peak_data"
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



def load_poi_statistics_data(batch_size=2000):
    conn_get = _get_conn('dw_api_db')
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = _get_conn('saaty_db')
    cursor_set = conn_set.cursor()

    select_sql = 'select * from api_algo_poi_statistic_Info'
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

        cursor_set.executemany(insert_sql_poi_statistic_data, rows)
        conn_set.commit()

    cursor_get.close()
    cursor_set.close()
    conn_get.close()
    conn_set.close()



def load_transporter_peak_data(batch_size=2000):
    conn_get = _get_conn('dw_api_db')
    cursor_get = conn_get.cursor(MySQLdb.cursors.SSDictCursor)

    conn_set = _get_conn('saaty_db')
    cursor_set = conn_set.cursor()

    select_sql = 'select * from api_algo_transporter_delivery_peek_Info'
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

        cursor_set.executemany(insert_sql_transporter_delivery_peek_data, rows)
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


insert_sql_poi_statistic_data = '''
insert into algo_poi_statistic_Info 
                                (poi_id, 
                                percentile_delivery_time_poi, 
                                avg_delivery_time_poi, 
                                percentile_distance_poi, 
                                std_distance_poi,
                                std_delivery_time_poi,
                                order_cnt,
                                city_id,
                                poi_lat,
                                poi_lng,
                                create_time, 
                                update_time) VALUES  
                                (%(poi_id)s, 
                                %(percentile_delivery_time_poi)s, 
                                %(avg_delivery_time_poi)s,
                                %(percentile_distance_poi)s, 
                                %(std_distance_poi)s, 
                                %(std_delivery_time_poi)s, 
                                %(order_cnt)s, 
                                %(city_id)s,
                                %(poi_lat)s,
                                %(poi_lng)s,
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                poi_id = VALUES (poi_id), 
                                percentile_delivery_time_poi = VALUES (percentile_delivery_time_poi), 
                                avg_delivery_time_poi = VALUES (avg_delivery_time_poi), 
                                percentile_distance_poi = VALUES  (percentile_distance_poi), 
                                std_distance_poi = VALUES  (std_distance_poi), 
                                std_delivery_time_poi = VALUES  (std_delivery_time_poi), 
                                order_cnt = VALUES  (order_cnt), 
                                city_id = VALUES (city_id),
                                poi_lat = VALUES (poi_lat),
                                poi_lng = VALUES (poi_lng),
                                update_time = VALUES (update_time)
                                '''



insert_sql_transporter_delivery_peek_data = '''
insert into algo_transporter_delivery_peek_Info 
                                (transporter_id, 
                                city_id, 
                                delivery_cnt, 
                                
                                avg_delivery_time2, 
                                 
                                per_delivery_time2,  
                                cnt_peek1,
                                cnt_peek2,
                                cnt_peek3,
                                cnt_peek0,
                                
                                per_delivery_time_peek1,
                                per_delivery_time_peek2,
                                per_delivery_time_peek3,
                                per_delivery_time_peek0,
                                create_time, 
                                update_time) VALUES  
                                (%(transporter_id)s, 
                                %(city_id)s, 
                                %(delivery_cnt)s,
                                
                                %(avg_delivery_time2)s, 
                               
                                %(per_delivery_time2)s, 
                                %(cnt_peek1)s, 
                                %(cnt_peek2)s, 
                                %(cnt_peek3)s, 
                                %(cnt_peek0)s,
                                
                                %(per_delivery_time_peek1)s,
                                %(per_delivery_time_peek2)s,
                                %(per_delivery_time_peek3)s,
                                %(per_delivery_time_peek0)s,
                                %(create_time)s, 
                                %(update_time)s 
                                ) ON duplicate KEY UPDATE  
                                transporter_id = VALUES (transporter_id), 
                                city_id = VALUES (city_id), 
                                delivery_cnt = VALUES (delivery_cnt), 
                                avg_delivery_time2 = VALUES  (avg_delivery_time2), 
                                per_delivery_time2 = VALUES  (per_delivery_time2), 
                                cnt_peek1 = VALUES  (cnt_peek1), 
                                cnt_peek2 = VALUES  (cnt_peek2), 
                                cnt_peek3 = VALUES  (cnt_peek3), 
                                cnt_peek0 = VALUES (cnt_peek0),
                                per_delivery_time_peek1 = VALUES (per_delivery_time_peek1),
                                per_delivery_time_peek2 = VALUES (per_delivery_time_peek2),
                                per_delivery_time_peek3 = VALUES (per_delivery_time_peek3),
                                per_delivery_time_peek0 = VALUES (per_delivery_time_peek0),
                                update_time = VALUES (update_time)
                                '''