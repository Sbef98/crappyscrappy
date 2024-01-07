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
        self.agentInfo = self.env.initializeAgent(self.liveQueryUpdateCallback)
    
    def liveQueryUpdateCallback(self, operation, data):
        if operation == 'connected':
            print("Connected to LiveQuery")
        elif operation == 'error':
            print(f"Error: {data}")
        elif operation == 'subscribed':
            print(f"Subscribed to query: {data}")
        elif operation == 'create':
            self.agentInfo = data
        elif operation == 'update':
            self.agentInfo = data
            print(" ==================================================================================")
            print(" ==================================================================================")
            print(" ==================================================================================")
            print(" ==================================================================================")
            print(" ==================================================================================")
            print(" ==================================================================================")
        elif operation == 'delete':
            # this agent shall die
            self.agentInfo = None
            exit()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_url': None})
            
    def goBackToParent(self, parent_url):
        # get the parent from the environment
        parent_node = self.env.getExistingNode(parent_url)
        yield scrapy.Request(parent_url, callback=self.parse, meta={'depth': parent_node['depth'], 'parent_url': parent_node['parent_url']})

    def parse(self, response):
        # let's read the whole content of the page
        try:
            content = response.css('body').get()
        except:
            # go back to parent
            # get the parent from the environment
            parent_url = response.meta['parent_url']
            #go back to parent
            self.goBackToParent(parent_url)
            
        # let's find all the urls
        all_links = response.css('a::attr(href)').getall()
        # filter out the relative paths
        try:
            links = [link for link in all_links if bool(urlparse(link).netloc)]
        except ValueError:
            # go back to parent
            # get the parent from the environment
            parent_url = response.meta['parent_url']
            #go back to parent
            self.goBackToParent(parent_url)
            
        linksWithQuality = self.checkLinksQuality(links, content)
        
        # let's now split the links based on being part of same domain, same subdomain or different domain
        # let's get the domain of the current url
        domain = urlparse(response.url).netloc
        # let's get the subdomain of the current url
        subdomain = urlparse(response.url).hostname
        
        # let's split the links
        sameSubDomainLinks = [link for link in linksWithQuality if urlparse(link['url']).hostname == subdomain]
        sameDomainLinks = [link for link in linksWithQuality if urlparse(link['url']).netloc == domain and urlparse(link['url']).hostname != subdomain]
        differentDomainLinks = [link for link in linksWithQuality if urlparse(link['url']).netloc != domain and urlparse(link['url']).hostname != subdomain]
        
        
        
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
            "children_nodes": len(linksWithQuality),
            "agent": self.agentInfo,
        }
        
        # let's save the node
        self.env.saveNode(node)
        
        #go on scraping all the links
        for link in links:
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
        return [{"url": link, "parentQualityStatement": sentiment} for link, sentiment in zip(links, [self.sentimentAnalysis(words) for words in links_words_before])]
    
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
    
    def overallQuality(self, listOfLinks):
        pass
    
    def pickDomain(self, domain):
        pass
    