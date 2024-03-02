import time
import uuid
import hashlib
import requests
import urllib.parse

from typing import List, Union


def get_direct_signed_link(url, uid, primary_key, expired_time_sec):
    """
    进行直链鉴权。

    # 待签名URL
    origin_url = 'http://vip.123pan.com/10/layout1/layout2/%E6%88%91.txt'
    # 鉴权密钥
    primary_key = 'mykey'
    # 账号id
    uid = 10
    # 防盗链过期时间间隔(秒)，60秒会导致链接失效
    expire_time_sec = 3 * 60
    url = get_signed_url(origin_url, uid, primary_key, expire_time_sec)

    :param url: 文件地址
    :param uid: 用户 uid
    :param primary_key: 密钥
    :param expired_time_sec: 过期描述
    :return: 签名之后的地址
    """
    path = urllib.parse.urlparse(url).path
    # 下载链接的过期时间戳（秒）
    timestamp = int(time.time()) + expired_time_sec
    # 生成随机数（建议使用UUID，不能包含中划线（-））
    random_uuid = str(uuid.uuid4()).replace('-', '')
    # 待签名字符串="URI-timestamp-rand-uid-PrivateKey" (注:URI是用户的请求对象相对地址，不包含参数)
    unsigned_str = f'{path}-{timestamp}-{random_uuid}-{uid}-{primary_key}'
    auth_key = f'{timestamp}-{random_uuid}-{uid}-' + hashlib.md5(unsigned_str.encode()).hexdigest()
    return url + '?auth_key=' + auth_key


class BaseURL:
    # 域名
    BASE_URL = "https://open-api.123pan.com"

    # 请求 Header
    PLATFORM = "open_platform"

    # 接口校验获取
    GET_ACCESS_TOKEN = BASE_URL + "/api/v1/access_token"

    # 用户类
    USER_INFO = BASE_URL + "/api/v1/user/info"

    # 文件类
    FILE_LIST = BASE_URL + "/api/v1/file/list"
    FILE_TRASH = BASE_URL + "/api/v1/file/trash"
    FILE_DELETE = BASE_URL + "/api/v1/file/delete"
    FILE_RECOVER = BASE_URL + "/api/v1/file/recover"
    FILE_MOVE = BASE_URL + "/api/v1/file/move"
    FILE_UPLOAD_MKDIR = BASE_URL + "/upload/v1/file/mkdir"
    FILE_UPLOAD_CREATE = BASE_URL + "/upload/v1/file/create"
    FILE_UPLOAD_LIST_UPLOAD_PARTS = BASE_URL + "/upload/v1/file/list_upload_parts"
    FILE_UPLOAD_GET_UPLOAD_URL = BASE_URL + "/upload/v1/file/get_upload_url"
    FILE_UPLOAD_COMPLETE = BASE_URL + "/upload/v1/file/upload_complete"
    FILE_UPLOAD_ASYNC_RESULT = BASE_URL + "/upload/v1/file/upload_async_result"

    # 文件分享类
    SHARE_LINK_CREATE = BASE_URL + "/api/v1/share/create"

    # 文件直链类
    LINK_QUERYTRANSCODE = BASE_URL + "/api/v1/direct-link/queryTranscode"
    LINK_DOTRANSCODE = BASE_URL + "/api/v1/direct-link/doTranscode"
    LINK_GET_M3U8 = BASE_URL + "/api/v1/direct-link/get/m3u8"
    LINK_DIRECT_LINK_ENABLE = BASE_URL + "/api/v1/direct-link/enable"
    LINK_DIRECT_LINK_DISABLE = BASE_URL + "/api/v1/direct-link/disable"
    LINK_DIRECT_URL = BASE_URL + "/api/v1/direct-link/url"
    LINK_OFFINE_DOWNLOAD = BASE_URL + "/api/v1/offline/download"


