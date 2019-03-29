from django.conf.urls import url

from . import views



urlpatterns =[
    # 购物车增\删\改\查
    url(r'^carts/$',views.CartView.as_view()),

    # 购物车全选
    url(r'^carts/selection/$',views.CartSelectedAllView.as_view())
]