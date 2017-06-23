# encoding=utf-8
# ------------------------------------------
#   版本：3.0
#   日期：2016-12-01
#   作者：九茶<http://blog.csdn.net/bone_ace>
# ------------------------------------------

BOT_NAME = ['sina_spider']

SPIDER_MODULES = ['sina_spider.spiders']
NEWSPIDER_MODULE = 'sina_spider.spiders'

DOWNLOADER_MIDDLEWARES = {
    "sina_spider.middleware.UserAgentMiddleware": 301,
    "sina_spider.middleware.CookiesMiddleware": 302,
}
ITEM_PIPELINES = {
    'scrapy.pipelines.images.ImagesPipeline' : 401,
    'scrapy.pipelines.files.FilesPipeline': 402,
    'sina_spider.pipelines.ESPipeline': 403,
}

IMAGES_STORE = '/workspace/gitEnv/sina-spider/image_store'
FILES_STORE = '/workspace/gitEnv/sina-spider/file_store'

IMAGES_EXPIRES = 90
IMAGES_THUMBS = {
        'small': (50, 50),
        'big': (270, 270),
}

IMAGES_MIN_HEIGHT = 10
IMAGES_MIN_WIDTH = 10
# 120 days of delay for files expiration
FILES_EXPIRES = 120
# 30 days of delay for images expiration
IMAGES_EXPIRES = 30
FILES_URLS_FIELD = 'fileUrls'
FILES_RESULT_FIELD = 'files'
IMAGES_URLS_FIELD = 'imageUrls'
IMAGES_RESULT_FIELD = 'images'

#SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER = "sina_spider.scrapy_es.scheduler.Scheduler"
# Ensure all spiders share same duplicates filter through redis.
#DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
DUPEFILTER_CLASS = "sina_spider.scrapy_es.dupefilter.ESRFPDupeFilter"
DUPEFILTER_DEBUG = True
# Default requests serializer is pickle, but it can be changed to any module
# with loads and dumps functions. Note that pickle is not compatible between
# python versions.
# Caveat: In python 3.x, the serializer must return strings keys and support
# bytes as values. Because of this reason the json or msgpack module will not
# work by default. In python 2.x there is no such issue and you can use
# 'json' or 'msgpack' as serializers.
#SCHEDULER_SERIALIZER = "scrapy_redis.picklecompat"

# Don't cleanup redis queues, allows to pause/resume crawls.
SCHEDULER_PERSIST = True

# Schedule requests using a priority queue. (default)
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

# Alternative queues.
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.FifoQueue'
#SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.LifoQueue'

# Max idle time to prevent the spider from being closed when distributed crawling.
# This only works if queue class is SpiderQueue or SpiderStack,
# and may also block the same time when your spider start at the first time (because the queue is empty).
#SCHEDULER_IDLE_BEFORE_CLOSE = 10

# The item pipeline serializes and stores the items in this redis key.
#REDIS_ITEMS_KEY = '%(spider)s:items'

# The items serializer is by default ScrapyJSONEncoder. You can use any
# importable path to a callable object.
#REDIS_ITEMS_SERIALIZER = 'json.dumps'


DOWNLOAD_DELAY = 0.1  # 间隔时间
LOG_FILE='/workspace/gitEnv/sina-spider/logs/spider.log'
LOG_FORMAT= '%(levelname)s %(asctime)s [%(name)s:%(module)s:%(funcName)s:%(lineno)s] [%(exc_info)s] %(message)s'
LOG_LEVEL = 'INFO'  # 日志级别
CONCURRENT_REQUESTS = 20  # 默认为16
# CONCURRENT_ITEMS = 1
# CONCURRENT_REQUESTS_PER_IP = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 12
REDIRECT_ENABLED = False
#REDIRECT_ENABLED = True


# The item pipeline serializes and stores the items in this redis key.
#REDIS_ITEMS_KEY = '%(spider)s:items'

# The items serializer is by default ScrapyJSONEncoder. You can use any
# importable path to a callable object.
#REDIS_ITEMS_SERIALIZER = 'json.dumps'

ES_HOST = ['http://10.134.13.99:9200']
# Specify the host and port to use when connecting to Redis (optional).
REDIS_HOST = '10.134.24.31'
REDIS_PORT = 6379

# Specify the full Redis URL for connecting (optional).
# If set, this takes precedence over the REDIS_HOST and REDIS_PORT settings.
#REDIS_URL = 'redis://user:pass@hostname:9001'

# Custom redis client parameters (i.e.: socket timeout, etc.)
#REDIS_PARAMS  = {}
# Use custom redis client class.
#REDIS_PARAMS['redis_cls'] = 'myproject.RedisClient'

# If True, it uses redis' ``SPOP`` operation. You have to use the ``SADD``
# command to add URLs to the redis queue. This could be useful if you
# want to avoid duplicates in your start urls list and the order of
# processing does not matter.
#REDIS_START_URLS_AS_SET = False

# Default start urls key for RedisSpider and RedisCrawlSpider.
#REDIS_START_URLS_KEY = '%(name)s:start_urls'

# Use other encoding than utf-8 for redis.
#REDIS_ENCODING = 'latin1'
