from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """分页配置类"""

    # 若前端不传每页显示条数,使用默认值2条
    page_size = 2

    # 定义前端用于控制每页显示条数字段
    page_size_query_param = 'page_size'

    # 每页最大显示条数
    max_page_size = 20
