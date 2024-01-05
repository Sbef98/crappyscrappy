import scrapy
import random

class QuoteSpider(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://quotes.toscrape.com']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_url': None})

    def parse(self, response):
        depth = response.meta['depth']
        parent_url = response.meta['parent_url']
        
        starting_url_domain = self.start_urls[0].split('/')[2]
        current_url_domain = response.url.split('/')[2]

        # if current depth is 0, let's pick one of the links at random and follow it
        if depth == 1:
            # get one of the links at random
            links = response.css('a::attr(href)').getall()
            index = random.randint(0, len(links) - 1)
            absolute_url = response.urljoin(links[index])
            yield {
                'url': absolute_url, 
                'depth': depth,
                'parent_url': parent_url,
                'starting_url': self.start_urls[0],
            }
            yield scrapy.Request(absolute_url, callback=self.parse, meta={'depth': 2, 'parent_url': response.url})
        # if the current depth is more than one, we should not pick the next link completely at random. Actually, we should give an higher chance to links who have the same domain as the starting_url
        elif depth < 5 or starting_url_domain != current_url_domain:
            # get all the links
            links = response.css('a::attr(href)').getall()
            # if the current url domain is not the same as the starting url domain, we should give an higher chance to links who have the same domain as the starting_url
            if starting_url_domain == current_url_domain:
                # get the links that do not have the same domain as the starting url
                links = [link for link in links if link.split('/')[2] != starting_url_domain]
            # get one of the links at random
            index = random.randint(0, len(links) - 1)
            absolute_url = response.urljoin(links[index])
            yield {
                'url': absolute_url, 
                'depth': depth,
                'parent_url': parent_url,
                'starting_url': self.start_urls[0],
            }
            yield scrapy.Request(absolute_url, callback=self.parse, meta={'depth': depth + 1, 'parent_url': response.url})
        else:
            print('😀')