"""celery配置信息"""

# 指定异步任务的存储位置(redis,7号库),即任务队列的位置
broker_url = "redis://192.168.174.128/7"