from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from random import randint
import logging
from django_redis import get_redis_connection
from dpy_meiduo_mall.libs.yuntongxun.sms import CCP
from rest_framework.response import Response
from celery_tasks.sms.tasks import send_sms_code

from . import constants
# Create your views here.

# 创建日志输出器对象
logger = logging.getLogger('django')


class SMSCodeView(APIView):
    """发送短信验证码"""

    def get(self,request,mobile):
        """GET请求接收路径参数mobile"""

        # 1.创建redis连接对象
        redis_conn = get_redis_connection('verify_code')

        # 先从redis中取出发送短信标记
        flag = redis_conn.get('sms_flag_%s' % mobile)
        # 只要if为真,说明当前号码60秒内发送过短信
        if flag:
            return Response({'message':'频繁发送短信'},status=status.HTTP_400_BAD_REQUEST)

        # 2.生成验证码
        sms_code = '%06d'%randint(0,999999)

        # 输出日志信息
        logger.info(sms_code)

        # 创建redis管道 : 利用管道让多条redis命令一次执行
        pl = redis_conn.pipeline()

        # # 3.把验证码存储到redis
        # # redis_conn.setex(key,过期时间,value)
        # redis_conn.setex('sms_%s' % mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)

        pl.setex('sms_%s' % mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)

        # # 存储一个已经发送过短信验证码的标识到redis
        # redis_conn.setex('sms_flag_%s' % mobile,constants.SEND_SMS_CODE_INTERVAL,1)

        pl.setex('sms_flag_%s' % mobile,constants.SEND_SMS_CODE_INTERVAL,1)

        # 执行管道(执行管道时,才会把管道中的多个redis命令一次全部执行)
        pl.execute()

        # # 4.使用容连云通讯发送短信验证码
        # CCP().send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES//60],1)

        send_sms_code.delay(mobile,sms_code)


        # 5.响应
        return Response({'message','OK'})