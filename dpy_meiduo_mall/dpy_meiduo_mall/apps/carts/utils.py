import pickle,base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request,user,response):
    """
    把cookie购物车数据合并到redis
    :param request: 本次要来合并时借用的请求对象
    :param user: 登陆时创建的user,为了后面获取redis数据而借用来的
    :param response: 为了后面合并完购物车数据清空cookie数据而借用的响应对象
    :return: 把借用的resposne响应回去
    """

    """
    存储到redis的数据都是以字符串的类型存储;
    从redis取出的数据,内部结果的bytes类型
    """

    # 获取cookie中的购物车数据
    cart_str = request.COOKIES.get('cart')

    if not cart_str:
        # 如果cookie购物车没有数据,直接返回
        return response

    # 把cookie购物车数据转换成cart_dict
    cookie_cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 获取redis中的购物车数据
    redis_conn = get_redis_connection('cart')

    # 获取redis中的hash字典
    redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)

    # 获取redis中商品的勾选状态
    redis_selected_set = redis_conn.smembers('selected_%s' % user.id)

    # 定义一个字典变量用来合并购物车数据
    new_redis_cart_dict = {}

    # 遍历redis的hash字典
    for sku_id_bytes,count_bytes in redis_cart_dict.items():

        # 先把redis中的数据装入new_redis_cart_dict中,注意,key一定要转换成int类型
        new_redis_cart_dict[int(sku_id_bytes)] = int(count_bytes)

    # 遍历cookie购物车字典
    for sku_id,sku_dict in cookie_cart_dict.items():

        # 把cookie的数据装入到new_redis_cart_dict
        new_redis_cart_dict[sku_id] = sku_dict['count']

        if sku_dict['selected']:
            # 如果cookie中的当前sku_id是勾选状态,就把此商品添加到redis中set集合

            # add()是set集合添加元素的方法,如果有相同的,会自动去重
            redis_selected_set.add(str(sku_id).encode())

    # 创建管道对象
    pl = redis_conn.pipeline()

    # 把合并后的new_redis_cart_dict大字典存储到redis的hash中
    pl.hmset('cart_%s' % user.id,new_redis_cart_dict)

    # 把合并后的勾选状态set集合存储到redis的set集合中
    pl.sadd('selected_%s' % user.id,*redis_selected_set)

    # 执行管道
    pl.execute()

    # 把cookie中的购物车数据请情况
    response.delete_cookie('cart')

    return response

