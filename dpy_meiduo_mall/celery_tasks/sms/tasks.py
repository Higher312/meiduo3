"""编写异步任务的代码"""
from .yuntongxun.sms import CCP
from . import constants
from celery_tasks.main import celery_app


# 把下面的函数装饰为celery的任务
# name参数给任务起别名
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile,sms_code):
    """
    发短信的异步任务
    :param mobile: 手机号
    :param sms_code: 验证码
    :return:
    """

    # 4.使用容连云通讯发送短信验证码
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)