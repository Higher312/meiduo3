from django.conf.urls import url

from . import views
urlpatterns = [
    # 获取扫码url
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    # QQ登陆认证
    url(r'^qq/user/$',views.QQAuthUserView.as_view()),
]