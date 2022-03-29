import os
import re
import json
import requests
from tqdm import tqdm
from multiprocessing import Pool

from tqdm.std import trange


headers = {
    "Referer": "https://www.bilibili.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0"}


def get_home_text(bvid):
    # 通过访问视频主页 获取 (title, cover)
    # 参数 (bvid)
    bv_url = f"https://www.bilibili.com/video/{bvid}"
    return requests.get(bv_url, headers=headers).text


def get_title(bv_text):
    title = re.findall('<h1 title="(.*?)" class="video-title">', bv_text)[0]
    title = title.replace('/', '-')
    # 创建文件夹
    try:
        os.mkdir(title)
    except Exception:
        print("文件覆盖")
    # 修改工作路径
    os.chdir(title)

    return title


def save_cover(bv_text, title):
    # 获取封面地址
    cover_url = re.findall('"thumbnailUrl":\["(.*?)"\],', bv_text)[0]
    cover = requests.get(cover_url, headers=headers).content

    # 保存封面
    with open(title+",jpg", "wb") as f:
        f.write(cover)


def get_cid_list(bvid):
    # 1.通过api接口		获取  (cid)
    # 参数 (bvid)
    cid_api = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
    cid_json = requests.get(cid_api, headers=headers).text
    cid_list = re.findall('"cid":(.*?),', cid_json)

    # 返回数据
    return cid_list


def get_video_url(cid, bvid):
    # 1.通过api接口		获取视频链接
    # 参数 (cid, bvid)
    video_api = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}"
    video_json = requests.get(video_api, headers=headers).text
    video_url = json.loads(video_json)["data"]["durl"][0]["url"]

    # 返回视频链接
    return video_url


def parsing(cid_list, bvid):
    isTrue = False
    # 1.判断视频是 单P 还是 多P
    if len(cid_list) > 1:
        isTrue = True
    if len(cid_list) == 0:
        print("错误: cid获取失败")
        exit(-233)

    if isTrue:
        video = []
        for cid in cid_list:
            video.append(get_video_url(cid, bvid))
    else:
        video = get_video_url(cid_list[0], bvid)

    # 2.返回数据
    return video, isTrue


def save_process(url):
    print("headers")
    headers = {
        "Referer": "https://www.bilibili.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0"}
    title = os.getcwd().split('/')[-1]
    video = url.split('---')[0]
    i = url.split('---')[1]
    # 保存视频
    # 获取文件名
    print("video:", video)
    print('file_name', i)
    file_name = f"P{i} "+title+".mp4"
    # 请求文件流 返回响应
    response = requests.get(video, headers=headers, stream=True)
    # 获取文件大小
    file_size = response.headers["Content-length"]
    # 创建进度条对象
    with tqdm(total=int(file_size), desc=file_name, unit="b", unit_scale=True, leave=False) as pbar:
        # 打开文件写入
        with open(file_name, "wb") as f:
            # 迭代文件 每块1024 (b)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    # 写入块
                    f.write(chunk)
                    # 更新
                pbar.update(1024)


def save(title, video_url):
    file_name = title+".mp4"
    response = requests.get(video_url, headers=headers, stream=True)
    file_size = response.headers["Content-length"]
    pbar = tqdm(total=int(file_size), desc=file_name,
                unit="b", unit_scale=True, leave=False)
    with open(file_name, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()


if __name__ == "__main__":
    while 1:
        try:
            # 1.获取并取出 bv号
            text = input("请输入视频链接:")
            # 获取 bvid
            bvid = re.findall("(BV.{10})", text)[0]
            break

        except IndexError:
            print("输入链接有误")

    home_text = get_home_text(bvid)
    title = get_title(home_text)
    save_cover(home_text, title)
    # 获取 cid
    cid_list = get_cid_list(bvid)
    # 解析 视频地址
    video, isTrue = parsing(cid_list, bvid)
    # 保存
    if isTrue:
        for i in range(len(video)):
            video[i] = video[i]+f"---{i+1}"
        with Pool() as pool:
            pool.apply_async(save_process, video)
    else:
        save(title, video)
    print("下载完毕")
