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
import urllib
import hashlib
from urlparse import urljoin, urlparse, parse_qsl, urlunparse
from urllib import urlencode
from lxml import etree
from datetime import datetime, timedelta
from scrapy_redis.spiders import RedisSpider
from scrapy.selector import Selector
from scrapy.http import Request
from sina_spider.items import TweetsItem, UserItem, RelationshipsItem, TweetsItemPics
from scrapy.shell import inspect_response
from weibo_ids import get_topic_urls


class Spider(RedisSpider):
    name = "SinaTopicSpider"
    host = "https://weibo.cn"
    redis_key = "SinaSpider:start_urls"
    start_urls = get_topic_urls()
    logging.getLogger("requests").setLevel(logging.WARNING)  # 将requests的日志级别设成WARNING

    def start_requests(self):
        for url in self.start_urls:
            pattern = 'https://m.weibo.cn/api/container/getIndex?from=feed&type=topic&value='
            name = re.findall(r'https://m.weibo.cn/k/(.*)\?from=feed', url)
            if name:
                newurl = pattern + name[0]
                yield Request(url=newurl, headers={'Referer':url}, callback=self.parse_information, meta={'seed':url})

    def parse_information(self, response):
        informationItem = UserItem()
        #inspect_response(response, self)
        dic = json.loads(response.body)
        pageinfo = dic.get('pageInfo', {})
        pageurl = pageinfo.get('page_url', '')
        if pageinfo and pageurl:
            informationItem['host'] = 'https://weibo.cn/topic'
            informationItem['name'] = pageinfo.get('page_title', '')
            informationItem['seed'] = response.meta.get('seed', '')
            informationItem['collectsCount'] = 0
            informationItem['pics'] = [{'href':pageinfo.get('portrait', ''), 'title':'', 'content':''}]
            if pageinfo.get('portrait', ''):
                informationItem['imageUrls'] = [pageinfo.get('portrait', '')]
            else:
                informationItem['imageUrls'] = []
            informationItem['url'] = pageurl
            informationItem['id'] = hashlib.sha1(pageurl).hexdigest()
            yield informationItem

        cardlist_head_cards = pageinfo.get('cardlist_head_cards', [{}])
        for head in cardlist_head_cards:
            channel_list = head.get('channel_list', [])
            for channel in channel_list:
                if channel.get('name', '') == u'精华':
                    containerid = channel.get('containerid', '')
                    #https://m.weibo.cn/api/container/getIndex?from=feed&type=topic&containerid=1008081e7b7e88c79b564b50d01cd209f89c85_-_soul&since_id=19
                    url_parts = list(urlparse(response.url))
                    query = dict(parse_qsl(url_parts[4]))
                    params = {'containerid':containerid, 'since_id':0}
                    query.update(params)
                    url_parts[4] = urlencode(query)
                    newurl = urlunparse(url_parts)
                    #informationItem 表的id作为tweets结构的srcid透传过去
                    yield Request(url=newurl,
                        headers={'Referer':response.url},
                        callback=self.parse_tweets,
                        meta={'srcid': informationItem['id'], 'since_id': 0})

    def parse_tweets(self, response):
        dic = json.loads(response.body)
        num = 0
        for bigcard in dic.get('cards', [{}]):
            cardgroup = bigcard.get('card_group', [{}])
            for card in cardgroup:
                cardtype = card.get('card_type', '')
                if cardtype == 9:
                    url = card.get('scheme', '')
                    mblog = card.get('mblog')
                    item = TweetsItem()
                    item['buff'] = {}
                    buff = item['buff']
                    #item['html'] = response.body
                    item['url'] = url
                    item['host'] = 'https://weibo.cn/topic'
                    item['pageid'] = mblog.get('id', '')
                    item['srcid'] = response.meta['srcid']
                    item['id'] = hashlib.sha1(item['srcid'] + item['url'] ).hexdigest()
                    item['rawTitle'] = mblog.get('text', '')
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
            url_parts = list(urlparse(response.url))
            query = dict(parse_qsl(url_parts[4]))
            since_id = response.meta.get('since_id', 0) + 20
            params = {'since_id':since_id - 1}
            query.update(params)
            url_parts[4] = urlencode(query)
            newurl = urlunparse(url_parts)
            print '*'*50, urllib.unquote(newurl)
            yield Request(url=newurl,
                        headers={'Referer':response.url},
                        callback=self.parse_tweets,
                        meta={'srcid': response.meta['srcid'], 'since_id': since_id})

        #yield Request(url="https://weibo.cn/%s/fans" % UID, callback=self.parse_relationship, dont_filter=True)

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


