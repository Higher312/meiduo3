from django.shortcuts import render
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework import status
import base64,pickle

from goods.models import SKU
from .serializers import CartSerializer,CartSKUSerializer,CartDeleteSerializer,CartSelectAllSerializer
# Create your views here.


class CartView(APIView):
    """购物车后端接口"""

    def perform_authentication(self, request):
        """解决用户未登录时,JWT认证问题,延迟认证"""

        """
        前端在请求时传递了JWT的请求头,
        如果认证不通过就进入不了接口,直接响应401未认证,
        前端解决方式:加if判断
        后端解决方式:重写perform_authentication方法
        """
        pass

    def post(self,request):
        """添加购物车"""

        # 指定序列化器
        serializer = CartSerializer(data=request.data)
        # 数据校验,有异常时并自动抛出异常
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        sku_id = validated_data.get('sku_id')
        count = validated_data.get('count')
        selected = validated_data.get('selected')

        # 捕捉user对象没有值,即未登录时异常,实现未登录用户添加商品到购物车
        try:
            user = request.user
        except:
            user = None

        # 提前创建响应对象
        response = Response(serializer.data,status=status.HTTP_201_CREATED)

        """登陆情况操作redis数据库
            前端未传token,user=request.user获取的也是匿名用户
            避免使匿名用户也能操作redis,加入权限认证
        """
        if user and user.is_authenticated:
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')

            # 创建管道
            pl = redis_conn.pipeline()

            """
            先把当前用户的购物车数据查询出来
            判断当前要添加的sku_id在hash字典中是否已经存在
            如果不存在,则直接添加
            如果存在,把原sku_id的count取出累加上本次count
            """
            """
            redis_dict = redis_conn.hgetall('cart_%s' % user.id)

            for red_sku_id in redis_dict:
                if sku_id == int(red_sku_id):
                    origin_count = redis_dict[red_sku_id]
                    count = count + origin_count

            # 存储sku_id,count存储到hash字典
            redis_conn.hmset('cart_%s' % user.id,sku_id,count)
            """

            # hincrby(取hash字典的key,sku_id,count)
            # 会取出原有的key和现在的key作比较,如果key已存在,取出原有的count加上现在的count
            # redis_conn.hincrby('cart_%s' % user.id,sku_id,count)
            pl.hincrby('cart_%s' % user.id,sku_id,count)

            # 将sku_id的选中状态存储到set集合中
            # 只有被勾选的商品才添加的set中
            if selected:
                # redis_conn.sadd('selected_%s' % sku_id)
                pl.sadd('selected_%s' % user.id,sku_id)

            # 执行管道
            pl.execute()

            # return Response(serializer.data,status=status.HTTP_201_CREATED)

        else:
            """未登录情况操作cookie"""
            # 获取当前cookie中已有的购物车数据
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                # 如果当前cookie中已经有数据,然后再进行转换

                # 把cookie的字符串转换成bytes类型的字符串,encode()
                cart_str_bytes = cart_str.encode()
                # 把bytes类型的字符串转换成bytes类型的ASCII,base64.b64decode()
                cart_ascii_bytes = base64.b64decode(cart_str_bytes)
                # 把bytes类型的ASCII转换成字典,pickle.loads()
                cart_dict = pickle.loads(cart_ascii_bytes)
            else:
                # 如果当前cookie中没有数据,准备一个空字典
                cart_dict = {}

            # 如果添加的商品是已存在的,做增量计算
            for cookie_sku_id in cart_dict:
                if sku_id == cookie_sku_id:
                    origin_count = cart_dict[cookie_sku_id]['count']
                    count += origin_count

            # 包装cookie购物车数据
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }

            # 存入cookie,把字典转换成字符串
            # 把字典转换成bytes类型的ASCII
            cart_ascii_bytes = pickle.dumps(cart_dict)
            # 把bytes类型的ASCII转换成bytes类型的字符串
            cart_str_bytes = base64.b64encode(cart_ascii_bytes)
            # 把bytes类型的字符串转换成字符串
            cart_str = cart_str_bytes.decode()

            # 创建response对象
            # return Response(serializer.data,status=status.HTTP_201_CREATED)
            response.set_cookie('cart',cart_str)

        # 响应
        return response

    def get(self,request):
        """查询购物车"""

        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:
            """登录用户操作redis购物车数据"""

            # 连接redis数据库
            redis_conn = get_redis_connection('cart')

            # 获取hash大字典
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)

            # 获取set集合数据
            redis_selected = redis_conn.smembers('selected_%s' % user.id)

            # 构建空字典,用于存储字符串购物车数据
            cart_dict = {}

            for sku_id,count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count),
                    'selected':sku_id in redis_selected
                }
        else:
            """用户未登录操作cookie购物车数据"""
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

            else:
                cart_dict = {}

        # 获取出字典中的所有sku_id
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 创建序列化器进行序列化
        serializer = CartSKUSerializer(skus,many=True)
        return Response(serializer.data)

    def put(self,requset):
        """修改购物车"""

        # 创建序列化器
        serializer = CartSerializer(data=requset.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        sku_id = validated_data.get('sku_id')
        count = validated_data.get('count')
        selected = validated_data.get('selected')
        try:
            user = requset.user
        except:
            user = None

        response = Response(serializer.data)

        if user and user.is_authenticated:
            """登录用户操作redis购物车数据"""

            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 直接覆盖商品的购买数量
            pl.hset('cart_%s' % user.id,sku_id,count)

            # 修改商品的勾选状态,如果勾选就添加到set集合中,否则从set集合中移除
            if selected:
                pl.sadd('selected_%s' % user.id,sku_id)
            else:
                pl.srem('selected_%s' % user.id,sku_id)

            pl.execute()

        else:
            """未登录用户操作cookie购物车数据|"""

            # 获取当前cookie中已有的购物车数据
            cart_str = requset.COOKIES.get('cart')

            # 如果当前cookie中已经有数据,然后再进行转换
            if cart_str:

                # 把cookie的字符串转换成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 把bytes类型的字符串转换成bytes类型的ASCII
                cart_ascii_bytes = base64.b64decode(cart_str_bytes)
                # 把bytes类型的ASCII转换成字典
                cart_dict = pickle.loads(cart_ascii_bytes)
            else:
                # 如果之前cookie中没有购物车数据,准备一个空字典
                cart_dict = {}

            # 包装cookie购物车数据
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }

            # 把字典转换成bytes类型的ASCII
            cart_ascii_bytes = pickle.dumps(cart_dict)
            # 把bytes类型的ASCII转换成bytes类型的字符串
            cart_str_bytes = base64.b64decode(cart_ascii_bytes)
            # 把bytes类型的字符串转换成字符串
            cart_str = cart_str_bytes.decode()

            # 设置cookie
            response.set_cookie('cart',cart_str)

        return response

    def delete(self,request):
        """删除购物车"""

        # 创建序列化器进行反序列化校验
        serializer = CartDeleteSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:
            """登陆用户操作redis购物车数据"""

            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 把sku_id对应的商品从hash字典中删除
            pl.hdel('cart_%s' % user.id,sku_id)

            # 把set集合中sku_id移除,移除商品的勾选状态
            pl.srem('selected_%s' % user.id,sku_id)

            pl.execute()

            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            """未登录用户操作cookie购物车数据"""

            # 获取cookie中的购物车数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # cart_dict = {}
                # 如果cookies为空直接响应
                return Response({'message':'cookie为空'},status=status.HTTP_400_BAD_REQUEST)

            # 判断要删除的sku-id是否存在
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            # 把字典转换成字符串
            cart_str =base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            response = Response(status=status.HTTP_204_NO_CONTENT)
            # 设置cookie
            response.set_cookie('cart',cart_str)

            return response


