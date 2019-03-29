from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    # 验证用户名是否已存在
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.UsernameCountView.as_view()),
    # 判断手机号是否已存在
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.MobileCountView.as_view()),
    # 注册功能
    url(r'^users/$',views.UserView.as_view()),
    # JWT登陆
    # url(r'^authorizations/$', obtain_jwt_token),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),
    # 查询用户个人信息
    url(r'^user/$', views.UserDetailView.as_view()),
    # 保存用户邮箱
    url(r'^email/$', views.EmailView.as_view()),
    # 验证邮箱
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),

    # 保存用户浏览记录
    url(r'^browse_histories/$',views.UserBrowseHistoryView.as_view()),
]

router = DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls