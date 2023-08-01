import requests
import rich.progress 
import getopt
import re
import sys
import json
from rich import pretty
import os

pretty.install()


opts,args = getopt.getopt(sys.argv[1:],"hiq:b:o:",["help","info","playlist"])


if len(opts) == 0:
    raise Exception("没有指定参数")

info_mode = False

for opt in opts:
    if opt[0] == '-h' or opt[0] == '--help':
        print("""
Usage: python bili-dl.py [options] <url>
Options:
    -h, --help            显示帮助
    -i, --info            显示视频信息
    -q <qn>               指定视频质量
        [*]表示需要大会员
            qn=6  240P 极速
            qn=16 360P 流畅	
            qn=32 480P 清晰
            qn=64 720P 高清	
            qn=74 720P60 高帧率	
            qn=80 1080P 高清	
            qn=112 1080P+ 高码率*
            qn=116 1080P60 高帧率*
            qn=120 4K 超清*
            qn=125 HDR 真彩色*
            qn=126 杜比视界*
            qn=127 8K 超高清*
    -b <kv>               指定cookies
    -o <path>             指定输出路径
    --playlist            下载所有分P
              """)
        exit(0)
    if opt[0] == '-i' or opt[0] == '--info':
        info_mode = True
        break
    
if len(args) == 0:
    raise Exception("没有指定视频url")

#视频质量
qn = 127
for opt in opts:
    if opt[0] == '-q':
        qn = int(opt[1])
        break

#输出路径
output_path = "./"
for opt in opts:
    if opt[0] == '-o':
        output_path = opt[1]
        # if not os.path.isdir(output_path):
        #     raise Exception("输出路径不是文件夹")
        if output_path[-1] != '/':
            output_path += '/'
        break

if not os.path.exists(output_path):
    os.mkdir(output_path)


url = args[0]

pattern = r"^(https?://)?(www\.)?bilibili\.com/video/((bv|BV|Bv|bV|av|AV|aV|Av)([a-zA-Z0-9]+))"

url_match = re.match(pattern,url)


if url_match == None:
    raise Exception("url格式不正确")

p_pattern = r"p=(\d+)"
p_match =  re.search(p_pattern,url)

video_part = 1

if p_match:
    video_part = int(p_match.group(1))

video_id = url_match.group(3)

av_pattern = r"(av|Av|aV|AV)([0-9]+)"

av_match =  re.match(av_pattern,video_id)

is_av_mode = False

if av_match:
    video_id = av_match.group(2)
    is_av_mode = True


# -----apis-------
view_api = "https://api.bilibili.com/x/web-interface/view"

play_api = "https://api.bilibili.com/x/player/playurl"
# -----apis-------

#读取配置
config = None

with open("./config.json",'r') as f:
        config = json.load(f)

#配置cookies
cookies = {}

if config:
    cookies = config["cookies"]
# 用户传入的cookies覆盖配置文件中的cookies
for opt in opts:
    if opt[0] == '-b':
        kv = opt[1].split('=')
        if len(kv) != 2:
            raise Exception("cookies格式不正确")
        cookies[kv[0]] = kv[1]


#获取视频信息
view_params = {}
if is_av_mode:
    view_params["aid"] = video_id
else:
    view_params["bvid"] = video_id

print("正在获取视频信息...")

view_res = requests.get(view_api,params=view_params,cookies=cookies)

view_res.raise_for_status()

view_json = view_res.json()

if view_json["code"] != 0:
    raise Exception("获取视频信息失败",view_json["message"])

is_muti_part = len(view_json["data"]["pages"]) > 1

bvid = view_json["data"]["bvid"]

if info_mode:
    
    #获取视频下载地址
    play_params = {
        "bvid":bvid,
        "cid":view_json["data"]["cid"],
        "qn":qn,
        "fnval":4048,
        "fnver":0,
        "fourk":1,
        "voice_balance":0,
    }

    play_res = requests.get(play_api,params=play_params,cookies=cookies)

    play_res.raise_for_status()

    play_json = play_res.json()


    print("视频标题:",view_json["data"]["title"])
    print("视频作者:",view_json["data"]["owner"]["name"])
    print("视频BV号:",bvid)
    print("视频AV号:",view_json["data"]["aid"])
    print(">>>>>视频简介>>>>>)")
    print(view_json["data"]["desc"])
    print("<<<<<视频简介<<<<<")
    print()
    #视频时长 HH:MM:SS
    duration = int(view_json["data"]["duration"])
    duration_h = duration // 3600
    duration_m = (duration - duration_h * 3600) // 60
    duration_s = duration - duration_h * 3600 - duration_m * 60
    print("视频时长: %02d:%02d:%02d" % (duration_h,duration_m,duration_s))
    #可选分辨率
    print("-----可选分辨率-----")
    accept_description = play_json["data"]["accept_description"]
    accept_quality = play_json["data"]["accept_quality"]
    for i in range(len(accept_description)):
        print(accept_description[i],"  qn=","[",accept_quality[i],"]")

    print()
    if is_muti_part:
        print("视频分P数量:",view_json["data"]["videos"])
        print("-----视频分P列表-----")
        for page in view_json["data"]["pages"]:
            print("标题:","p"+str(page["page"]),page["part"])
            print("cid:",page["cid"])
            #视频时长 HH:MM:SS
            duration = int(page["duration"])
            duration_h = duration // 3600
            duration_m = (duration - duration_h * 3600) // 60
            duration_s = duration - duration_h * 3600 - duration_m * 60
            print("时长: %02d:%02d:%02d" % (duration_h,duration_m,duration_s))
            print()
    exit(0)

