from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from alipay import AliPay
from django.conf import settings
import os

from orders.models import OrderInfo
from .models import Payment


class PaymentView(APIView):
    """支付包接口"""

    # 指定权限
    permission_classes = [IsAuthenticated]

    def get(self,request,order_id):
        """生成支付宝支付url"""

        # 获取当前请求用户
        user = request.user

        # 1.校验订单

        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user,status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message':'订单有误'},status=status.HTTP_400_BAD_REQUEST)

        # 2.创建支付宝对象
        alipay = AliPay(
            appid = settings.ALIPAY_APPID,
            app_notify_url = None,  # 默认回调url
            app_private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'keys/app_private_key.pem'),
            alipay_public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'keys/alipy_public_key.pem'),
            sign_type = 'RSA2',
            debug = settings.ALIPAY_DEBUG
        )

        # 3.生成支付url后面的参数
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no = order_id,
            total_amount = str(order.total_amount),
            subject = '美多商城:%s' % order_id,
            return_url = 'http://www.meiduo.site:8080/pay_success.html',
        )

        # 4.拼接url + 参数
        alipay_url = settings.ALIPAY_URL + "?" + order_string

        # 5.响应支付url
        return Response({'alipay_url':alipay_url})


class PaymentStatusView(APIView):
    """"""

    def put(self,request):
        """修改订单状态及保存支付流水号"""

        # 提取查询字符串的数据
        query_dict = request.query_params
        data = query_dict.dict()    # 将query_dict转为python字典
        signature = data.pop('sign')     # 获取签证

        # 创建支付宝对象
        alipay = AliPay(
            appid = settings.ALIPAY_APPID,
            app_notify_url = None,  # 默认回调url
            app_private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'keys/app_private_key.pem'),
            alipay_public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'keys/alipy_public_key.pem'),
            sign_type = 'RSA2',
            debug = settings.ALIPAY_DEBUG
        )

        # 校验sign部分,校验是不是支付宝回给我们的支付成功状态
        success = alipay.verify(data,signature)
        if success:
            # 获取美多商城订单号
            order_id = data.get('out_trade_no')

            # 获取支付宝订单号
            trade_no = data.get('trade_no')

            # 存储支付宝及订单编号
            Payment.objects.create(
                order_id = order_id,
                trade_id = trade_no
            )

            # 修改订单的状态由待付款改为待发货
            OrderInfo.objects.filter(order_id=order_id,status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            # 响应支付宝订单编号
            return Response({'trade_id':trade_no})
        else:
            return Response({'message':'非法请求'},status=status.HTTP_403_FORBIDDEN)