class DataResponse:
    response_data = None

    def __init__(self, response=None, code=0, message="", data=None):
        """
        服务器返回数据类。

        :param response: 服务器返回原 请求 数据
        :param code: 自定义响应值。
        :param message: 自定义消息。
        :param data: 自定义数据。
        """
        if response is None:
            self.response = None
            self.response_data = {
                "code": code,
                "message": message,
                "data": data,
                "x-traceID": ""
            }
            return

        self.response = response
        self.response_data = response.json()

    @property
    def data(self):
        """
        服务器返回数据段。
        :return: str
        """
        return self.response_data.get('data')

    @property
    def x_traceID(self):
        """
        服务器记录值。
        :return: str
        """
        return self.response_data.get('x-traceID')

    @property
    def message(self):
        """
        服务器返回消息。
        :return: str
        """
        return self.response_data.get('message')

    @property
    def success(self):
        """
        是否成功
        :return: bool
        """
        return self.response_data.get('code') == 0

    @property
    def code(self):
        """
        服务器返回 code 码。参见：https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced/txgcvbfgh0gtuad5

        +---------------+-----------------+
        | body 中的 code  | 描述            |
        +===============+=================+
        | 0             | 成功             |
        | 401           | access_token无效 |
        | 429           | 请求太频繁        |
        +---------------+-----------------+

        :return: int
        """
        return self.response_data.get('code')


class pan123openAPI():
    clientID = None
    clientSecret = None

    access_token = None
    access_token_expiredAt = None

    baseurl = BaseURL()

    def __init__(self, clientID=None, clientSecret=None):
        """
        123pan OpenAPI 接口初始化。

        python::

            # 自动获取 access_token
            pan123 = pan123openAPI("your clientID", "your clientSecret")
            pan123.refresh_access_token()

            # 手动设置 access_token
            pan123 = pan123openAPI()
            pan123.refresh_access_token("your access token")


        :param clientID: 客户端ID，开发者客户端ID。
        :param clientSecret: 客户端密钥，开发者客户端ID。
        """
        self.clientID = clientID
        self.clientSecret = clientSecret

        self.user = _User(self)
        self.file = _File(self)
        self.link = _Link(self)

    def refresh_access_token(self, access_token=None) -> DataResponse:
        """
        重新获取 access_token，或手动设置 access_token 。调用此函数后，可以调用其它函数对 123pan 进行操作。

        python::

            # 请求获取
            data = pan123.refresh_access_token().data
            print(data['accessToken'])  # eyJhb...
            print(data['expiredAt'])  # 2024-03-22T19:52:23+08:00

            # 自定义
            data = pan123.refresh_access_token("eyJhb...").data
            print(data['expiredAt'])  # 将返回空字符串

        """

        if access_token is not None:
            self.access_token = access_token
            return DataResponse(data={'accessToken': access_token, 'expiredAt': ""})

        headers = {
            'Platform': self.baseurl.PLATFORM
        }

        data = {
            'clientID': self.clientID,
            'clientSecret': self.clientSecret
        }

        response = requests.post(self.baseurl.GET_ACCESS_TOKEN, data, headers=headers)

        data_response = DataResponse(response)

        self.access_token = data_response.data['accessToken']
        self.access_token_expiredAt = data_response.data['expiredAt']

        return data_response

    def request(self, method, url, data=None, files=None):
        """
        简单请求服务器。

        :param method: 请求方式
        :param url: 统一资源定位器
        :param data: 请求携带数据
        :param files: 携带的文件
        :return: requests.Response
        """
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/json',
            'Platform': self.baseurl.PLATFORM
        }

        response = getattr(requests, method)(url, data=data, headers=headers, files=files)

        return response


