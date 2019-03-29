"""celery客服端"""
from celery import Celery
import os


# 手动指定celery配置文件加载路径
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dpy_meiduo_mall.settings.dev")

# 1.创建celery应用对象
# 传递的meiduo没有实际意义,只是给celery应用对象起了一个别名
celery_app = Celery('meiduo')

# 2.加载celery配置信息
celery_app.config_from_object('celery_tasks.config')

# 3.自动注册异步任务
celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email','celery_tasks.html'])