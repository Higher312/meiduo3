from rest_framework.urls import url

from . import views


urlpatterns = [
    # 结算
    url(r'^orders/settlement/$',views.OrderSettlementView.as_view()),
    # 提交订单
    url(r'^orders/$',views.CommitOrderView.as_view()),

    url(r'^orders/orderall/$',views.OrderAllView.as_view()),
]