class _Link:
    def __init__(self, super_pan123: pan123openAPI):
        """
        分享链接或者直链相关。

        :param super_pan123: 父类
        """
        self.super = super_pan123
        self.baseurl = super_pan123.baseurl
        self.request = super_pan123.request

    def offine_download(self, url: str, fileName=None, callBackUrl=None) -> DataResponse:
        """
        创建离线下载任务。

        :param url: 下载资源地址(http/https)
        :param fileName: 自定义文件名称
        :param callBackUrl: 回调地址
                url: 下载资源地址
                status: 0 成功，1 失败
                fileReason：失败原因

                请求类型：POST
                {
                    "url": "http://dc.com/resource.jpg",
                    "status": 0,
                    "failReason": ""
                }
        :return: 服务器响应数据
        """
        data = {
            'url': url
        }

        if fileName:
            data['fileName'] = fileName

        if callBackUrl:
            data['callBackUrl'] = callBackUrl

        response = self.request('post', self.baseurl.LINK_OFFINE_DOWNLOAD)

        data_response = DataResponse(response)

        return data_response

    def query_transcode(self, ids: list) -> DataResponse:
        """
        查询直链转码进度。参考：https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced/mf5nk6zbn7zvlgyt

        data 数据段是一个字典，键值如下：

        +-----------+-------+------+-------------------------+
        | 名称        | 类型    | 是否必填 | 说明                      |
        +===========+=======+======+=========================+
        | noneList  | array | 必填   | 未发起过转码的 ID              |
        | errorList | array | 必填   | 错误文件ID列表,这些文件ID无法进行转码操作 |
        | success   | array | 必填   | 转码成功的文件ID列表             |
        +-----------+-------+------+-------------------------+

        :param ids: 视频文件ID列表。示例:[1,2,3,4]
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.LINK_QUERYTRANSCODE,
                                data={'ids': ids})

        data_response = DataResponse(response)

        return data_response

    def do_transcode(self, ids: list) -> DataResponse:
        """
        发起直链转码。

        :param ids: 视频文件ID列表。示例:[1,2,3,4]
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.LINK_DOTRANSCODE,
                                data={'ids': ids})

        data_response = DataResponse(response)

        return data_response

    def get_m3u8(self, fileID: int) -> DataResponse:
        """
        获取直链转码链接。

        服务器 data 返回数据如下：

        +---------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+
        | 名称                  | 类型     | 是否必填 | 说明                                                                                                                  |
        +=====================+========+======+=====================================================================================================================+
        | list                | array  | 必填   | 响应列表                                                                                                                |
        | list[*].resolutions | string | 必填   | 分辨率                                                                                                                 |
        | list[*].address     | string | 播放地址 | 请将播放地址放入支持的 hls 协议的播放器中进行播放。示例在线播放地址:https://m3u8-player.com/请注意,转码链接播放过程中将会消耗您的直链流量。如果您开启了直链鉴权,也需要将转码链接根据鉴权指引进行签名。 |
        +---------------------+--------+------+---------------------------------------------------------------------------------------------------------------------+


        :param fileID: 启用直链空间的文件夹的fileID
        :return: 服务器响应数据
        """
        response = self.request('get', self.baseurl.LINK_GET_M3U8,
                                data={'fileID': fileID})

        data_response = DataResponse(response)

        return data_response

    def direct_link_enable(self, fileID: int) -> DataResponse:
        """
        启用直链空间。

        服务器 data 返回数据如下：

        +----------+--------+------+-----------------+
        | 名称       | 类型     | 是否必填 | 说明              |
        +==========+========+======+=================+
        | filename | string | 必填   | 成功启用直链空间的文件夹的名称 |
        +----------+--------+------+-----------------+

        :param fileID: 启用直链空间的文件夹的fileID
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.LINK_DIRECT_LINK_ENABLE,
                                data={'fileID': fileID})

        data_response = DataResponse(response)

        return data_response

    def direct_link_disable(self, fileID: int) -> DataResponse:
        """
        禁用直链空间。

        服务器 data 返回数据如下：

        +----------+--------+------+-----------------+
        | 名称       | 类型     | 是否必填 | 说明              |
        +==========+========+======+=================+
        | filename | string | 必填   | 成功禁用直链空间的文件夹的名称 |
        +----------+--------+------+-----------------+

        :param fileID: 禁用直链空间的文件夹的fileID
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.LINK_DIRECT_LINK_DISABLE,
                                data={'fileID': fileID})

        data_response = DataResponse(response)

        return data_response

    def direct_link_url(self, fileID: int) -> DataResponse:
        """
        获取直链链接。

        服务器 data 返回数据如下：

        +----------+--------+------+-----------------+
        | 名称       | 类型     | 是否必填 | 说明              |
        +==========+========+======+=================+
        | url | string | 必填   | 文件对应的直链链接 |
        +----------+--------+------+-----------------+

        :param fileID: 需要获取直链链接的文件的fileID
        :return: 服务器响应数据
        """
        response = self.request('get', self.baseurl.LINK_DIRECT_URL,
                                data={'fileID': fileID})

        data_response = DataResponse(response)

        return data_response


