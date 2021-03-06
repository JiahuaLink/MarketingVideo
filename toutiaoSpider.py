# -*- coding: utf-8 -*-
import html
import os
import random
import re
import threading
import time
import urllib
from hashlib import md5

import requests
from fake_useragent import UserAgent
from lxml import etree

# 这里替换成你自己的浏览器信息
# user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'


class ToutiaoSpider():

    def __init__(self, keyword):
        self.keyword = keyword
        self.cookie = 'tt_webid=6822891653222827533; s_v_web_id=verify_k9s6hgsg_99WhK6ec_OthU_4AxT_BBjx_3GFEiKf2nYpl; WEATHER_CITY=%E5%8C%97%E4%BA%AC; __tasessionId=fe0xje8971588578269099; tt_webid=6822891653222827533; csrftoken=d452e4f78c502fc9d1281c858b7e8706; ttcid=1888a12680dc49d39526f10d5a95ed0c18; SLARDAR_WEB_ID=347731cd-27ab-45f9-87c2-9486a5786b15; passport_csrf_token=6b1ad1e0b94c87e64735242b8df85922; sso_uid_tt=fe204b41fe197707974efd1ca62bff4d; sso_uid_tt_ss=fe204b41fe197707974efd1ca62bff4d; toutiao_sso_user=ce59d36fe9800d2cbc5599a6cf49824f; toutiao_sso_user_ss=ce59d36fe9800d2cbc5599a6cf49824f; sid_guard=f5d43a55ea74bbf79b0c0d66e0308870%7C1588580928%7C5184000%7CFri%2C+03-Jul-2020+08%3A28%3A48+GMT; uid_tt=d209183682a69c92982a1a7a8b22365f; uid_tt_ss=d209183682a69c92982a1a7a8b22365f; sid_tt=f5d43a55ea74bbf79b0c0d66e0308870; sessionid=f5d43a55ea74bbf79b0c0d66e0308870; sessionid_ss=f5d43a55ea74bbf79b0c0d66e0308870; tt_scid=KOvQ4rR2Wda77zam6von5MoXRc7SHlbTSK2RoFBAcWLjkglytrS71FRFd5f5ZyhS2aa0'
    #
        self.root_dir = os.path.abspath('.')
        self.topic_path = os.path.join(self.root_dir, 'topics')
        self.copywriting_path = os.path.join(self.topic_path, keyword)
        self.headers = {
            'Host': 'www.toutiao.com',
            'Referer': 'https://www.toutiao.com/search/?keyword=' + urllib.parse.quote(keyword),
            'User-Agent':  UserAgent().random,
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': self.cookie
        }

        self.start_offset = 0
        # 获取的文案最大数量
        self.end_offset = 100
        # 20 20 增加
        self.step = 20

    # 根据偏移量获取每页文章列表
    def get_page_by_offset(self, offset):
        params = {
            'aid': '24',
            'app_name': 'web_search',
            'offset': offset,
            'format': 'json',
            'keyword': self.keyword,
            'autoload': 'true',
            'count': '20',
            'en_qc': '1',
            'cur_tab': '1',
            'from': 'search_tab',
            'pd': 'synthesis',
        }

        url = 'https://www.toutiao.com/api/search/content/?'

        resp = requests.get(url, headers=self.headers, params=params)
        if resp.status_code == 200:
            return resp.json()

    # 获取每篇文章的重定向链接

    def get_article_url(self, article):
        if article.get('data'):
            for item in article.get('data'):
                article_url = item.get('article_url')
                title = item.get('title')
                yield {
                    'article_url': article_url,
                    'title': title
                }

    # 将图片保存到文件
    def save2images(self, title, images_urls):

        root_dir = os.path.abspath('.')
        topic_path = os.path.join(
            self.topic_path, self.keyword, title)
        if not os.path.exists(topic_path):
            os.makedirs(topic_path)
        for url in images_urls:
            resp = requests.get(url)
            # print(url)
            file_name = os.path.join(topic_path, md5(
                resp.content).hexdigest() + '.jpg')

            if not os.path.exists(file_name):

                with open(file_name, 'wb') as f:
                    f.write(resp.content)
            else:
                print('Already Downloaded', file_name)

    # 将文案保存到文件
    def save2descripts(self, title, descript_texts):
        # print(descript_texts)
        topic_path = self.topic_path
        if not os.path.exists(topic_path):
            os.makedirs(topic_path)
        file_name = os.path.join(topic_path,title, title+'.txt')

        # if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            f.write(title+'\n')
            for raw_descript in descript_texts:
                # 数据清洗 去除<br> <strong> </strong>
                descript = re.sub(r'<.*?>|（.*?）', '', raw_descript)
                descript = re.sub(r'[，|。|；|？|......]', '\n', descript)
                descript = re.sub(r'[“|”|：|；|、]', '', descript)
                if descript:
                    print(descript)
                    try:
                        f.write(descript+'\n')
                    except:
                        pass
        # else:
        #     print('Description Already Write', file_name)

    # 获取每篇文章的图片和文案列表

    def get_article_info(self, article):
        article_url = article.get('article_url')
        title = article.get('title')

        if article_url:
            print("{} {}".format(title, article_url))
            # 这里需要使用session的方式，否则会因为重定向次数太多而报错
            session = requests.Session()
            session.headers['User-Agent'] = self.headers['User-Agent']
            try:
                resp = session.get(article_url)
            except requests.ConnectionError:
                print('{} ConnectionError'.format(article_url))
                # resp.encoding = resp.apparent_encoding
            if resp.status_code == 200:
                content = html.unescape(resp.text.encode(
                    'utf-8').decode('unicode_escape').encode('raw_unicode_escape').decode())
                # soup = BeautifulSoup(resp.text, 'lxml')
                # result = soup.find_all(name='script')[6]
                k = re.compile(
                    r'var BASE_DATA = (.*?);</script>', re.DOTALL)
                try:
                    infos = k.findall(content)[0]
                except Exception as e:
                    print("非头条链接{}".format(article_url))
                    return
                url_regex = r'<img src=\\"(.*?)\\" img_width'
                images_urls = re.findall(url_regex, infos, re.S)
                content_regex = r'<p>(.*?)</p>'
                descript_texts = re.findall(content_regex, infos, re.S)

                if images_urls:
                    self.save2images(title, images_urls)
                else:
                    print("获取不到图片")
                if descript_texts:
                    self.save2descripts(title, descript_texts)
                else:
                    print("获取不到文案")

    def run(self):
        for offset in range(self.start_offset, self.end_offset, self.step):
            article_list = self.get_page_by_offset(offset)
            for article in self.get_article_url(article_list):
                # 每篇文章单独起一个线程进行抓取
                t = threading.Thread(target=self.get_article_info(article))
                t.start()
                t.join()
                # self.get_article_info(article)
    # 随机选择文案  关键词  抽取的文章数量 抽取的段落总数量

    def random_chooose_descript(self, keyword, artileNum, paragrahNum):
        '''随机获取文案拼接'''
        descript = ''
        textlist = []
        paragrah_list = []
        fileList = os.listdir(os.path.join(self.topic_path, keyword))
        # 随机抽取文章篇数
        choose_files = random.sample(fileList, artileNum)
        for choose_file in choose_files:
            # print("随机选择文案："+choose_file)
            file = os.path.join(self.copywriting_path,
                                choose_file, choose_file+'.txt')
            
            paragrah_list = self.get_paragrah_list(file)
        if paragrah_list:
            textlist = random.sample(paragrah_list, paragrahNum)
            for text in textlist:
                # print("随机选择文案段落:"+text)
                descript += text
        print('==============合成文案==================\n'+descript)
        return descript

    def get_paragrah_list(self, file):
        paragraphs = []
        para = ''
        for num, line in enumerate(open(file, 'r')):
            if line:
                para += line
            if line == '\n':
                paragraphs.append(para)
                para = ''
        return paragraphs


if __name__ == '__main__':
    keyword = '罗志祥经常多人运动'
    # ToutiaoSpider(keyword).run()
    ToutiaoSpider(keyword).random_chooose_descript(keyword, 4, 1)

    print('========Done==========')
