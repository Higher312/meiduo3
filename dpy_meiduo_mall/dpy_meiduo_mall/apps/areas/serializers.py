from rest_framework import serializers

from .models import Area


class AreaSerializer(serializers.ModelSerializer):
    """
    查所有省时(list),它代表序列化输出所有省的序列化器
    查询单个省时,它代表序列化输出当前省下面的所有城市的序列化器
    查询单个市时,它代表序列化输出当前市下面的所有区县的序列化器
    """

    class Meta:
        model = Area
        fields = ['id','name']


class SubsSerializer(serializers.ModelSerializer):
    """
    此序列化器只有在查询单一视图时才会使用
    查询单个省时,序列化输出当前省下面的所有市
    查询单个市时,序列化输出当前市下面的所有区县
    """

    subs = AreaSerializer(many=True,read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name','subs']