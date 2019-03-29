from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储系统"""

    def __init__(self,client_conf=None,base_url=None):
        """初始化方法:不带任何参数实例化存储类"""

        """方式一"""
        # if client_conf:
        #     self.client_conf = client_conf
        # else:
        #     self.client_conf = settings.FDFS_CLIENT_CONF

        """方式二"""
        # self.client_conf = client_conf if client_conf else settings.FDFS_CLIENT_CONF
        # self.base_url = base_url if base_url else settings.FDFS_BASE_URL

        """方式三"""
        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_BASE_URL

    def _open(self,name,mode='rb'):
        """
        被Storage.open()调用，在打开文件时被使用
        :param name: 表示要打开的文件名
        :param mode: 打开文件的模式 read bytes
        """
        pass

    def _save(self,name,content):
        """
        被Storage.save()调用,保存文件时就会调用
        Django会将该方法的返回值保存到数据库中对应的文件字段，
        也就是说该方法应该返回要保存在数据库中的文件名称信息
        :param name: 要保存的文件名
        :param content: 要保存的文件对象
        :return: file_id 把上传后的文件路径返回
        """
        # 1.创建client

        # 固定文件路径形式
        # client = Fdfs_client('dpy_meiduo_mall/utils/fastdfs/client.conf')
        # 使用配置信息形式
        # client = Fdfs_client(settings.FDFS_CLIENT_CONF)

        # 可在无参数时实例化对象
        client = Fdfs_client(self.client_conf)

        # 2.上传文件到fastdfs

        # 绝对路径方式,此方法上传的图片,在storage中有文件后缀
        # ret = client.upload_by_filename('文件的绝对路径")

        # 把要上传的文件以二进制形式进行上传,没有后缀
        ret = client.upload_by_buffer(content.read())

        # 3.判断上传是否成功
        if ret.get('Status') != 'Upload successed.':
            raise Exception('Upload file failed')

        # 4.文件上传成功
        return ret.get('Remote file_id')

    def exists(self, name):
        """此方法只返回bool值,
        返回True表示上传文件已存在,不再上传
        返回False表上传文件不存在,可以上传
        name:要上传的文件名"""

        return False

    def url(self, name):
        """
        返回上传到fastdfs中文件的绝对路径给浏览器访问使用
        :param name: 上传到fastdfs中的file_id
        """

        # return settings.FDFS_BASE_URL + name
        return self.base_url + name
