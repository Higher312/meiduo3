from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.mixins import CacheResponseMixin

from .models import Area
from . import serializers

# Create your views here.


class AreaViewSet(CacheResponseMixin,ReadOnlyModelViewSet):
    """查询省市区数据"""

    # 禁用分页
    pagination_class = None

    # 指定序列化器
    serializer_class = serializers.AreaSerializer

    # 指定查询集

    def get_queryset(self):
        """重写get_queryset()方法,动态指定查询集"""

        if self.action == 'list':
            # 当前是List行为
            return Area.objects.filter(parent=None)

        else:
            return Area.objects.all()

    def get_serializer_class(self):
        """重写get_serializer_class()方法,动态指定序列化(输出)器"""

        if self.action == 'list':
            return serializers.AreaSerializer
        else:
            return serializers.SubsSerializer
