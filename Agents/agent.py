import scrapy
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
from textblob import TextBlob
import re


class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://www.unimore.it/', "https://www.comune.modena.it/", "https://www.ferrari.com/it-IT"]

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()
        self.agentInfo, self.liveQueryClient = self.env.initializeAgent(self.liveQueryUpdateCallback)
    
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
        elif operation == 'delete':
            # this agent shall die
            self.agentInfo = None
            exit()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_node': None})
            
    def goBackToParent(self, parent_node):
        # get the parent from the environment
        parent_node = self.env.getExistingNode(parent_node)
        yield scrapy.Request(parent_node, callback=self.parse, meta={'depth': parent_node['depth'], 'parent_node': parent_node['parent_node']})

    def parse(self, response):
        # let's read the whole content of the page
        try:
            content = response.css('body').get()
        except:
            # go back to parent
            # get the parent from the environment
            parent_node = response.meta['parent_node']
            #go back to parent
            self.goBackToParent(parent_node)
            
        # let's find all the urls
        all_links = response.css('a::attr(href)').getall()
        # filter out the relative paths
        try:
            # links = [link for link in all_links if bool(urlparse(link).netloc) and not self.should_skip_url(link)]
            links = [link for link in all_links if not link.startswith('/') and not self.should_skip_url(link)]
        except ValueError:
            # go back to parent
            # get the parent from the environment
            parent_node = response.meta['parent_node']
            #go back to parent
            self.goBackToParent(parent_node)
            
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
        parent_node = response.meta['parent_node']
        try:
            parentQualityStatement = response.meta['parentQualityStatement']
        except KeyError:
            parentQualityStatement = None
        # let's get the current url
        url = response.url
        # let's get the current page language:
        # language = self.detectLanguage(content)
        
        edge = {
            "agent": self.agentInfo,
            "parent_node": parent_node,
            "traversal_depth": depth,
            "parentQualityStatement": parentQualityStatement
        }
        
        node = {
            "url": url,
            "children_nodes": len(linksWithQuality),
            "traversals": [edge],                  # arrays becuase more than one agent may land on the same node
        }
        
        # let's save the node
        self.env.saveNode(node)
        
        if(depth == 1):
            #go on scraping all the links
            for link in linksWithQuality:
                # let's create the request
                request = scrapy.Request(link['url'], callback=self.parse, meta={'depth': depth + 1, 'parent_node': url, 'parentQualityStatement': link['parentQualityStatement']})
                # let's yield the request
                yield request
        
        self.liveQueryClient.unsubscribe(1)

    def should_skip_url(self, url):
        #basic filtering
        skip_patterns = [
            r'accounts\.google\.com',   # Google sign-in URLs
            r'/login',                  # URLs containing '/login'
            r'/signin',                 # URLs containing '/signin'
            r'signin',                 # URLs containing 'signin'
            r'/account',                # URLs containing '/account'
            r'/auth',                   # URLs containing '/auth' for authentication
            r'\.pdf$',                  # URLs ending with '.pdf'
            r'\.jpg$',                  # URLs ending with '.jpg'
            r'\.png$',                  # URLs ending with '.png'
            r'\.zip$',                  # URLs ending with '.zip'
            r'\?page=',                 # URLs with pagination parameters
            r'\?sort=',                 # URLs with sorting parameters
            r'\?filter=',               # URLs with filtering parameters
            r'\?sessionid=',            # URLs with session IDs
            r'\?utm_source=',           # URLs with tracking parameters
            r'\?tracking_id=',
        ]
        
        # Check if the URL matches any skip patterns
        for pattern in skip_patterns:
            if re.search(pattern, url):
                return True  # Skip the URL
        
        return False  # Don't skip the URL

    
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


if __name__ == "__main__":
    agent = AgentAnt()