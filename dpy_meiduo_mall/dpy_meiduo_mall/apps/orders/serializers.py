from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal
from django_redis import get_redis_connection
from django.db import transaction

from goods.models import SKU
from .models import OrderInfo,OrderGoods


class OrderAllSerializer(serializers.ModelSerializer):
    """全部订单序列化器"""

    class Meta:
        model = OrderInfo

        fields = ['order_id','total_count','total_amount', 'pay_method','status']


class CommitOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化器"""

    class Meta:
        model = OrderInfo
        # 输出字段:order_id
        # 输入字段:'address','pay_method'
        fields = ['order_id','address','pay_method']
        # 字段限制
        read_only_fields = ['order_id']
        extra_kwargs = {
            'address':{
                'write_only':True,
                'required':True,
            },
            'pay_method':{
                'write_only':True,
                'required':True,
            }
        }

    def create(self, validated_data):
        """重写存储订单表,订单商品表数据方法"""

        """获取当前保存订单时需要的信息"""
        # 获取user对象
        user = self.context['request'].user

        # 生成订单编号(当前时间+user_id)
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id

        # 获取validated_data里面的address的模型对象
        address = validated_data.get('address')

        # 获取validated_data里面的pay_method支付方式
        pay_method = validated_data.get('pay_method')

        # 定义订单状态
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        # 明显的开启事物
        with transaction.atomic():

            # 开启一个事物点
            save_point = transaction.savepoint()

            try:

                # 保存订单基本信息 OrderInfo(一)
                order = OrderInfo.objects.create(
                    user=user,
                    order_id = order_id,
                    address = address,
                    total_count = 0,
                    total_amount = Decimal('0.00'),
                    freight = Decimal('10.00'),
                    pay_method=pay_method,
                    # status = '待支付' if '如果支付方式是支付宝' else '待发货'
                    status = status

                )

                # 从redis读取购物车中被勾选的商品信息
                redis_conn = get_redis_connection('cart')
                redis_cart = redis_conn.hgetall('cart_%s' % user.id)
                redis_selected = redis_conn.smembers('selected_%s' % user.id)

                # 构建空字典
                cart_dict = {}

                # 遍历购物车中被勾选的商品信息
                for sku_id_bytes in redis_selected:
                    cart_dict[int(sku_id_bytes)] = int(redis_cart[sku_id_bytes])

                # sku_ids = SKU.objects.filter(id__in=cart_dict.keys())
                # 一键获取商品id可能出现缓存问题

                # 获取当前商品的id和销量
                for sku_id,sku_count in cart_dict.items():

                    while True:
                        # 获取sku对象
                        sku = SKU.objects.get(id=sku_id)

                        # 先把sku的库存和销量取出
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断库存,如果购买量大于库存
                        if sku_count > sku.stock:
                            raise serializers.ValidationError('库存不足')

                        # 减少库存,增加销量 SKU
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 重新查询新的库存
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        result = SKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=new_stock,sales=new_sales)

                        if result == 0:
                            # 如果result为0说明下单失败,跳过本次循环,继续下一次
                            continue


                        # 修改SPU销量
                        # 获取spu模型对象
                        spu = sku.goods
                        spu.sales += sku_count
                        spu.save()

                        # 保存订单商品信息 OrderGoods(多)
                        OrderGoods.objects.create(
                            order = order,
                            sku = sku,
                            count = sku_count,
                            price = sku.price
                        )

                        # 累加计算总数量和总价
                        order.total_count += sku_count
                        order.total_amount += (sku.price * sku_count)

                        # 下单成功
                        break

                # 加入邮费
                order.total_amount += order.freight

                # 更新订单信息
                order.save()


            except Exception:
                # 暴力回滚
                transaction.savepoint_rollback(save_point)
                raise
            else:
                # 提交事物
                transaction.savepoint_commit(save_point)

            # 清楚购物车中已结算的商品
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id,*redis_selected)
            pl.srem('selected_%s' % user.id,*redis_selected)
            pl.execute()

        # 响应
        return order


class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)