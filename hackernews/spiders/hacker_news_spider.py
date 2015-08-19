import scrapy
from hackernews.items import HackerNewsItem
from scrapy.linkextractors import LinkExtractor

class HackerNewsSpider(scrapy.Spider):
    name = "hnews"
    allowed_domains = ["ycombinator.com"]

    def start_requests(self):
        yield scrapy.Request("http://news.ycombinator.com", callback=self.parse)

    def parse(self, response):
        for sel in response.xpath("//tr[@class='athing']"):
            item = HackerNewsItem()
            link_sel = sel.xpath("./td[@class='title']")
            item['title'] = link_sel.xpath("./a/text()").extract()[0]
            item['url'] = link_sel.xpath("./a/@href").extract()[0]
            details_sel = sel.xpath("./following-sibling::*[position()=1]/td[@class='subtext']")
            item['points'] = details_sel.xpath("./span[@class='score']/text()").extract_first()
            item['user_name'] = details_sel.xpath("./a[starts-with(@href, 'user')]/text()").extract_first()
            item['since'] = details_sel.xpath("./a[starts-with(@href, 'item')][contains(., 'ago')]/text()").extract_first()
            item['comments'] = details_sel.xpath("./a[starts-with(@href, 'item')][contains(., 'comment') or contains(., 'discuss')]/text()").extract_first()
            yield item

        next_page_url = filter(lambda s: s.text == 'More', LinkExtractor().extract_links(response))[0].url
        yield scrapy.Request(next_page_url, callback=self.parse)
