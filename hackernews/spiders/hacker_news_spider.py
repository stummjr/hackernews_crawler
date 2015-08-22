import scrapy
from urlparse import urljoin
from scrapy.linkextractors import LinkExtractor
from hackernews.items import HackerNewsItem, CommentItem


class HackerNewsSpider(scrapy.Spider):
    name = "hnews"
    allowed_domains = ["ycombinator.com"]
    start_urls = ["http://news.ycombinator.com"]

    def parse(self, response):
        for sel in response.xpath("//tr[@class='athing']"):
            item = self.extract_news_item(sel, response)
            yield item
            # ads have no comments
            if item['comments_url'] is not None:
                yield scrapy.Request(
                    item['comments_url'], callback=self.parse_comments
                )
        next_page_url = filter(
            lambda s: s.text == 'More',
            LinkExtractor().extract_links(response)
        )[0].url
        yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_comments(self, response):
        items = []
        # the first item is not a comment
        for athing_sel in response.xpath('//tr[@class="athing"]')[1:]:
            comment_item = CommentItem()
            comment_item['nesting_level'] = int(
                athing_sel.xpath(
                    ".//td[@class='ind']/img/@width"
                ).extract_first()
            )
            comment_item['text'] = "\n".join(
                athing_sel.xpath(
                    ".//td[@class='default']//span[@class='comment']//text()"
                ).extract()[1:-6]
            )
            comment_item['user_name'] = athing_sel.xpath(
                ".//td[@class='default']//span[@class='comhead']/"
                "a[starts-with(@href, 'user')]/text()"
            ).extract_first()
            comment_item['id_'] = athing_sel.xpath(
                ".//td[@class='default']//a[starts-with(@href, 'item')]/@href"
            ).extract_first()
            comment_item['hacker_news_item'] = response.url
            items.append(comment_item)
        self.fill_parents(items)
        for item in items:
            yield item

    def extract_news_item(self, sel, response):
        news_item = HackerNewsItem()
        link_sel = sel.xpath("./td[@class='title']")
        news_item['title'] = link_sel.xpath("./a/text()").extract_first()
        news_item['url'] = link_sel.xpath("./a/@href").extract_first()
        details_sel = sel.xpath(
            "./following-sibling::*[position()=1]/td[@class='subtext']"
        )
        news_item['points'] = details_sel.xpath(
            "./span[@class='score']/text()"
        ).extract_first()
        news_item['user_name'] = details_sel.xpath(
            "./a[starts-with(@href, 'user')]/text()"
        ).extract_first()
        news_item['since'] = details_sel.xpath(
            "./a[starts-with(@href, 'item')][contains(., 'ago')]/text()"
        ).extract_first()
        news_item['comments'] = details_sel.xpath(
            "./a[starts-with(@href, 'item')][contains(., 'comment') or"
            "contains(., 'discuss')]/text()"
        ).extract_first()
        comments_path = details_sel.xpath(
            "./a[starts-with(@href, 'item')]/@href"
        ).extract_first()
        news_item['comments_url'] = (comments_path and
                                     urljoin(response.url, comments_path))
        return news_item

    def get_parent_of(self, list_, current):
        for i in range(current, -1, -1):
            if list_[i]['nesting_level'] < list_[current]['nesting_level']:
                return list_[i]['id_']

    def fill_parents(self, list_):
        for i, item in enumerate(list_):
            item['parent'] = self.get_parent_of(list_, i)
