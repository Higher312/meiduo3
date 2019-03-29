from django.shortcuts import render
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter

from .models import SKU
from .serializers import SKUListSerializer,SKUSearchSerializer
# Create your views here.


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUSearchSerializer


class SKUListView(ListAPIView):
    """查询商品列表sku数据"""

    # 指定序列化器
    serializer_class = SKUListSerializer

    # 指定过滤后端为排序
    filter_backends = [OrderingFilter]
    # 指定排序字段
    ordering_fields = ('create_time','price','sales')

    # 局部过滤,只对当前视图过滤
    # pagination_class = StandardResultsSetPagination

    # 指定查询集
    # queryset = SKU.objects.fileter(is_launched=True,category_id=xx)
    # 外键
    # hbook = book
    # bhook_id = book.id

    def get_queryset(self):
        # 视图对象.kwargs属性可以获取正则组别名的参数数据
        # 视图对象.args属性可以获取正则组每页别名的参数数据

        cat_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=cat_id)


