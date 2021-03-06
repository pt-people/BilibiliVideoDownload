import requests
import re
import json
from tqdm import tqdm
import os


headers = {
	"Referer":"https://www.bilibili.com",
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0"
 }


def page_info(bvid):
	# 1.通过api接口		获取  (cid)
	# 参数 (bvid)
	cid_api = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
	cid_json = requests.get(cid_api).text
	cid_list = re.findall('"cid":(.*?),', cid_json)
    
	# 2.通过访问视频主页 获取 (title, cover)
	# 参数 (bvid)
	bv_url = f"https://www.bilibili.com/video/{bvid}"
	bv_json = requests.get(bv_url).text
	title = re.findall('"true">(.*?)_哔哩哔哩_bilibili</title>', bv_json)[0]
	title = title.replace('/', '-')
	cover_url = re.findall('"thumbnailUrl":\["(.*?)"\],', bv_json)[0]
	cover = requests.get(cover_url).content
	
	# 3.返回数据
	return {"title": title,"cover": cover, "cid_list": cid_list}


def get_video(cid, bvid):
	# 1.通过api接口		获取视频链接
	# 参数 (cid, bvid)
	video_api = f"https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}"
	video_json = requests.get(video_api).text
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
	
	# 判断是否是多P
	if isTrue:
		video = []
		for cid in cid_list:
			video.append(get_video(cid,bvid))
	else:
		video = get_video(cid_list[0], bvid)
		
	# 2.返回数据
	return video, isTrue


def save(title, cover, video_url, isTrue):
	os.mkdir(title)
	os.chdir("./"+title)
	
	# 保存封面
	with open(title+".jpg", "wb") as f:
		f.write(cover)
		
	# 保存视频	
	if (isTrue):
		for i in tqdm(range(len(video_url)), desc="视频列表"):
			# 获取文件名
			file_name = f"P{i+1} "+title+".mp4"
			# 请求文件流 返回响应
			response = requests.get(video_url[i],headers=headers, stream=True)
			# 获取文件大小
			file_size = response.headers["Content-length"]
			# 创建进度条对象
			pbar = tqdm(total=int(file_size), desc=file_name, unit="b", unit_scale=True, leave=False)	
			# 打开文件写入
			with open(file_name, "wb") as f:
				# 迭代文件 每块1024 (b)
				for chunk in response.iter_content(chunk_size=1024):
					if chunk:
						# 写入块
						f.write(chunk)
						# 更新
						pbar.update(1024)
			# 关闭进度条对象
			pbar.close()
	else:
			file_name = title+".mp4"
			response = requests.get(video_url,headers=headers, stream=True)
			file_size = response.headers["Content-length"]
			pbar = tqdm(total=int(file_size), desc=file_name, unit="b", unit_scale=True, leave=False)	
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
			
	# 获取 视频信息
	info = page_info(bvid)
	# 解析 视频地址
	video, isTrue = parsing(info["cid_list"], bvid)
	# 保存
	save(info["title"], info["cover"], video, isTrue)
	print("下载完毕")
	
