from django.db import models


class BaseModel(models.Model):
    """为模型类补充字段"""

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:

        """
        元数据选项abstract=True声明为抽象模型类;
        抽象模型类,不会在数据库中创建数据表,仅仅用于实现继承
        """
        abstract = True
