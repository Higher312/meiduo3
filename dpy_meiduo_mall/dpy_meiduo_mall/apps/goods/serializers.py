from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from .models import SKU
from .search_indexes import SKUIndex

class SKUListSerializer(serializers.ModelSerializer):
    """sku序列化器"""

    class Meta:
        model = SKU
        # 要映射的字段
        fields = ['id','name','price','default_image_url','comments']


class SKUSearchSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUListSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'object')