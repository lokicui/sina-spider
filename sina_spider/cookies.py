#encoding=utf-8
# ------------------------------------------
#   版本：3.0
#   日期：2016-12-01
#   作者：九茶<http://blog.csdn.net/bone_ace>
# ------------------------------------------

import os
import time
import json
import pdb
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from yumdama import identify
from weibo_ids import myWeiBo
IDENTIFY = 1  # 验证码输入方式:        1:看截图aa.png，手动输入     2:云打码
dcap = dict(DesiredCapabilities.PHANTOMJS)  # PhantomJS需要使用老版手机的user-agent，不然验证码会无法通过
dcap["phantomjs.page.settings.userAgent"] = (
    "Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
)
logger = logging.getLogger(__name__)
#logger = logging.getLogger()
#handler = logging.StreamHandler()
#formatter = logging.Formatter(
#        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)
#logger.setLevel(logging.DEBUG)
logging.getLogger("selenium").setLevel(logging.WARNING)  # 将selenium的日志级别设成WARNING，太烦人

"""
    输入你的微博账号和密码，可去淘宝买，一元5个。
    建议买几十个，实际生产建议100+，微博反爬得厉害，太频繁了会出现302转移。
"""


def getCookie(account, password):
    """ 获取一个账号的Cookie """
    #try:
    if True:
        browser = webdriver.PhantomJS(desired_capabilities=dcap)
        #browser.get("https://weibo.cn/login/")
        browser.get('https://passport.weibo.cn/signin/login')
        time.sleep(1)

        failure = 0
        while u'登录' in browser.title and failure < 5:
            failure += 1
            browser.save_screenshot("aa.png")
            #username = browser.find_element_by_name("mobile")
            username = browser.find_element_by_id("loginName")
            username.clear()
            username.send_keys(account)

            #psd = browser.find_element_by_xpath('//input[@type="password"]')
            try:
                psd = browser.find_element_by_id('loginPassword')
                psd.clear()
                psd.send_keys(password)
                code = browser.find_element_by_name("code")
                code.clear()
                if IDENTIFY == 1:
                    code_txt = raw_input(u"请查看路径下新生成的aa.png，然后输入验证码:")  # 手动输入验证码
                else:
                    from PIL import Image
                    img = browser.find_element_by_xpath('//form[@method="post"]/div/img[@alt="请打开图片显示"]')
                    x = img.location["x"]
                    y = img.location["y"]
                    im = Image.open("aa.png")
                    im.crop((x, y, 100 + x, y + 22)).save("ab.png")  # 剪切出验证码
                    code_txt = identify()  # 验证码打码平台识别
                code.send_keys(code_txt)
            except Exception, e:
                pass

            #commit = browser.find_element_by_name("submit")
            commit = browser.find_element_by_id("loginAction")
            commit.click()
            time.sleep(3)
            if u'随时随地发现新鲜事' not in browser.title:
                time.sleep(4)
            if u'未激活微博' in browser.page_source:
                print u'账号未开通微博'
                return {}

        cookie = {}
        if u'微博' in browser.title:
            for elem in browser.get_cookies():
                cookie[elem["name"]] = elem["value"]
            logger.warning("Get Cookie Success!( Account:%s )" % account)
        return json.dumps(cookie)
    #except Exception, e:
    #    logger.warning("Failed %s with:%s!" % (account, str(e)))
    #    return ""
    #finally:
    #    try:
    #        browser.quit()
    #    except Exception, e:
    #        pass


def initCookie(redis, spiderName):
    """ 获取所有账号的Cookies，存入Redis。如果Redis已有该账号的Cookie，则不再获取。 """
    for weibo in myWeiBo:
        if redis.get("%s:Cookies:%s--%s" % (spiderName, weibo[0], weibo[1])) is None:  # 'spidername:Cookies:账号--密码'，为None即不存在。
            cookie = getCookie(weibo[0], weibo[1])
            if len(cookie) > 0:
                redis.set("%s:Cookies:%s--%s" % (spiderName, weibo[0], weibo[1]), cookie)
    cookieNum = "".join(redis.keys()).count("%s:Cookies" % spiderName)
    logger.warning("The num of the cookies is %s" % cookieNum)
    if cookieNum == 0:
        logger.warning('Stopping...')
        os.system("pause")


def updateCookie(accountText, redis, spiderName):
    """ 更新一个账号的Cookie """
    account = accountText.split("--")[0]
    password = accountText.split("--")[1]
    cookie = getCookie(account, password)
    if len(cookie) > 0:
        logger.warning("The cookie of %s has been updated successfully!" % account)
        redis.set("%s:Cookies:%s" % (spiderName, accountText), cookie)
    else:
        logger.warning("The cookie of %s updated failed! Remove it!" % accountText)
        removeCookie(accountText, redis, spiderName)


def removeCookie(accountText, redis, spiderName):
    """ 删除某个账号的Cookie """
    redis.delete("%s:Cookies:%s" % (spiderName, accountText))
    cookieNum = "".join(redis.keys()).count("%s:Cookies" % spiderName)
    logger.warning("The num of the cookies left is %s" % cookieNum)
    if cookieNum == 0:
        logger.warning("Stopping...")
        os.system("pause")

if __name__ == '__main__':
    for weibo in myWeiBo:
        ret = getCookie(weibo[0], weibo[1])
        print weibo, ret
