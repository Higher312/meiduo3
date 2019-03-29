from django.shortcuts import render
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView,ListAPIView

from goods.models import SKU
from .serializers import OrderSettlementSerializer,CommitOrderSerializer,OrderAllSerializer
from .models import OrderInfo


class OrderSettlementView(APIView):
    """结算接口"""

    # 指定权限
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """"""

        user = request.user

        # 获取出redis中的hash字典及set
        redis_conn = get_redis_connection('cart')
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        redis_selected = redis_conn.smembers('selected_%s' % user.id)

        # 准备空字典
        cart_dict = {}

        # 遍历set集合,只拿到勾选商品的sku_id和count
        for sku_id_bytes in redis_selected:
            cart_dict[int(sku_id_bytes)] = int(redis_cart[sku_id_bytes])

        # 获取出所有勾选商品的SKU模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 给对应的每个sku模型多添加一个count属性
        for sku in skus:
            sku.count = cart_dict[sku.id]

        # 运费
        freight = Decimal(10.00)

        # 创建序列化器进行序列化输出
        """
        序列化器的第一个参数:
        单个模型对象\字典:不需声明
        查询集\列表模型:需声明many=True
        """
        serializer = OrderSettlementSerializer({'freight':freight,'skus':skus})

        # 响应
        return Response(serializer.data)


class CommitOrderView(CreateAPIView):
    """提交订单"""

    # 指定序列化器
    serializer_class = CommitOrderSerializer

    # 指定权限
    permission_classes = [IsAuthenticated]


class OrderAllView(ListAPIView):
    """全都订单"""

    # 指定查询集
    queryset = OrderInfo.objects.all()

    # 指定序列化器
    serializer_class = OrderAllSerializer

    # 指定权限
    permission_classes = [IsAuthenticated]