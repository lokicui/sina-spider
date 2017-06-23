# encoding=utf-8
# ------------------------------------------
#   版本：3.0
#   日期：2016-12-01
#   作者：九茶<http://blog.csdn.net/bone_ace>
# ------------------------------------------

from scrapy import Item, Field


class UserItem(Item):
    """ 个人信息 """
    id = Field()  # 用户ID
    name = Field()  # 昵称
    seed = Field()
    url = Field()
    host = Field()
    pic = Field()
    pics = Field()
    collectsCount = Field()
    buff = Field()
    imageUrls = Field()
    images = Field()


class TweetsItem(Item):
    """ 微博信息 """
    id = Field()  #
    url = Field()
    host = Field()
    pageid = Field()
    srcid = Field()
    rawTitle = Field()
    title = Field()
    rawContent = Field()
    content = Field()
    pics = Field()
    oriPics = Field()
    videos = Field()
    videoPics = Field()
    music = Field()
    musicPic = Field()
    repostsCount = Field()
    commentsCount = Field()
    attitudesCount = Field()
    collectsCount = Field()
    viewsCount = Field()
    buff = Field()
    imageUrls = Field()
    images = Field()
    fileUrls = Field()
    files = Field()
    releaseTime = Field()
    updateTime = Field()
    insertTime = Field()

class TweetsItemPics(Item):
    '''
    微博的组图单独存
    '''
    _id = Field()
    UID = Field()
    Picall = Field() #组图
    Oripicall = Field() #组图原图

class RelationshipsItem(Item):
    """ 用户关系，只保留与关注的关系 """
    Host1 = Field()
    Host2 = Field()  # 被关注者的ID
