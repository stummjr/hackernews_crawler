# -*- coding: utf-8 -*-
import scrapy


class HackerNewsItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    points = scrapy.Field()
    comments = scrapy.Field()
    comments_url = scrapy.Field()
    user_name = scrapy.Field()
    since = scrapy.Field()


class CommentItem(scrapy.Item):
    hacker_news_item = scrapy.Field()
    id_ = scrapy.Field()
    nesting_level = scrapy.Field()
    parent = scrapy.Field()
    text = scrapy.Field()
    user_name = scrapy.Field()
    since = scrapy.Field()
