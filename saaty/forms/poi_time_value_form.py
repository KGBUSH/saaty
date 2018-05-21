# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import validators
from wtforms import ValidationError
from common.framework.forms.fields import ListField

__all__ = [
    "SupplierPickupTimeForm",
    "ReceiverTimeForm"
]


class SupplierPickupTimeForm(FlaskForm):
    error_messages = {
        'error_no_city': u'城市id为空',
        'error_no_lng': u'发货地经度为空',
        'error_no_lat': u'发货地纬度为空',
        'error_no_supplier_id': u'商户id为空'
    }

    supplierInfoList = ListField('待查询商户列表信息', validators=[
        validators.input_required(u'待查询商户列表信息为空'),
    ])

    def validate_supplierInfoList(self, field):
        supplier_info_list = field.data
        print(supplier_info_list)
        for supplier_info in supplier_info_list:
            if 'cityId' not in supplier_info:
                raise ValidationError(self.error_messages['error_no_city'])
            if 'supplierLng' not in supplier_info:
                raise ValidationError(self.error_messages['error_no_lng'])
            if 'supplierLat' not in supplier_info:
                raise ValidationError(self.error_messages['error_no_lat'])
            if 'supplierId' not in supplier_info:
                raise ValidationError(
                    self.error_messages['error_no_supplier_id'])


class ReceiverTimeForm(FlaskForm):
    error_messages = {
        'error_no_city': u'城市id为空',
        'error_no_lng': u'收货地经度为空',
        'error_no_lat': u'收货地纬度为空',
        'error_no_supplier_id': u'商户id为空'
    }
    receiverInfoList = ListField('收货地信息列表', validators=[
        validators.input_required(u'请求列表信息为空'),
    ])

    def validate_receiverInfoList(self, field):
        receiver_info_list = field.data
        for receiver_info in receiver_info_list:
            if 'cityId' not in receiver_info:
                raise ValidationError(self.error_messages['error_no_city'])
            if 'receiverLng' not in receiver_info:
                raise ValidationError(self.error_messages['error_no_lng'])
            if 'receiverLat' not in receiver_info:
                raise ValidationError(self.error_messages['error_no_lat'])
