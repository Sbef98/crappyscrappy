import scrapy
import random
from environmentHandler import VirtualEnvironment

class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://quotes.toscrape.com']

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_url': None})

    def parse(self, response):
        