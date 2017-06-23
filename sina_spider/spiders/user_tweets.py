# encoding=utf-8
# ------------------------------------------
#   版本：3.0
#   日期：2016-12-01
#   作者：九茶<http://blog.csdn.net/bone_ace>
# ------------------------------------------
import os
import sys
import logging
import requests
import re
import json
import hashlib
from urlparse import urljoin
from lxml import etree
from datetime import datetime, timedelta
from scrapy_redis.spiders import RedisSpider
from scrapy.selector import Selector
from scrapy.http import Request
from sina_spider.items import TweetsItem, UserItem, RelationshipsItem, TweetsItemPics
from scrapy.shell import inspect_response
from weibo_ids import get_user_urls


class Spider(RedisSpider):
    name = "SinaUserSpider"
    host = "https://weibo.cn"
    redis_key = "SinaSpider:start_urls"
    start_urls = get_user_urls()
    logging.getLogger("requests").setLevel(logging.WARNING)  # 将requests的日志级别设成WARNING

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, headers={'Referer':self.host}, callback=self.parse_uid, meta={'expires': 1})

    def parse_uid(self, response):
        informationItem = UserItem()
        #inspect_response(response, self)
        selector = Selector(response)
        user_info = selector.xpath(u'body/div[@class="u"]//div[@class="ut"]/a[text()="资料"]/@href').extract()
        if user_info:
            user_info_url = urljoin(response.url, user_info[0])
            yield Request(url=user_info_url, headers={'Referer':response.url}, callback=self.parse_user_info, meta={'seed':response.url, 'expires':1})

    def parse_user_info(self, response):
        """ 抓取个人信息 """
        informationItem = UserItem()
        selector = Selector(response)
        UID = re.findall('(\d+)/info', response.url)[0]
        #inspect_response(response, self)
        try:
        #if True:
            text1 = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())  # 获取标签里的所有text()
            pic = selector.xpath(u'body/div[@class="c"]//img[@alt="头像"]/@src').extract()
            nickname = re.findall(u'昵称[：:]?(.*?);', text1)
            gender = re.findall(u'性别[：:]?(.*?);', text1)
            place = re.findall(u'地区[：:]?(.*?);', text1)
            briefIntroduction = re.findall(u'简介[：:]?(.*?);', text1)
            birthday = re.findall(u'生日[：:]?(.*?);', text1)
            sexOrientation = re.findall(u'性取向[：:]?(.*?);', text1)
            sentiment = re.findall(u'感情状况[：:]?(.*?);', text1)
            vipLevel = re.findall(u'会员等级[：:]?(.*?);', text1)
            authentication = re.findall(u'认证[：:]?(.*?);', text1)
            url = re.findall(u'互联网[：:]?(.*?);', text1)

            informationItem['buff'] = {}
            informationItem['host'] = 'https://weibo.cn/user'
            buff = informationItem['buff']
            if url:
                informationItem['url'] = url[0]
            if pic and pic[0]:
                informationItem['pics'] = [{'href':pic[0], 'title':'', 'content':''}]
                informationItem['imageUrls'] = [pic[0]]
            informationItem['id'] = hashlib.sha1(informationItem['url']).hexdigest()
            informationItem['seed'] = response.meta['seed']
            if nickname and nickname[0]:
                informationItem['name'] = nickname[0].strip()
            try:
                if gender and gender[0]:
                    buff['gender'] = gender[0].replace(u"\xa0", "")
                if place and place[0]:
                    place = place[0].replace(u"\xa0", "").split(" ")
                    buff['province'] = place[0]
                    if len(place) > 1:
                        buff['city'] = place[1]
                if briefIntroduction and briefIntroduction[0]:
                    buff['briefIntroduction'] = briefIntroduction[0].replace(u"\xa0", "")
                if birthday and birthday[0]:
                    try:
                        birthday = datetime.strptime(birthday[0], "%Y-%m-%d")
                        buff['birthday'] = str(birthday - timedelta(hours=8))
                    except Exception:
                        buff['birthday'] = str(birthday[0])   # 有可能是星座，而非时间
                if sexOrientation and sexOrientation[0]:
                    if sexOrientation[0].replace(u"\xa0", "") == gender[0]:
                        buff['sexOrientation'] = u'同性恋'
                    else:
                        buff['sexOrientation'] = u'异性恋'
                if sentiment and sentiment[0]:
                    buff['sentiment'] = sentiment[0].replace(u"\xa0", "")
                if vipLevel and vipLevel[0]:
                    buff["VIPlevel"] = vipLevel[0].replace(u"\xa0", "")
                if authentication and authentication[0]:
                    buff['authentication'] = authentication[0].replace(u"\xa0", "")
            except:
                pass
            try:
                urlothers = "https://weibo.cn/attgroup/opening?uid=%s" % UID
                r = requests.get(urlothers, cookies=response.request.cookies, timeout=5)
                if r.status_code == 200:
                    selector = etree.HTML(r.content)
                    texts = ";".join(selector.xpath('//body//div[@class="tip2"]/a//text()'))
                    if texts:
                        num_tweets = re.findall(u'微博\[(\d+)\]', texts)
                        num_follows = re.findall(u'关注\[(\d+)\]', texts)
                        num_fans = re.findall(u'粉丝\[(\d+)\]', texts)
                        if num_tweets:
                            buff["numTweets"] = int(num_tweets[0])
                        if num_follows:
                            buff["numFollows"] = int(num_follows[0])
                        if num_fans:
                            buff["numFans"] = int(num_fans[0])
                            informationItem['collectsCount'] = int(num_fans[0])
            except Exception, e:
                pass
        except Exception, e:
            print '*'*20, e, UID
        else:
            yield informationItem
            yield Request(url='https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s' % (UID, UID),
                    headers={'Referer':response.url},
                    callback=self.parse_get_index,
                    meta={'srcid': informationItem['id'], 'expires':3600})
        #yield Request(url="https://weibo.cn/%s/profile?filter=1&page=1" % UID, callback=self.parse_tweets, dont_filter=True)
        #yield Request(url="https://weibo.cn/%s/follow" % UID, callback=self.parse_relationship, dont_filter=True)
        #yield Request(url="https://weibo.cn/%s/fans" % UID, callback=self.parse_relationship, dont_filter=True)

    def parse_get_index(self, response):
        #inspect_response(response, self)
        dic = json.loads(response.body)
        if 'tabsInfo' not in dic:
            return
        tabs = dic['tabsInfo']['tabs']
        containerid = ''
        for tab in tabs:
            if tab['title'] == u'微博':
                containerid = tab['containerid']
                break
        #https://m.weibo.cn/api/container/getIndex?uid=1750270991&luicode=20000174&featurecode=20000320&type=uid&value=1750270991&containerid=1076031750270991&page=2
        if containerid:
            page = 1
            yield Request(url='%s&containerid=%s&page=%d' % (response.url, containerid, page),
                    headers={'Referer':response.url},
                    callback=self.parse_weibo_list,
                    meta={'srcid': response.meta['srcid'], 'page': page, 'expires':3600})

    def strptime(self, timestr):
        m = re.findall(u'(\d+)秒前', timestr)
        tm = None
        if m:
            tm = datetime.now() - timedelta(seconds=int(m[0]))
        else:
            m = re.findall(u'(\d+)分钟前', timestr)
            if m:
                tm = datetime.now() - timedelta(seconds=int(m[0])*60)
            else:
                m = re.findall(u'(\d+)小时', timestr)
                if m:
                    tm = datetime.now() - timedelta(seconds=int(m[0])*60*60)
        if not m:
            timestr = timestr.replace(u'今天', datetime.now().strftime('%F'))
            if len(timestr) > 11:
                tm = datetime.strptime(timestr, '%Y-%m-%d %H:%S')
            else:
                tm = datetime.strptime(timestr, '%m-%d %H:%S').replace(datetime.now().year)
        return tm.strftime('%s')

    def get_ori_pics(self, mblog, key='pics'):
        oriPics = []
        for pic in mblog.get(key, []):
            oripic = {}
            oripic['title'] = ''
            oripic['content'] = ''
            oripic['href'] = pic.get('large', {}).get('url', '')
            oriPics.append(oripic)
        return oriPics

    def get_pics(self, mblog, key='pics'):
        pics = []
        for pic in mblog.get(key, []):
            oripic = {}
            oripic['title'] = ''
            oripic['content'] = ''
            oripic['href'] = pic.get('url', '')
            pics.append(oripic)
        return pics

    def get_videos(self, mblog, key='page_info'):
        pageinfo = mblog.get(key, {})
        if pageinfo.get('type', '') == 'video':
            videoinfo = {}
            videoinfo['title'] = pageinfo.get('page_title', '')
            videoinfo['href'] = pageinfo.get('media_info', {}).get('stream_url', '')
            videoinfo['content'] = pageinfo.get('content2', '')
            return [videoinfo]
        else:
            return []

    def get_video_pics(self, mblog, key='page_info'):
        pageinfo = mblog.get(key, {})
        if pageinfo.get('type', '') == 'video':
            videoPic = {}
            videoPic['title'] = ''
            videoPic['content'] = ''
            videoPic['href'] = pageinfo.get('page_pic', {}).get('url', '')
            return [videoPic]
        else:
            return []

    def parse_weibo_list(self, response):
        dic = json.loads(response.body)
        num = 0
        for i, card in enumerate(dic['cards']):
            if i == 0 and card.get('title', {}).get('text', '') == u'置顶':
                continue
            item = TweetsItem()
            card_type = card.get('card_type', 0)
            if card_type != 9:
                continue
            url = card.get('scheme', '')
            if not url:
                continue
            mblog = card['mblog']
            item['buff'] = {}
            buff = item['buff']
            #item['html'] = response.body
            item['host'] = 'https://weibo.cn/user'
            item['url'] = url
            item['srcid'] = response.meta['srcid']
            item['id'] = hashlib.sha1(item['srcid'] + item['url']).hexdigest()
            item['pageid'] = mblog['id']
            item['rawTitle'] = mblog.get('raw_text', '')
            item['title'] = ' '.join(Selector(text=mblog.get('text', '')).xpath('//text()').extract()) if mblog.get('text', '') else ''
            created_at = mblog.get('created_at', '')
            item['releaseTime'] = self.strptime(created_at)
            item['repostsCount'] = mblog.get('reposts_count', '')
            item['commentsCount'] = mblog.get('comments_count', '')
            item['attitudesCount'] = mblog.get('attitudes_count', '')
            buff['source'] = mblog.get('source', '')
            buff['pageInfo'] = mblog.get('page_info', {}) or mblog.get('pageInfo', {})
            item['oriPics'] = self.get_ori_pics(mblog)
            item['pics'] = self.get_pics(mblog)
            item['videos'] = self.get_videos(mblog)
            item['videoPics'] = self.get_video_pics(mblog)
            #转发的微博
            if 'retweeted_status' in mblog:
                retweet = mblog['retweeted_status']
                item['rawTitle'] += ' ' + retweet.get('text', '')
                item['title'] += ' ' + ' '.join(Selector(text=retweet.get('text', '')).xpath('//text()').extract()) if retweet.get('text', '') else ''
                item['pics'] += self.get_pics(retweet)
                item['oriPics'] += self.get_ori_pics(retweet)
                item['videos'] += self.get_videos(retweet, 'page_info') or self.get_videos(retweet, 'pageInfo')
                item['videoPics'] += self.get_video_pics(retweet, 'page_info') or self.get_video_pics(retweet, 'pageInfo')
                buff['pageInfo'] = retweet.get('page_info', {}) or retweet.get('pageInfo', {})
            image_urls = []
            for pic in item['oriPics'] + item['pics'] + item['videoPics']:
                href = pic.get('href', '')
                if not href:
                    continue
                image_urls.append(href)
            file_urls = []
            for video in item['videos']:
                href = video.get('href', '')
                if not href:
                    continue
                file_urls.append(href)
            item['imageUrls'] = image_urls
            #item['fileUrls'] = file_urls
            item['fileUrls'] = [] #视频先不下载了
            num += 1
            yield item
        if num > 0:
            oripage = response.meta['page']
            page = oripage + 1
            url = response.url.replace('page=%d' % oripage, 'page=%d' % page)
            yield Request(url=url,
                    headers={'Referer':response.url},
                    callback=self.parse_weibo_list,
                    meta={'srcid': response.meta['srcid'], 'page': page})

    def parse_tweets(self, response):
        """ 抓取微博数据 """
        selector = Selector(response)
        UID = re.findall('(\d+)/profile', response.url)[0]
        divs = selector.xpath('body/div[@class="c" and @id]')
        for div in divs:
            try:
                tweetsItems = TweetsItem()
                TID = div.xpath('@id').extract_first()  # 微博ID
                content = div.xpath('div/span[@class="ctt"]//text()').extract()  # 微博内容
                #图片
                pic = div.xpath('div/a/img[@class="ib"]/@src').extract()
                #原图
                oripic = div.xpath(u'div/a[text()="原图"]/@href').extract()
                #组图
                picall = div.xpath(u'div/a[contains(text(), "组图")]/@href').extract()
                cooridinates = div.xpath('div/a/@href').extract()  # 定位坐标
                like = re.findall(u'赞\[(\d+)\]', div.extract())  # 点赞数
                transfer = re.findall(u'转发\[(\d+)\]', div.extract())  # 转载数
                comment = re.findall(u'评论\[(\d+)\]', div.extract())  # 评论数
                others = div.xpath('div/span[@class="ct"]/text()').extract()  # 求时间和使用工具（手机或平台）

                tweetsItems["_id"] = UID + "-" + TID
                tweetsItems["UID"] = UID
                if pic:
                    tweetsItems['Pic'] = pic[0]
                if oripic:
                    tweetsItems['Oripic'] = oripic[0]
                if content:
                    tweetsItems["Content"] = " ".join(content).strip(u'[位置]')  # 去掉最后的"[位置]"
                if cooridinates:
                    cooridinates = re.findall('center=([\d.,]+)', cooridinates[0])
                    if cooridinates:
                        tweetsItems["Co_oridinates"] = cooridinates[0]
                if like:
                    tweetsItems["Like"] = int(like[0])
                if transfer:
                    tweetsItems["Transfer"] = int(transfer[0])
                if comment:
                    tweetsItems["Comment"] = int(comment[0])
                if others:
                    others = others[0].split(u'来自')
                    tweetsItems["PubTime"] = others[0].replace(u"\xa0", "")
                    if len(others) == 2:
                        tweetsItems["Tools"] = others[1].replace(u"\xa0", "")
                yield tweetsItems
                if picall:
                    yield Request(url=picall[0] + '&uid=%s' % UID, headers={'Referer':response.url}, callback=self.parse_picall)
            except Exception, e:
                print e
                pass

        url_next = selector.xpath(u'body/div[@class="pa" and @id="pagelist"]/form/div/a[text()="下页"]/@href').extract()
        if url_next:
            yield Request(url=self.host + url_next[0], headers={'Referer':response.url}, callback=self.parse_tweets, dont_filter=True)

    def parse_picall(self, response):
        #inspect_response(response, self)
        selector = Selector(response)
        hrefs = selector.xpath(u'body/div[@class="c"]/a/img/@src').extract()
        orihrefs = selector.xpath(u'body/div[@class="c"]/a[text()="原图"]/@href').extract()
        item = TweetsItemPics()
        TID, UID = re.findall('https://weibo.cn/mblog/picAll/(\w+)?.*uid=(\d+)', response.url)[0]
        item['_id'] = UID + '-' + TID
        item['UID'] = UID
        item['Picall'] = hrefs
        item['Oripicall'] = [urljoin(self.host, x) for x in orihrefs]
        return item

    def parse_relationship(self, response):
        """ 打开url爬取里面的个人ID """
        selector = Selector(response)
        if "/follow" in response.url:
            ID = re.findall('(\d+)/follow', response.url)[0]
            flag = True
        else:
            ID = re.findall('(\d+)/fans', response.url)[0]
            flag = False
        urls = selector.xpath(u'//a[text()="关注他" or text()="关注她"]/@href').extract()
        uids = re.findall('uid=(\d+)', ";".join(urls), re.S)
        for uid in uids:
            relationshipsItem = RelationshipsItem()
            relationshipsItem["Host1"] = ID if flag else uid
            relationshipsItem["Host2"] = uid if flag else ID
            yield relationshipsItem
            yield Request(url="https://weibo.cn/%s/info" % uid, callback=self.parse_user_info)

        next_url = selector.xpath(u'//a[text()="下页"]/@href').extract()
        if next_url:
            yield Request(url=self.host + next_url[0], callback=self.parse_relationship, dont_filter=True)
