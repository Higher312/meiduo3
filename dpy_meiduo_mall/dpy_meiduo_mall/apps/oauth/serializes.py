from rest_framework import serializers
from django_redis import get_redis_connection

from .utils import check_save_user_token
from users.models import User
from oauth.models import OAuthQQUser


class QQAuthUserSerialize(serializers.Serializer):
    """QQ登录创建用户序列化器"""

    # 1.定义需要序列化或反序列化的字段
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    # 2.校验
    def validate(self, data):
        """校验"""

        """1.获取openid"""
        # 取出加密的openid
        openid_token = data.get('access_token')
        # 把openid还原
        openid = check_save_user_token(openid_token)

        if not openid:
            # access_token即存储的openid有过期时间
            raise serializers.ValidationError('access_token无效')

        # 把解密后的openid存入反序列化的大字典中后续保存时使用
        data['openid'] = openid

        """2.获取redis中短信验证码和用户输入的做判断"""
        # 获取前端传过来的短信信息
        sms_code = data.get('sms_code')
        redis_conn = get_redis_connection('verify_code')
        real_sms_code = redis_conn.get('sms_%s' % data.get('mobile'))
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('sms_code错误')

        """3.用手机号去查询用户是否存在"""
        mobile = data.get('mobile')
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:

            # 手机号不存在,说明是一个新用户
            pass

        else:
            # 不走except则走else,说明手机号已经注册过美多商城,直接验证密码
            if not user.check_password(data.get('password')):
                raise serializers.ValidationError('密码不正确')
            else:
                # 把用户直接加入到反序列化的大字典中,以备后用
                data['user'] = user

        return data

    # 3.保存,重写create方法
    def create(self, validated_data):

        # 从validatea_data来获取user,若有值,说明当前用户是已经注册,直接和openid绑定
        user = validated_data.get('user')

        if not user:
            # 若user没有值,创建新用户
            user = User.objects.create(
                username = validated_data['mobile'],
                # password = validated_data['password'],
                mobile = validated_data['mobile']
            )
            # 存储密码加密
            user.set_password(validated_data['password'])
            user.save()

        # 将用户与openid绑定
        OAuthQQUser.objects.create(
            openid = validated_data['openid'],
            user = user
        )
        # 返回用户数据
        return user