class _User:
    def __init__(self, super_pan123: pan123openAPI):
        """
        用户相关数据请求。

        :param super_pan123: 父类
        """
        self.super = super_pan123
        self.baseurl = super_pan123.baseurl
        self.request = super_pan123.request

    def info(self) -> DataResponse:
        """
        获取用户信息。参见：https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced/fa2w0rosunui2v4m

        data 数据段是一个字典，键值如下：

        +----------------+--------+------+---------+
        | 名称             | 类型     | 是否必填 | 说明      |
        +================+========+======+=========+
        | uid            | number | 必填   | 用户账号id  |
        | nickname       | string | 必填   | 昵称      |
        | headImage      | string | 必填   | 头像      |
        | passport       | string | 必填   | 手机号码    |
        | mail           | string | 必填   | 邮箱      |
        | spaceUsed      | number | 必填   | 已用空间    |
        | spacePermanent | number | 必填   | 永久空间    |
        | spaceTemp      | number | 必填   | 临时空间    |
        | spaceTempExpr  | string | 必填   | 临时空间到期日 |
        +----------------+--------+------+---------+

        :return: 服务器响应数据
        """
        response = self.request('get', self.baseurl.USER_INFO)

        data_response = DataResponse(response)

        return data_response


class _File:
    def __init__(self, super_pan123: pan123openAPI):
        """
        文件操作相关数据请求。

        :param super_pan123: 父类
        """
        self.super = super_pan123
        self.baseurl = super_pan123.baseurl
        self.request = super_pan123.request

    def list(self, parentFileId, **kwargs):
        """
        罗列目录文件。参见：https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced/hosdqqax0knovnm2

        查询参数参考：

        +----------------+--------+------+--------------------------------+
        | 名称             | 类型     | 是否必填 | 说明                             |
        +================+========+======+================================+
        | parentFileId   | number | 必填   | 文件夹ID，根目录传 0                   |
        | page           | number | 必填（代码默认 1）   | 页码数                            |
        | limit          | number | 必填 （代码默认 15）  | 每页文件数量，最大不超过100                |
        | orderBy        | string | 必填  （代码默认 file_name） | 排序字段,例如:file_id、size、file_name |
        | orderDirection | string | 必填  （代码默认 asc） | 排序方向:asc、desc                  |
        | trashed        | bool   | 选填   | 是否查看回收站的文件                     |
        | searchData     | string | 选填   | 搜索关键字                          |
        +----------------+--------+------+--------------------------------+

        data 返回参数参考：

        +--------------------------+---------+------+--------------------------+
        | 名称                       | 类型      | 是否必填 | 说明                       |
        +==========================+=========+======+==========================+
        | total                    | number  | 必填   | 文件总数
        | fileList                 | array   | 必填   |                          |
        | fileList[*].fileID       | number  | 必填   | 文件ID                     |
        | fileList[*].filename     | string  | 必填   | 文件名                      |
        | fileList[*].type         | number  | 必填   | 0-文件  1-文件夹              |
        | fileList[*].size         | number  | 必填   | 文件大小                     |
        | fileList[*].etag         | boolean | 必填   | md5                      |
        | fileList[*].status       | number  | 必填   | 文件审核状态。 大于 100 为审核驳回文件   |
        | fileList[*].parentFileId | number  | 必填   | 目录ID                     |
        | fileList[*].parentName   | string  | 必填   | 目录名                      |
        | fileList[*].category     | number  | 必填   | 文件分类：0-未知 1-音频 2-视频 3-图片 |
        | fileList[*].contentType  | number  | 必填   | 文件类型                     |
        +--------------------------+---------+------+--------------------------+

        :param kwargs: 查询参数。
        :return: 服务器响应数据
        """
        kwargs['parentFileId'] = parentFileId
        kwargs['page'] = kwargs.get('page', 1)
        kwargs['limit'] = kwargs.get('limit', 15)
        kwargs['orderBy'] = kwargs.get('orderBy', 'file_name')
        kwargs['orderDirection'] = kwargs.get('orderDirection', 'asc')

        response = self.request('get', self.baseurl.FILE_LIST, kwargs)

        data_response = DataResponse(response)

        return data_response

    def trash(self, fileIDs: Union[int, List]):
        """
        删除文件，将文件放入回收站中。

        :param fileIDs: 文件 ID 或者含有文件 ID 的列表。提供列表批量删除。
        :return: 服务器响应数据
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]

        response = self.request('post', self.baseurl.FILE_TRASH, {'fileIDs': fileIDs})

        data_response = DataResponse(response)

        return data_response

    def delete(self, fileIDs: Union[int, List]):
        """
        彻底删除文件。彻底删除文件前，文件必须要在回收站中（先使用 trash 方法），否则无法删除。

        :param fileIDs: 文件 ID 或者含有文件 ID 的列表。提供列表批量删除。
        :return: 服务器响应数据
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]

        response = self.request('post', self.baseurl.FILE_DELETE, {'fileIDs': fileIDs})

        data_response = DataResponse(response)

        return data_response

    def recover(self, fileIDs: Union[int, List]):
        """
        从回收站恢复文件。将回收站的文件恢复至删除前的位置。

        :param fileIDs: 文件 ID 或者含有文件 ID 的列表。提供列表批量删除。
        :return: 服务器响应数据
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]

        response = self.request('post', self.baseurl.FILE_DELETE, {'fileIDs': fileIDs})

        data_response = DataResponse(response)

        return data_response

    def move(self, fileIDs: Union[int, List], toParentFileID: int):
        """
        移动文件文件。

        :param fileIDs: 文件 ID 或者含有文件 ID 的列表。提供列表批量删除。
        :param toParentFileID: 要移动到的目标文件夹id，移动到根目录时填写 0。
        :return: 服务器响应数据
        """
        if isinstance(fileIDs, int):
            fileIDs = [fileIDs]

        response = self.request('post', self.baseurl.FILE_MOVE,
                                {'fileIDs': fileIDs, 'toParentFileID': toParentFileID})

        data_response = DataResponse(response)

        return data_response

    def mkdir(self, name: str, parentID: int):
        """
        创建目录。

        data 返回参数参考：

        +-------+--------+------+---------+
        | 名称    | 类型     | 是否必填 | 说明      |
        +=======+========+======+=========+
        | dirID | number | 必填   | 创建的目录ID |
        +-------+--------+------+---------+


        :param name: 目录名(注:不能重名)
        :param parentID: 父目录id，上传到根目录时填写 0
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_MKDIR,
                                {'name': name, 'parentID': parentID})

        data_response = DataResponse(response)

        return data_response

    @staticmethod
    def md5(filename_or_io):
        """
        内部方法，用于获取文件的 md5 。

        :param filename_or_io: 文件名或字节流对象，如果是字节流对象请手动将光标移动到开头。
        :return: 文件 md5 。
        """
        if isinstance(filename_or_io, str):
            f = open(filename_or_io, "rb")
        else:
            f = filename_or_io

        md5_hash = hashlib.md5()

        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)

        if isinstance(filename_or_io, str):
            f.close()

        return md5_hash.hexdigest()

    def create(self, parentFileID: int, filename: str, etag: str, size: int):
        """
        上传文件的过程方法，用于创建文件。

        返回数据参考：

        +-------------+---------+------+-----------------------------------------+
        | 名称          | 类型      | 是否必填 | 说明                                      |
        +=============+=========+======+=========================================+
        | fileID      | number  | 非必填  | 文件ID。当123云盘已有该文件,则会发生秒传。此时会将文件ID字段返回。唯一 |
        | preuploadID | string  | 必填   | 预上传ID(如果 reuse 为 true 时,该字段不存在)         |
        | reuse       | boolean | 必填   | 是否秒传，返回true时表示文件已上传成功                   |
        | sliceSize   | number  | 必填   | 分片大小，必须按此大小生成文件分片再上传                    |
        +-------------+---------+------+-----------------------------------------+


        :param parentFileID: 父文件夹
        :param filename: 文件名
        :param etag: 文件 md5
        :param size: 文件大小
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_CREATE,
                                {
                                    'parentFileID': parentFileID,
                                    'filename': filename,
                                    'etag': etag,
                                    'size': size
                                })

        data_response = DataResponse(response)

        return data_response

    def list_upload_parts(self, preuploadID: int):
        """
        上传文件的过程方法，用于罗列已上传文件部分。

        返回数据参考：

        +---------------------+--------+------+-------+
        | 名称                  | 类型     | 是否必填 | 说明    |
        +=====================+========+======+=======+
        | parts               | array  | 必填   | 分片列表  |
        | parts[*].partNumber | number | 必填   | 分片编号  |
        | parts[*].size       | number | 必填   | 分片大小  |
        | parts[*].etag       | string | 必填   | 分片md5 |
        +---------------------+--------+------+-------+


        :param preuploadID: 预上传ID。
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_LIST_UPLOAD_PARTS,
                                {'preuploadID': preuploadID})

        data_response = DataResponse(response)

        return data_response

    def get_upload_url(self, preuploadID: int, sliceNo: int):
        """
        上传文件的过程方法，获取上传地址。

        返回数据参考：

        +--------------+--------+------+------+
        | 名称           | 类型     | 是否必填 | 说明   |
        +==============+========+======+======+
        | presignedURL | string | 必填   | 上传地址 |
        +--------------+--------+------+------+

        :param preuploadID: 预上传ID。
        :param sliceNo: 分片序号，从1开始自增
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_GET_UPLOAD_URL,
                                {'preuploadID': preuploadID, 'sliceNo': sliceNo})

        data_response = DataResponse(response)

        return data_response

    def upload_complete(self, preuploadID: int):
        """
        上传文件的过程方法，上传文件完成请求。

        返回数据参考：

        +-----------+--------+------+----------------------------------------------------+
        | 名称        | 类型     | 是否必填 | 说明                                                 |
        +===========+========+======+====================================================+
        | fileID    | number | 非必填  | 当下方 completed 字段为true时,此处的 fileID 就为文件的真实ID(唯一)    |
        | async     | bool   | 必填   | 是否需要异步查询上传结果。false为无需异步查询,已经上传完毕。true 为需要异步查询上传结果。 |
        | completed | bool   | 必填   | 上传是否完成                                             |
        +-----------+--------+------+----------------------------------------------------+


        :param preuploadID: 预上传ID。
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_COMPLETE,
                                {'preuploadID': preuploadID})

        data_response = DataResponse(response)

        return data_response

    def upload_async_result(self, preuploadID: int):
        """
        上传文件的过程方法，上传文件完成请求。

        返回数据参考：

        +-----------+--------+------+------------------------------+
        | 名称        | 类型     | 是否必填 | 说明                           |
        +===========+========+======+==============================+
        | completed | bool   | 必填   | 上传合并是否完成,如果为false,请至少1秒后发起轮询 |
        | fileID    | number | 必填   | 上传成功的文件ID                    |
        +-----------+--------+------+------------------------------+



        :param preuploadID: 预上传ID。
        :return: 服务器响应数据
        """
        response = self.request('post', self.baseurl.FILE_UPLOAD_ASYNC_RESULT,
                                {'preuploadID': preuploadID})

        data_response = DataResponse(response)

        return data_response

    def upload(self, filename_or_io, upload_name, parentFileID, upload_method=None, callback=None):
        """
        上传文件。重名或其他问题会报错。 callback 返回 False 时，报错。

        :param filename_or_io: 文件名或字节流。
        :param upload_name: 上传的文件名。
        :param parentFileID: 上传的父目录ID。
        :param upload_method: 上传数据用的函数，默认采用 requests.post 。参考：
                            def upload_method(url, data):
                                 requests.put(url, data=data)
        :param callback: 函数回调，每次请求服务器时都会调用。callback(step, data_response, upload_progress)
                        step 是一个步骤标记， 0 -- 请求创建文件  1 -- 获取上传地址  2 -- 上传数据  3 -- 请求上传完成  4 -- 轮询查询上传是否完毕
                        upload_progress 参数是一个字典， 包含 sliceNo（当前部分） 、 sliceNo_all（全部部分）、uploaded_size （已上传大小） 、 total_size （总大小）
        :return: 上传成功，返回文件 ID 。否则返回 -1 。
        """
        if callback is None:
            def callback(*args):
                return True

        if upload_method is None:
            def upload_method(url, data):
                requests.put(url, data=data)

        if isinstance(filename_or_io, str):
            f = open(filename_or_io, "rb")
        else:
            f = filename_or_io

        f.seek(0)
        file_etag = self.md5(filename_or_io)
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)

        # 创建文件
        data_response = self.create(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size)

        if data_response.code != 0:
            raise ValueError(data_response.message)

        if data_response.data['reuse']:
            return data_response.data['fileID']

        preuploadID = data_response.data['preuploadID']
        sliceSize = data_response.data['sliceSize']

        # 计算上传次数
        total_sliceNo = file_size // sliceSize + bool(file_size % sliceSize)
        sliceNo = 1  # 从 1 开始自增

        # 统计已上传大小
        uploaded_size = 0

        assert callback(0, data_response, {"sliceNo": sliceNo, "sliceNo_total": total_sliceNo, "uploaded_size": 0,
                                           "total_size": file_size})

        while sliceNo <= total_sliceNo:
            data_response = self.get_upload_url(preuploadID, sliceNo)
            assert callback(1, data_response,
                            {"sliceNo": sliceNo, "sliceNo_total": total_sliceNo, "uploaded_size": uploaded_size,
                             "total_size": file_size})
            presignedURL = data_response.data['presignedURL']

            file_data = f.read(sliceSize)
            uploaded_size += len(file_data)
            upload_method(presignedURL, file_data)
            assert callback(2, data_response,
                            {"sliceNo": sliceNo, "sliceNo_total": total_sliceNo, "uploaded_size": uploaded_size,
                             "total_size": file_size})

            sliceNo += 1

        data_response = self.upload_complete(preuploadID)
        assert callback(3, data_response,
                        {"sliceNo": sliceNo, "sliceNo_total": total_sliceNo, "uploaded_size": uploaded_size,
                         "total_size": file_size})

        if data_response.data['completed']:
            return data_response.data['fileID']

        if data_response.data['async']:
            while True:
                time.sleep(1)
                data_response = self.upload_async_result(preuploadID)
                assert callback(4, data_response,
                                {"sliceNo": sliceNo, "sliceNo_total": total_sliceNo, "uploaded_size": uploaded_size,
                                 "total_size": file_size})

                if data_response.data['completed']:
                    return data_response.data['fileID']

        return -1

    def share(self, shareName: str, shareExpire: int, fileIDList: str, sharePwd=None) -> DataResponse:
        """
        创建分享链接。参见：https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced/dwd2ss0qnpab5i5s


        data 数据段是一个字典，键值如下：

        +----------+--------+------+----------------------------------------------------+
        | 名称       | 类型     | 是否必填 | 说明                                                 |
        +==========+========+======+====================================================+
        | shareID  | number | 必填   | 分享ID                                               |
        | shareKey | string | 必填   | 分享码,请将分享码拼接至 https://www.123pan.com/s/ 后面访问,即是分享页面 |
        +----------+--------+------+----------------------------------------------------+


        :param shareName: 分享链接
        :param shareExpire: 分享链接有效期天数,该值为枚举  固定只能填写:1、7、30、0  填写0时代表永久分享
        :param fileIDList: 分享文件ID列表,以逗号分割,最大只支持拼接100个文件ID,示例:1,2,3。如果你传入一个列表，则会自动拼接。
        :param sharePwd: 设置分享链接提取码
        :return: 服务器响应数据
        """

        if isinstance(fileIDList, list):
            fileIDList = [str(_) for _ in fileIDList]

        data = {
            'shareName': shareName,
            'shareExpire': shareExpire,
            'fileIDList': fileIDList
        }

        if sharePwd:
            data['sharePwd'] = sharePwd

        response = self.request('post', self.baseurl.SHARE_LINK_CREATE, data=data)

        data_response = DataResponse(response)

        return data_response
