from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJSSerializer,BadData
from django.conf import settings

from dpy_meiduo_mall.utils.models import BaseModel
from . import constants

# Create your models here.


class User(AbstractUser):
    """自定义用户模型类:默认字段不全"""

    mobile = models.CharField(max_length=11,unique=True,verbose_name="手机号")
    email_active = models.BooleanField(default=False,verbose_name='邮箱激活状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_email_verify_url(self):
        """生成激活url"""

        # 1.创建加密的序列化器对象,并设置过期时间
        serializer = TJSSerializer(settings.SECRET_KEY,constants.VERIFY_EMAIL_TOKEN_EXPIRS)

        # 2.构造要加密的数据
        data = {'user_id':self.id,'email':self.email}

        # 3.加密并编码成字符串
        token = serializer.dumps(data).decode()
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token='+token

        # 响应邮件验证链接
        return verify_url

    @staticmethod
    def check_email_verify_url(token):
        """解密并获取user对象"""

        # 1.创建并加密序列化器对象
        serializer = TJSSerializer(settings.SECRET_KEY,constants.VERIFY_EMAIL_TOKEN_EXPIRS)

        # 2.解密token
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        # 不走except则走else
        else:
            user_id = data.get('user_id')
            email = data.get('email')
            # 联合查询,获取用户对象,防止信息被修改
            try:
                user = User.objects.get(id=user_id,email=email)
            except User.DoesNotExist:
                return None
            else:
                # 返回用户对象,供后续邮箱状态反序列化输入
                return user


class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']