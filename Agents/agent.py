import scrapy
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
import re

import tldextract, random
from scrapy.exceptions import CloseSpider

def get_domain(url):
    extracted = tldextract.extract(url)
    return "{}.{}".format(extracted.domain, extracted.suffix)

class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://www.unimore.it/'] #, "https://www.comune.modena.it/", "https://www.ferrari.com/"]
    custom_settings = {
    'DEPTH_LIMIT': 999999  # A very large number to practically make it unlimited
    }

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()
        self.agentInfo, self.liveQueryClient = self.env.initializeAgent(self.liveQueryUpdateCallback)
        self.subscription_id = ""
    
    def liveQueryUpdateCallback(self, operation, data):
        if operation == 'connected':
            self.subscription_id = data['clientId']
            print("Connected to LiveQuery")
        elif operation == 'error':
            print(f"Error: {data}")
        elif operation == 'subscribed':
            print(f"Subscribed to query: {data}")
        elif operation == 'create':
            self.agentInfo = data
        elif operation == 'update':
            self.agentInfo = data
            if(self.agentInfo["pathQuality"] == 0):
                self.die("Path quality is 0")
        # elif operation == 'delete':
        #     # this agent shall die
        #     self.agentInfo = None
        #     exit()

    def closed(self, reason):
        self.agentInfo["state"] = "dead"
        self.env.updateAgent(self.agentInfo)
        self.liveQueryClient.unsubscribe(self.subscription_id)
        raise CloseSpider(reason)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_node': None}, dont_filter=True)
            
    def die(self, reason):
        self.closed(reason)
        
            
    def parse(self, response):
        # let's get the depth
        depth = response.meta['depth']
        if 'parent_node' in response.meta:
            parent_node = response.meta['parent_node']
        else:
            parent_node = None
        
        # let's read the whole content of the page
        try:
            content = response.css('body').get()
        except:
            self.die("No content found in page")
            
        # let's find all the urls
        all_links = response.css('a::attr(href)').getall()
        # doing a basic clean out, to make sure we'll ignore the useless links
        links = []
        for link in all_links:
            try:
                if not self.should_skip_url(link):
                    links.append(link)
            except ValueError:
                print(f"Skipping {link}")
        
        if(len(links) == 0 or not links):
            self.die("No more ways to go")
            
        # let's get the current url
        url = response.url
        
        node = {
            "url": url,
            "content": content,
            "parent_node": parent_node,
            "agent": self.agentInfo["objectId"],
        }
        
        # let's save the node
        self.env.saveNode(node)
        
        agent = self.agentInfo
        # let's update the agent
        agent["max_depth"] = depth
        self.env.updateAgent(agent)
        
        nextLink = self.pickNextLink(links)
        # let's create the request
        request = scrapy.Request(nextLink, callback=self.parse, meta={'depth': depth + 1, 'parent_node': url }, dont_filter=True, errback=self.handle_error)

        # let's yield the request
        yield request

    def handle_error(self, failure):
        # go back to parent
        self.die(failure.value.response.url + " is not reachable")

    def pickNextLink(self, links):
        return random.choice(links)

    def should_skip_url(self, url):

        #for now, ignore any link to google or facebook or linkedin or twitter or instagram or youtube
        skip_domains = [
            r'google\.com',   # Google sign-in URLs
            r'facebook\.com',   # Google sign-in URLs
            r'linkedin\.com',   # Google sign-in URLs
            r'twitter\.com',   # Google sign-in URLs
            r'instagram\.com',   # Google sign-in URLs
            r'youtube\.com',   # Google sign-in URLs
            r'youtu\.be',   # Google sign-in URLs
        ]
        # Check if the URL matches any skip patterns
        for pattern in skip_domains:
            if re.search(pattern, url):
                return True

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
        #check if not subomain
        if(url.startswith('/')):
            return True
        # let's check if the link is an anchor
        if(url.startswith('#')):
            return True
        if(not url.startswith('http')):
            return True
        #check if it is a url 
        if not bool(urlparse(url).netloc):
            return True

        # Check if the URL matches any skip patterns
        for pattern in skip_patterns:
            if re.search(pattern, url):
                return True  # Skip the URL
        
        return False  # Don't skip the URL
        

if __name__ == "__main__":
    agent = AgentAnt()