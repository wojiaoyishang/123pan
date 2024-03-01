# 123云盘开放平台 123云盘直链鉴权 Python 代码示例

#### 介绍
123云盘开放平台和123云盘直链鉴权示例。注意：此仓库并非官方仓库，详细说明请查看下方链接：

+ 官方的开放平台文档：[https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced](https://123yunpan.yuque.com/org-wiki-123yunpan-muaork/cr6ced)
+ 官方直链鉴权：[https://www.123pan.com/faq?problem=dev_guide](https://www.123pan.com/faq?problem=dev_guide)
+ 123pan 官方 gitee 账号：[https://gitee.com/pan123-git](https://gitee.com/pan123-git)

代码中的URL鉴权来自：[https://gitee.com/pan123-git/123pan-link/issues/I7QXI8](https://gitee.com/pan123-git/123pan-link/issues/I7QXI8)

#### 使用示例
***注：由于 Python 等其它编程语言不支持数字开头的模块（变量）名，所以代码中的所有关于“123pan”的字段，均使用“pan123”来称呼。**

+ 直链鉴权示例

```python
from pan123 import get_direct_signed_link

# 待签名URL
origin_url = 'http://vip.123pan.com/10/layout1/layout2/%E6%88%91.txt'
# 鉴权密钥
primary_key = 'mykey'
# 账号id
uid = 10
# 防盗链过期时间间隔(秒)，60秒会导致链接失效
expire_time_sec = 3 * 60
url = get_direct_signed_link(origin_url, uid, primary_key, expire_time_sec)
```

+ 开发平台示例

初始化：

```python
from pan123 import pan123openAPI

# 自动获取 access_token
pan123 = pan123openAPI("your clientID", "your clientSecret")
pan123.refresh_access_token()

# 手动设置 access_token
pan123 = pan123openAPI()
pan123.refresh_access_token("your access token")
```

获取服务器信息：

```python
# 请求获取
data = pan123.refresh_access_token().data
print(data['accessToken'])  # eyJhb...
print(data['expiredAt'])  # 2024-03-22T19:52:23+08:00
```

***此处不一一列举，代码中有非常详尽的注释。***