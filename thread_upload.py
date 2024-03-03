import time
import requests
from concurrent.futures import ThreadPoolExecutor, wait
from pan123 import pan123openAPI


pan123 = pan123openAPI("your clientID", "your clientSecret")
pan123.refresh_access_token()
task_upload_per = []


def upload(filename, upload_name, parentFileID):
    """
    上传文件。重名或其他问题会报错。 callback 返回 False 时，报错。

    :param filename: 文件名。
    :param upload_name: 上传的文件名。
    :param parentFileID: 上传的父目录ID。
    :return: 上传成功，返回文件 ID 。否则返回 -1 。
    """

    f = open(filename, "rb")
    file_etag = pan123.file.md5(f)
    f.seek(0, 2)
    file_size = f.tell()
    f.seek(0)

    # 创建文件
    data_response = pan123.file.create(parentFileID=parentFileID, filename=upload_name, etag=file_etag, size=file_size)

    if data_response.code != 0:
        raise ValueError(data_response.message)

    if data_response.data['reuse']:
        return data_response.data['fileID']

    preuploadID = data_response.data['preuploadID']
    sliceSize = data_response.data['sliceSize']

    # 计算上传次数
    total_sliceNo = file_size // sliceSize + bool(file_size % sliceSize)
    sliceNo = 1  # 从 1 开始自增

    with ThreadPoolExecutor(max_workers=2) as t:
        task_list = []

        while sliceNo <= total_sliceNo:
            time.sleep(1)

            start_seek = f.tell()
            if start_seek + sliceSize > file_size:
                f.seek(0, 2)
            else:
                f.seek(sliceSize, 1)
            end_seek = f.tell()
            # print(start_seek, end_seek)
            task_upload_per.append(0)
            task_list.append(
                t.submit(upload_file_data, filename, preuploadID, start_seek, end_seek - start_seek, sliceNo - 1))

            sliceNo += 1
        while True:
            print("\r文件上传进度：", task_upload_per, end="")
            if len(wait(task_list, timeout=1).done) == len(task_list):
                print()
                break

    data_response = pan123.file.upload_complete(preuploadID)

    if data_response.data['completed']:
        return data_response.data['fileID']

    if data_response.data['async']:
        while True:
            time.sleep(1)
            data_response = pan123.file.upload_async_result(preuploadID)

            if data_response.data['completed']:
                return data_response.data['fileID']

    return -1


class upload_in_chunks(object):
    def __init__(self, fp, length, id, chunksize=1 << 13):
        self.fp = fp
        self.id = id
        self.chunksize = chunksize
        self.totalsize = length
        self.readsofar = 0

    def __iter__(self):
        while True:
            if self.readsofar + self.chunksize >= self.totalsize:
                data = self.fp.read(self.totalsize - self.readsofar)
            else:
                data = self.fp.read(self.chunksize)
            if not data:
                break
            yield data
            self.readsofar += len(data)
            task_upload_per[self.id] = self.readsofar * 1e2 / self.totalsize
            if self.readsofar >= self.totalsize:
                break

    def __len__(self):
        return self.totalsize


def upload_file_data(filename, preuploadID, start_seek, length, id):
    """分片段上传"""
    with open(filename, "rb") as f:
        while True:
            data_response = pan123.file.get_upload_url(preuploadID, id+1)
            presignedURL = data_response.data['presignedURL']
            f.seek(start_seek)
            try:
                requests.put(presignedURL, data=upload_in_chunks(f, length, id, chunksize=1024), timeout=60)
                break
            except requests.exceptions.RequestException:
                continue