filter_file_name = lambda name: re.sub(r'[\/:*?"<>|]','-',name)

def download(url,name,type = 'video'):
    suffix = url.split('?')[0].split('.')[-1]
    headers = {
        "referer":"https://www.bilibili.com/",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    total_sizee = requests.head(url,headers=headers).headers['content-length']
    total_sizee = int(total_sizee)

    save_name = name + '.' + suffix
    progress_name = ""
    if type == 'video':
        save_name += '.vpart'
        progress_name = '[视频]'+name

    if type == 'audio':
        save_name += '.apart'
        progress_name = '[音频]'+name

    save_path = output_path + save_name

    if os.path.exists(save_path):
        #获取已下载的文件大小
        downloaded_size = os.path.getsize(save_path)
        if downloaded_size == total_sizee:
            with rich.progress.Progress() as progress :
                task = progress.add_task(progress_name,total=total_sizee)
                progress.update(task,advance=downloaded_size)
            return save_name
        else:
            #继续下载
            headers['Range'] = 'bytes=%d-' % downloaded_size
            with open(save_path,'ab') as f \
                , requests.get(url,stream=True,headers=headers) as r \
                , rich.progress.Progress() as progress :
                r.raise_for_status()
                task = progress.add_task(progress_name,total=total_sizee)
                progress.update(task,advance=downloaded_size)
                for content in r.iter_content(chunk_size=8096):
                    f.write(content)
                    progress.update(task,advance=len(content))
    else:
        with open(save_path,'wb') as f \
            , requests.get(url,stream=True,headers=headers) as r \
            , rich.progress.Progress() as progress :
            r.raise_for_status()
            task = progress.add_task(progress_name,total=total_sizee)

            for content in r.iter_content(chunk_size=8096):
                f.write(content)
                progress.update(task,advance=len(content))
    return save_path


def download_video(name,bvid,cid):
    video_name = filter_file_name(name)
    save_path = output_path + video_name + '.mp4'

    if os.path.exists(save_path):
        print(video_name+" >>> "+"已下载")
        return
    #获取视频下载地址
    play_params = {
        "bvid":bvid,
        "cid":cid,
        "qn":qn,
        "fnval":4048,
        "fnver":0,
        "fourk":1,
        "voice_balance":0,
    }

    print("正在获取视频下载地址...")

    play_res = requests.get(play_api,params=play_params,cookies=cookies)

    play_res.raise_for_status()

    play_json = play_res.json()

    video_urls = play_json["data"]["dash"]["video"]
    audio_urls = play_json["data"]["dash"]["audio"]

    video_url = video_urls[0]["baseUrl"]
    audio_url = audio_urls[0]["baseUrl"]

    for video in video_urls:
        if video["id"] == qn:
            video_url = video["baseUrl"]
            break

    if play_json["code"] != 0:
        raise Exception("获取视频下载地址失败",play_json["message"])

    saved_video_name = download(video_url,video_name)
    saved_audio_name = download(audio_url,video_name,'audio')

    

    print("合并音视频...")
    os.system("ffmpeg -hide_banner -loglevel error -i \"%s\" -i \"%s\" -c:v copy -c:a copy \"%s\"" % (saved_audio_name,saved_video_name,save_path))
    os.remove(saved_video_name)
    os.remove(saved_audio_name)
    print(video_name+" >>> "+"下载完成")

video_name = view_json["data"]["title"] + "["+bvid + "]"

if is_muti_part:
    is_playlist_mode = False
    for opt in opts:
        if opt[0] == '--playlist':
            is_playlist_mode = True

    if is_playlist_mode:
        print("正在下载所有分P...")
        pages = view_json["data"]["pages"]
        for page in pages:
            cid = page["cid"]
            part_name = video_name + "-"+"p"+str(page["page"])+"-"+page["part"]
            download_video(part_name,bvid,cid)
        print("所有分P下载完成")
        
    else:
        print("视频有多个分P 使用--playlist参数下载所有分P")
        pages = view_json["data"]["pages"]

        if video_part > len(pages):
            raise Exception("分P不存在")
        
        current_page =  pages[video_part-1]
        cid = current_page["cid"]
        part_name = video_name + "-"+"p"+str(video_part)+"-"+current_page["part"]

        download_video(part_name,bvid,cid)

else:
    download_video(video_name,bvid,view_json["data"]["cid"])
