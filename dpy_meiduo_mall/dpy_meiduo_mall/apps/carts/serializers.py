from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """添加购物车序列化器"""

    # 定义字段
    sku_id = serializers.IntegerField(label='商品SKU ID',min_value=1)
    count = serializers.IntegerField(label='商品数量',min_value=1)
    selected = serializers.BooleanField(label='是否勾选',default=True)

    # 额外追加校验
    def validate_sku_id(self,value):
        """校验sku_id的有效性"""

        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id不存在')

        return value



class CartSKUSerializer(serializers.ModelSerializer):
    """查询购物车序列化器"""

    count = serializers.IntegerField(label='商品数量',min_value=1)
    selected = serializers.BooleanField(label='是否勾选',default=True)

    class Meta:
        model = SKU
        fields = ['id','name','price','default_image_url','count','selected']



class CartDeleteSerializer(serializers.Serializer):
    """删除购物车序列化器"""

    sku_id = serializers.IntegerField(label='商品SKU ID',min_value=1)

    def validate_sku_id(self, value):
        """校验sku_id的有效性"""

        try:
            sku_id = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品sku_id不存在')

        return value


class CartSelectAllSerializer(serializers.Serializer):
    """购物车全选序列化器"""

    # label是给后端接口使用的(查看)
    # bool类型不需要校验
    selected = serializers.BooleanField(label='是否全选')
