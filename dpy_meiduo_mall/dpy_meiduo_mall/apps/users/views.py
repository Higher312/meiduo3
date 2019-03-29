from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView,RetrieveAPIView,UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin,UpdateModelMixin
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken

from .models import User, Address
from .serializers import UserModelSerializer,UserDetailSerializer,\
    EmailSerializer,UserAddressSerializer,AddressTitleSerializer,\
    UserBrowseHistorySeializer
from . import constants
from goods.models import SKU
from goods.serializers import SKUListSerializer
from carts.utils import merge_cart_cookie_to_redis
# Create your views here.


class UserAuthorizeView(ObtainJSONWebToken):
    """用户登录认证类重写"""

    def post(self, request, *args, **kwargs):
        """重写登陆的post方法然后super继承"""

        response = super(UserAuthorizeView, self).post(request, *args, **kwargs)

        # 重写登录的认证类视图就是为了做合并购物车
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user

            return merge_cart_cookie_to_redis(request,user,response)


class UserBrowseHistoryView(CreateAPIView):
    """"""

    # 指定序列化器
    serializer_class = UserBrowseHistorySeializer

    # 指定权限
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """查询用户浏览记录"""

        # 从redis中取出当前登录用户的浏览记录redis数据
        redis_conn = get_redis_connection("history")
        sku_ids = redis_conn.lrange('history_%s' % request.user.id,0,-1)

        # 用来保存sku模型
        sku_list = []

        # 把一个一个的sku_id对应的sku模型取出来
        for sku_id in sku_ids:
            sku_model = SKU.objects.get(id=sku_id)
            sku_list.append(sku_model)

        # 进行序列化输出
        serializer = SKUListSerializer(sku_list,many=True)

        return Response(serializer.data)


class AddressViewSet(CreateModelMixin,UpdateModelMixin,GenericViewSet):
    """收货地址"""

    # 1.指定序列化器
    serializer_class = UserAddressSerializer

    # 2.指定权限
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

    def create(self,request,*args,**kwargs):
        """新增收货地址"""

        # count = Address.objects.filter(user_id = request.user.id).count()
        count = request.user.addresses.count()

        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message':'用户收货地址已经超过上限'},status=status.HTTP_400_BAD_REQUEST)

        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(serializer.data,status=status.HTTP_201_CREATED)

        return super(AddressViewSet, self).create(request,*args,**kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VerifyEmailView(UpdateAPIView):
    """验证(激活)邮箱"""

    def get(self,request):

        # 1.提取token查询字符串数据
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)

        # 2.解密token,根据token获取当前用户对象user
        user = User.check_email_verify_url(token)
        if not user:
            return Response({'message':'无效的token'},status=status.HTTP_400_BAD_REQUEST)

        # 3.修改email_active字段显示信息并进行反序列化输入
        user.email_active = True
        user.save()

        # 4.响应数据
        return Response({'message':'OK'})


class EmailView(UpdateAPIView):
    """保存邮箱和发送邮件"""

    # 1.指定序列化器
    serializer_class = EmailSerializer

    # 2.指定权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """重写查询单一方法,返回本次请求的用户"""

        return self.request.user


class UserDetailView(RetrieveAPIView):
    """查询用户个人信息"""

    # 1.指定序列化器
    serializer_class = UserDetailSerializer

    # 2.指定权限
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """重写查询单一方法,返回本次请求的用户"""

        return self.request.user


class UserView(CreateAPIView):
    """用户注册视图逻辑"""

    # 指定序列化器
    serializer_class = UserModelSerializer


class UsernameCountView(APIView):
    """判断用户名是否已存在"""

    def get(self,request,username):
        """查询用户名接口实现"""

        # 拿前端传过来的用户名去查询数据,如果用户已存在count是1,不存在是0
        count = User.objects.filter(username=username).count()
        data = {
            "username":username,
            "count":count
        }
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否注册"""

    def get(self,request,mobile):
        """查询手机号接口实现"""

        count = User.objects.filter(mobile=mobile).count()
        data = {
            "mobile":mobile,
            "count":count
        }
        return Response(data=data)