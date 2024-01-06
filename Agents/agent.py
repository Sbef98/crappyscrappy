import scrapy
import random
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
from textblob import TextBlob


class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://google.com']

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_url': None})

    def parse(self, response):
        # let's read the whole content of the page
        content = response.css('body').get()
        # let's find all the urls
        all_links = response.css('a::attr(href)').getall()
        # filter out the relative paths
        links = [link for link in all_links if bool(urlparse(link).netloc)]
        # linksWithQuality = self.checkLinksQuality(links, content)
        # let's get the depth
        depth = response.meta['depth']
        # let's get the parent url
        parent_url = response.meta['parent_url']
        # let's get the current url
        url = response.url
        # let's get the current page language:
        # language = self.detectLanguage(content)
        # let's create the node
        node = {
            "url": url,
            "parent_url": parent_url,
            "depth": depth,
            "daughter_nodes": links,
            # "content": content,
            # "content_language": language,
            # the "first discovery date" and the last "update" will be given for granted
            # by the parse server, who will update the two numbers automatically.
        }
        # let's save the node
        self.env.saveNode(node)
        if(depth < 10):
            # explore any link
            link = random.choice(links)
            # let's create the request
            request = scrapy.Request(link, callback=self.parse, meta={'depth': depth + 1, 'parent_url': url})
            # let's yield the request
            yield request
    
    def checkLinksQuality(self, links, content):
        # let's find in which part of content the links are
        # let's find the index of the links
        links_index = [content.find(link) for link in links]
        # let's read the 10 words before the link
        links_words_before = [content[index - 10:index] for index in links_index]
        # let's do a sentiment analysis on the 10 words before the link, if it is positive then it is a good link
        # let's return a dictionary with the link and the quality and the language
        return [{"url": link, "parentQualityStatement": sentiment} for link, sentiment, language in zip(links, [self.sentimentAnalysis(words) for words in links_words_before])]
    
    def detectLanguage(self, text):
        # Using TextBlob for language detection. It is a very simple and strtaightforward library,
        # therefore it is good enough for now.
        blob = TextBlob(text)
        language = blob.detect_language()
        print(language)
        return language
    
    def sentimentAnalysis(self, text):
        # Using TextBlob for sentiment analysis. It is a very simple and strtaightforward library,
        # therefore it is good enough for now.
        blob = TextBlob(text)
        return blob.sentiment.polarity
    