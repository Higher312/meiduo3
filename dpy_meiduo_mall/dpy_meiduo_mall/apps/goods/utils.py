from collections import OrderedDict

from .models import GoodsChannel


def get_categories():
    """商品分类菜单:第一级和第二级"""

    """
    示例:
    组号group_id相同:在一个频道内
    序号sequence:组内的顺序(运营管理使用)
    同一频道channels:第一级商品类别
    同一商品类别sub_cats:第二级商品类别

    使用有序字典保存类别的顺序
    categories = {
        1: { # 组1
            'channels': [{'id':, 'name':, 'url':},{}, {}...],
            'sub_cats': [{'id':, 'name':, 'sub_cats':[{},{}]}, {}, {}, ..]
        },
        2: { # 组2

        }
    }
    """

    # 创建空的商品频道有序字典
    categories = OrderedDict()

    # 根据组号和序号,查询商品频道,返回查询集
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 遍历商品频道查询集,
    for channel in channels:

        # 获取第一级商品分类的组号
        group_id = channel.group_id

        # 当前组号不在有序字典中,加入,(组号为键,当第一级商品分类和第二级商品分类为值)
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # 当前组号在有序字典中,利用当前频道的外键属性,获取当前频道中的第一级商品类别
        cat1 = channel.category

        # 把当前第一级商品类别的属性追加到有序字典中
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 第一级商品类别为一方,第二级商品类别为多方,一方外键是多方类名小写_set
        # 获取第二级商品分类查询集
        # 遍历第二级商品分类查询集,获取当前第二级商品分类
        for cat2 in cat1.goodscategory_set.all():

            # 绑定当前第二级商品分类到sub_cats键
            cat2.sub_cats = []

            # 第二级商品类别为一方,商品列表为多方,一方外键是多方类名小写_set
            # 获取商品列表查询集
            # 遍历商品列表查询集,获取当前商品列表
            for cat3 in cat2.goodscategory_set.all():

                # 把当前商品列表追加到当前第二级商品分类字典中
                cat2.sub_cats.append(cat3)

            # 把第二级商品分类追加到商品频道有序字典中
            categories[group_id]['sub_cats'].append(cat2)

    # 返回商品频道有序字典
    return categories