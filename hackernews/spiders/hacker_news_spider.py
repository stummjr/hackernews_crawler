import scrapy
import urlparse
from scrapy.linkextractors import LinkExtractor
from hackernews.items import HackerNewsItem, CommentItem


class HackerNewsSpider(scrapy.Spider):
    name = "hnews"
    allowed_domains = ["ycombinator.com"]
    start_urls = ["http://news.ycombinator.com"]

    def extract_post(self, sel, response):
        item = HackerNewsItem()
        link_sel = sel.xpath("./td[@class='title']")
        item['title'] = link_sel.xpath("./a/text()").extract_first()
        item['url'] = link_sel.xpath("./a/@href").extract_first()
        details_sel = sel.xpath(
            "./following-sibling::*[position()=1]/td[@class='subtext']"
        )
        item['points'] = details_sel.xpath(
            "./span[@class='score']/text()"
        ).extract_first()
        item['user_name'] = details_sel.xpath(
            "./a[starts-with(@href, 'user')]/text()"
        ).extract_first()
        item['since'] = details_sel.xpath(
            "./a[starts-with(@href, 'item')][contains(., 'ago')]/text()"
        ).extract_first()
        item['comments'] = details_sel.xpath(
            "./a[starts-with(@href, 'item')][contains(., 'comment') or"
            "contains(., 'discuss')]/text()"
        ).extract_first()
        item['comments_url'] = urlparse.urljoin(
            response.url, details_sel.xpath(
                "./a[starts-with(@href, 'item')]/@href"
            ).extract_first()
        )
        return item

    def parse(self, response):
        for sel in response.xpath("//tr[@class='athing']"):
            item = self.extract_post(sel, response)
            yield item
            # ads have no comments
            if item['comments_url'] != 'https://news.ycombinator.com/':
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
        for athing_sel in response.xpath('//tr[@class="athing"]')[1:]:
            item = CommentItem()
            item['nesting_level'] = int(
                athing_sel.xpath(
                    ".//td[@class='ind']/img/@width"
                ).extract_first()
            )
            item['text'] = "\n".join(
                athing_sel.xpath(
                    ".//td[@class='default']//span[@class='comment']//text()"
                ).extract()[1:-6]
            )
            item['user_name'] = athing_sel.xpath(
                ".//td[@class='default']//span[@class='comhead']/"
                "a[starts-with(@href, 'user')]/text()"
            ).extract_first()
            item['id_'] = athing_sel.xpath(
                ".//td[@class='default']//a[starts-with(@href, 'item')]/@href"
            ).extract_first()
            item['hacker_news_item'] = response.url
            items.append(item)

        self.fill_parents(items)
        for item in items:
            yield item

    def get_parent_of(self, list_, current):
        for i in range(current, -1, -1):
            if list_[i]['nesting_level'] < list_[current]['nesting_level']:
                return list_[i]['id_']

    def fill_parents(self, list_):
        for i, item in enumerate(list_):
            item['parent'] = self.get_parent_of(list_, i)
