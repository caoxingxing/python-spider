# -*- coding:utf-8 -*-
from contextlib import closing
import requests, json, re, os, sys, random
from ipaddress import ip_address
from subprocess import Popen, PIPE
import urllib

class DouYin(object):
	def __init__(self, width = 500, height = 300):
		"""
		抖音App视频下载
		"""
		rip = ip_address('.'.join(map(str, (random.randint(0, 255) for _ in range(4)))))
		while rip.is_private:
			rip = ip_address('.'.join(map(str, (random.randint(0, 255) for _ in range(4)))))
		self.headers = {
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
			'accept-encoding': 'gzip, deflate, br',
			'accept-language': 'zh-CN,zh;q=0.9',
			'cache-control': 'max-age=0',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Linux; U; Android 5.1.1; zh-cn; MI 4S Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.146 Mobile Safari/537.36 XiaoMi/MiuiBrowser/9.1.3',
			'X-Real-IP': str(rip),
			'X-Forwarded-For': str(rip),
		}

	def get_video_urls(self, user_id):
		"""
		获得视频播放地址
		Parameters:
			user_id：查询的用户ID
		Returns:
			video_names: 视频名字列表
			video_urls: 视频链接列表
			nickname: 用户昵称
		"""
		video_names = []
		video_urls = []
		share_urls = []
		unique_id = ''
		device_id = str(random.randint(3, 5)) + ''.join(map(str, (random.randint(0, 9) for _ in range(10))))
		search_url = 'https://api.amemv.com/aweme/v1/discover/search/?cursor=0&keyword={0}&count=10&type=1&retry_type=no_retry&device_id={1}&ac=wifi&channel=xiaomi&aid=1128&app_name=aweme&version_code=162&version_name=1.6.2&device_platform=android&ssmix=a&device_type=MI+5&device_brand=Xiaomi&os_api=24&os_version=7.0&manifest_version_code=162&resolution=1080*1920&dpi=480&update_version_code=1622'.format(user_id, device_id)
		req = requests.get(search_url, headers=self.headers)
		html = json.loads(req.text)
		aweme_count = 32767 # html['user_list'][0]['user_info']['aweme_count']
		uid = html['user_list'][0]['user_info']['uid']
		nickname = html['user_list'][0]['user_info']['nickname']
		unique_id = html['user_list'][0]['user_info']['unique_id']
		if unique_id != user_id:
			unique_id = html['user_list'][0]['user_info']['short_id']
			if unique_id != user_id:
				print('用户ID可能输入错误或无法搜索到此用户ID')
				sys.exit()
		share_user_url = 'https://www.amemv.com/share/user/%s' % uid
		share_user = requests.get(share_user_url, headers=self.headers)
		_dytk_re = re.compile(r"dytk: '(.+)'")
		dytk = _dytk_re.search(share_user.text).group(1)
		print('JS签名下载中')
		urllib.request.urlretrieve('https://github.com/Jack-Cherish/python-spider/blob/master/douyin/fuck-byted-acrawler.js', 'fuck-byted-acrawler.js')
		try:
			process = Popen(['node', 'fuck-byted-acrawler.js', str(uid)], stdout=PIPE, stderr=PIPE)
		except (OSError, IOError) as err:
			print('请先安装 node.js: https://nodejs.org/')
			sys.exit()
		sign = process.communicate()[0].decode().strip('\n')
		user_url = 'https://www.amemv.com/aweme/v1/aweme/post/?user_id=%s&max_cursor=0&count=%s&aid=1128&_signature=%s&dytk=%s' % (uid, aweme_count, sign, dytk)
		req = requests.get(user_url, headers=self.headers)
		html = json.loads(req.text)
		for each in html['aweme_list']:
			share_desc = each['share_info']['share_desc']
			if os.name == 'nt':
				for c in r'\/:*?"<>|':
					nickname = nickname.replace(c, '').strip()
					share_desc = share_desc.replace(c, '').strip()
			share_id = each['aweme_id']
			if share_desc in ['抖音-原创音乐短视频社区', 'TikTok']:
				video_names.append(share_id + '.mp4')
			else:
				video_names.append(share_id + '-' + share_desc + '.mp4')
			share_urls.append(each['share_info']['share_url'])
			video_urls.append(each['video']['play_addr']['url_list'][0])

		return video_names, video_urls, share_urls, nickname

	def get_download_url(self, video_url, watermark_flag):
		"""
		获得带水印的视频播放地址
		Parameters:
			video_url：带水印的视频播放地址
		Returns:
			download_url: 带水印的视频下载地址
		"""
		# 带水印视频
		if watermark_flag == True:
			download_url = video_url
		# 无水印视频
		else:
			download_url = video_url.replace('playwm', 'play')

		return download_url

	def video_downloader(self, video_url, video_name, watermark_flag=False):
		"""
		视频下载
		Parameters:
			video_url: 带水印的视频地址
			video_name: 视频名
			watermark_flag: 是否下载带水印的视频
		Returns:
			无
		"""
		size = 0
		video_url = self.get_download_url(video_url, watermark_flag=watermark_flag)
		with closing(requests.get(video_url, headers=self.headers, stream=True)) as response:
			chunk_size = 1024
			content_size = int(response.headers['content-length'])
			if response.status_code == 200:
				sys.stdout.write('  [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))

				with open(video_name, 'wb') as file:
					for data in response.iter_content(chunk_size = chunk_size):
						file.write(data)
						size += len(data)
						file.flush()

						sys.stdout.write('  [下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
						sys.stdout.flush()

	def run(self):
		"""
		运行函数
		Parameters:
			None
		Returns:
			None
		"""
		self.hello()
		user_id = input('请输入ID(例如145651081):')
		watermark_flag = int(input('是否下载带水印的视频(0-否,1-是):'))
		video_names, video_urls, share_urls, nickname = self.get_video_urls(user_id)
		if nickname not in os.listdir():
			os.mkdir(nickname)
		print('视频下载中:共有%d个作品!\n' % len(video_urls))
		for num in range(len(video_urls)):
			print('  解析第%d个视频链接 [%s] 中，请稍后!\n' % (num + 1, share_urls[num]))
			if '\\' in video_names[num]:
				video_name = video_names[num].replace('\\', '')
			elif '/' in video_names[num]:
				video_name = video_names[num].replace('/', '')
			else:
				video_name = video_names[num]
			if os.path.isfile(os.path.join(nickname, video_name)):
				print('视频已存在')
			else:
				self.video_downloader(video_urls[num], os.path.join(nickname, video_name), watermark_flag)
			print('\n')
		print('下载完成!')

	def hello(self):
		"""
		打印欢迎界面
		Parameters:
			None
		Returns:
			None
		"""
		print('*' * 100)
		print('\t\t\t\t抖音App视频下载小助手')
		print('\t\t作者:Jack Cui、steven7851')
		print('*' * 100)


if __name__ == '__main__':
	douyin = DouYin()
	douyin.run()
