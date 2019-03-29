from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from rest_framework import status
import logging
from rest_framework_jwt.settings import api_settings
from .utils import generate_save_user_token

from oauth.models import OAuthQQUser
from .serializes import QQAuthUserSerialize
from carts.utils import merge_cart_cookie_to_redis
# Create your views here.
# 创建日志输出器对象
logger = logging.getLogger('django')

# # 2.初始化OAuthQQ对象
# oauthqq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
#                   client_secret=settings.QQ_CLIENT_SECRET,
#                   redirect_uri=settings.QQ_REDIRECT_URI
#                   )


class QQAuthUserView(APIView):
    """用户扫码登录成功的回调函数"""

    def get(self,request):
        """完成oauth2.0认证"""

        # 1.提取code请求参数
        code = request.query_params.get('code')
        if not code:
            return Response({'message':'没有code'},status=status.HTTP_400_BAD_REQUEST)

        # 2.初始化OAuthQQ对象
        oauthqq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI
                          )

        try:
            # 3.利用code参数,使用get_access_token()方法,向QQ服务器发送get请求,获取access_token
            access_token = oauthqq.get_access_token(code)

            # 4.利用access_token参数,使用get_open_id()方法,向QQ服务器发送get请求,获取openid
            openid = oauthqq.get_open_id(access_token)
        except Exception as error:
            logger.info(error)
            return Response({'message':'QQ服务器异常'},status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 使用openid查询该QQ是否在美多商城中绑定过用户
        try:
            oauth_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:

            # 没有查到值,说明该openid没绑定美多商城用户,对
            # openid进行加密,响应给前端保存,后续创建新用户绑定使用
            access_token_openid = generate_save_user_token(openid)

            return Response({'access_token':access_token_openid})

        else:
            # 不走except,则走else,说明openid已经绑定美多商城用户
            # 生成JWT token,响应返回
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 获取oauthModel关联/绑定的用户模型对象
            # 查询到oauth_model有值,直接使用该用户
            user = oauth_model.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            # return Response({
            #     'user_id': user.id,
            #     'username': user.username,
            #     'token': token
            # })
            response = Response({
                'user_id': user.id,
                'username': user.username,
                'token': token
            })
            # 购物车合并
            return merge_cart_cookie_to_redis(request, user, response)

    def post(self,request):
        """openid绑定用户"""

        # 1.创建序列化器对象
        serializer = QQAuthUserSerialize(data=request.data)

        # 2.数据校验
        serializer.is_valid(raise_exception=True)

        # 3.保存
        user = serializer.save()

        # 生成JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 获取oauthModel关联/绑定的用户模型对象
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = Response({
            'use_id':user.id,
            'username':user.username,
            'token':token
        })

        # 购物车合并
        return merge_cart_cookie_to_redis(request,user,response)


class QQAuthURLView(APIView):
    """获取QQ登录扫码链接"""

    def get(self,request):
        """返回QQ扫码url"""

        # 1.获取next参数
        next = request.query_params['next']
        if not next:
            next = '/'

        # 2.初始化OAuthQQ对象
        oauthqq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                          client_secret=settings.QQ_CLIENT_SECRET,
                          redirect_uri=settings.QQ_REDIRECT_URI,
                          state=next)

        # 3.调用OAuthQQ中的oauthqq.get_qq_url()方法获取到拼接好的扫码url
        login_url = oauthqq.get_qq_url()

        # 4.响应
        return Response({'login_url':login_url})