# 一个简单的bilibili视频下载器
可以简单地下载各种b站视频,支持断点续传，分p下载

使用一个简单的命令就可轻松下载视频
## 安装
### 依赖
* python3
* ffmpeg

ffmpeg 需要添加到本地环境变量中


```console
pip install -r requirements.txt
```

### 开始
直接下载视频
```console
python bilibili.py https://www.bilibili.com/video/BV1Ra411R7kb/
```

下载所有多分P视频
```console
python bilibili.py --playlist https://www.bilibili.com/video/BV1Eb411u7Fw/
```

使用cookies
```console
python bilibili.py -b SESSDATA=xxxxx https://www.bilibili.com/video/BV1Eb411u7Fw/
```


也可以在config.json 里配置cookies
```json
{
    "cookies": {
        "SESSDATA":"xxxxxx"
    }
}

```

输入-h查看更多帮助
```console
python bilibili.py -h
```

