from itsdangerous import TimedJSONWebSignatureSerializer as TJSSerializer,BadData
from django.conf import settings


def generate_save_user_token(openid):
    """对openid进行加密"""

    # 1.创建序列化器
    # 使用格式： serializer = TJSSerializer (秘钥, 有效期秒)
    serializer = TJSSerializer(settings.SECRET_KEY,600)

    # 2.包装要加密的数据
    data = {
        'openid':openid
    }

    # 3.使用dumps转换成bytes类型（再加密）(默认返回值bytes类型)
    # 使用格式：serializer. dumps（数据）
    token = serializer.dumps(data)

    # 4.响应
    return token.decode()


def check_save_user_token(access_token):
    """解密"""

    # 1.创建序列化器
    serializer = TJSSerializer(settings.SECRET_KEY,600)

    # 2.反序列化解密
    try:
        data = serializer.loads(access_token)
    except BadData:
        return None

    else:
        return data.get('openid')