from django.contrib.auth.backends import ModelBackend
import re

from .models import User


def jwt_response_payload_handler(token,user=None,request=None):
    """重写jwt响应成功的返回数据方法"""

    return {
        'token':token,
        'user_id':user.id,
        'username':user.username
    }


def get_user_by_account(account):
    """动态根据accout来查找用户"""

    try:
        # 若正则匹配成功就是手机号登陆
        if re.match('^1[3-9]\d{9}$',account):
            user = User.objects.get(mobile=account)

        # 否则是用户名登陆
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    else:
        # 返回查询到的user
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义django用户认证类来使用多账号登陆"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """根据username或mobile查找user对象,校验密码是否正确,返回user"""

        # 1.根据用户名或手机号获取user对象
        user = get_user_by_account(username)

        # 2.校验密码是否正确
        if user and user.check_password(password):
            return user