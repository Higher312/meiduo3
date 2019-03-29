from django.contrib import admin

from . import models
from celery_tasks.html.tasks import generate_static_list_search_html,generate_static_sku_detail_html

# Register your models here.


class GoodsCategoryAdmin(admin.ModelAdmin):
    """监听事件,触发异步任务"""

    def save_model(self, request, obj, form, change):
        """
        站点中点击商品分类(GoodsCategory)的保存按钮时调用
        :param request: 本次保存的请求对象
        :param obj: 当前要修改或保存的模型对象
        :param form: 本次提交的表单数据
        :param change: bool类型,表示本次保存和之前数据有无修改(修改True)
        :return: None
        """
        obj.save()

        # 触发异步任务生成list.html
        generate_static_list_search_html.delay()

    def delete_model(self, request, obj):
        """
        站点中点击商品分类(GoodsCategory)的删除按钮时调用
        :param request: 本次请求对象
        :param obj: 本次要删除的模型对象
        :return: None
        """
        obj.delete()

        # 触发异步任务生成list.html
        generate_static_list_search_html.delay()


class SKUAdmin(admin.ModelAdmin):
    """SKU站点模型管理类"""

    def save_model(self, request, obj, form, change):

        obj.save()
        generate_static_sku_detail_html.delay(obj.id)

    def delete_model(self, request, obj):

        obj.delete()
        generate_static_sku_detail_html.delay(obj.id)


class SKUAImageAdmin(admin.ModelAdmin):
    """SKU图片站点模型管理类"""

    def save_model(self, request, obj, form, change):

        obj.save()
        generate_static_sku_detail_html.delay(obj.sku_id)

    def delete_model(self, request, obj):
        
        obj.delete()
        generate_static_sku_detail_html.delay(obj.sku_id)


admin.site.register(models.GoodsCategory,GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU,SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage,SKUAImageAdmin)