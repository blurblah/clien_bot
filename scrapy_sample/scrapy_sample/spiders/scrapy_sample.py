
import scrapy


class SampleSpider(scrapy.Spider):
    name = "sample"

    def start_requests(self):
        urls = [
            'https://www.clien.net/service/board/jirum',
            'https://www.clien.net/service/board/sold'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        board = response.url.split('/')[-1]
        filename = 'client-%s.html' % board
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