class CartSelectedAllView(APIView):
    """购物车全选"""

    def perform_authentication(self, request):
        """延后认证"""
        pass

    def put(self,request):
        """"""

        # 创建序列化器进行反序列化
        serializer = CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except:
            user = None

        # 创建响应对象
        response = Response({'message':'ok'})

        if user and user.is_authenticated:
            """登录用户操作redis购物车"""

            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')

            # 把hash字典中的所有购物车商品数据取出
            redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)

            # 获取出字典中的所有key
            sku_ids = redis_cart_dict.keys()
            # 如果是全选就把所有的sku_id添加到set集合中
            if selected:
                redis_conn.sadd('selected_%s' % user.id,*sku_ids)

            else:
                # 如果是取消全选,就把所有的sku_id从set集合中移除
                redis_conn.srem('selected_%s' % user.id,*sku_ids)

        else:
            """未登录用户操作cookie购物车"""
            # 获取cookie
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                # 把cart_str转换成cart_dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

            else:
                # cart_dict = {}
                return Response({'message':'cookie为空'},status=status.HTTP_400_BAD_REQUEST)

            # 遍历字典修改购物车所有商品的勾选状态
            for sku_id in cart_dict:
                cart_dict[sku_id]['selected'] = selected

            # 把cart_dict转换成cart_str
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response.set_cookie('cart',cart_str)

        return response