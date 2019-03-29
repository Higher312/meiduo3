from django_redis import get_redis_connection
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
import re
from rest_framework_jwt.settings import api_settings

from .models import User,Address
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU


class UserBrowseHistorySeializer(serializers.Serializer):
    """保存浏览记录的序列化器"""

    sku_id = serializers.IntegerField(label='sku商品id',min_value=1)

    def validate_sku_id(self,value):
        """额外给sku_id追加校验,校验是否有效"""

        try:
            SKU.objects.get(id=value)

        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id不存在')

        return value

    def create(self, validated_data):
        """存浏览记录到redis中"""

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        sku_id = validated_data.get('sku_id')

        # 获取当前的登录用户
        user = self.context['request'].user

        # 创建redis管道对象
        pl = redis_conn.pipeline()

        # 保存sku_id之前先去重
        # redis_conn.lrem('history_%s' % sku_id)
        pl.lrem('history_%s' % user.id ,0,sku_id)

        # 保存新的sku_id到列表的最前面
        # redis_conn.lpush('history_%s' % user.id,sku_id)
        pl.lpush('history_%s' % user.id,sku_id)

        # 截取前5个
        # redis_conn.ltrim('history_%s' % user.id,0,4)
        pl.ltrim('history_%s' % user.id,0,4)

        # 执行管道
        pl.execute()

        # 返回
        return validated_data


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """保存用户地址"""
        
        user = self.context['request'].user
        validated_data['user'] = user
        
        # return Address.object.create(**validated_data)
        return super(UserAddressSerializer, self).create(validated_data)
        
        
class EmailSerializer(serializers.ModelSerializer):
    """邮箱序列化器"""

    class Meta:
        model = User
        fields = ['id','email']
        # 添加额外必传字段
        extra_kwargs = {
            'email':{
                'required':True
            }
        }

    def update(self, instance, validated_data):
        """反序列化输入保存邮箱字段"""

        # 从反序列化校验完成的字典中取出email赋值给当前模型对象的email属性
        instance.email = validated_data['email']
        instance.save()

        # 获取发送邮件验证链接
        verify_url = instance.generate_email_verify_url()
        # 发送验证邮件
        send_verify_email.delay(instance.email,verify_url)

        # 响应当前模型数据
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """用户个人信息"""

    class Meta:
        model = User

        fields = ['id','username','mobile','email','email_active']


# 有模型，可以映射需要字段，选择继承ModelSerialize;
class UserModelSerializer(ModelSerializer):
    """创建用户序列化器"""

    # 缺少所需字段,重写序列化器字段
    # 字段默认双向，write_onle只做输入（反序列化）
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    # 多加一个输出字段
    token = serializers.CharField(label='token',read_only=True)

    class Meta:
        # 从哪个模型映射字段
        model = User
        """
        模型中存在的字段:id,username,password,mobile
        输出字段(序列化):id,username,mobile
        输入字段(反序列化):username,password,password2,mobile,sms_code,allow
        双向字段：usename,moblie
        """
        # 需要映射哪些字段
        fields = ['id','username','password','password2','mobile','sms_code','allow','token']

        # 重写映射过来的字段设置
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    # 手机号单独校验
    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    # 用户是否同意协议单独校验
    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    # 密码比对联合校验
    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_code')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        重写序列化器的存储方法,把password2,sms_code,allow数据从validated_date字典依次
        """
        # del字典[键]：删除指定的键值
        # 字典.pop(键)：删除指定键值，返回被删除的值（唯一返回）
        # 移除数据库模型类中不存在的属性
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # user = User.objects.create(**validated_data)
        # user = super().create(validated_data)
        # 创建user模型对象
        # **字典,解开字典,以关键字形式
        user = User(**validated_data)

        # 调用django的认证系统加密密码
        # 对要存储的密码进行加密处理
        user.set_password(validated_data['password'])
        user.save()

        # 加载jwt配置中处理payload的函数
        """
        'JWT_PAYLOAD_HANDLER':
        'rest_framework_jwt.utils.jwt_payload_handler',
        存的是导包路径(配置项,表示可以修改)
        """
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        # 加载生成token的函数
        """
        key = api_settings.JWT_PRIVATE_KEY or jwt_get_secret_key(payload)
        return jwt.encode(
            payload,
            key,
            api_settings.JWT_ALGORITHM
        ).decode('utf-8')
        """
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 传入用户对象user生成载荷payload
        payload = jwt_payload_handler(user)
        # 传入载荷,加上头部信息和盐,生成token
        token = jwt_encode_handler(payload)

        # 把jwt token和用户id,用户名(username)一起响应出去
        user.token = token

        return user