from arrow import get
import scrapy
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
from textblob import TextBlob
import re, requests
from datetime import datetime
from w3lib.http import headers_raw_to_dict

import tldextract

def get_domain(url):
    extracted = tldextract.extract(url)
    return "{}.{}".format(extracted.domain, extracted.suffix)

class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://www.unimore.it/', "https://www.comune.modena.it/"]

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()
        self.agentInfo, self.liveQueryClient = self.env.initializeAgent(self.liveQueryUpdateCallback)
        
        self.maxNodeAge = 31536000 # max age of a node in seconds (current 1 year, 60*60*24*365)
        self.maxOldAgePenalization = 0.5 # max penalization for old age (current 0.5)
        
        self.domainDifferantiationWeights = [1,2,3]
    
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
            
        currentNodeAgeWeight = self.getNodeAgeWeight(response)
        # the weight of the current node is a value between 0 and 1. Let's stretch it to something between 1.0 and 1.5
        # so that it's actually a + if it is very well updated
        currentNodeAgeWeight = self.maxOldAgePenalization + currentNodeAgeWeight
        
        linksWeights = self.checkLinksQuality(links, content)
        linksWeights = self.setDomainWeights(linksWeights, response.url, currentNodeAgeWeight)
        #linksWeights = self.setLinksAgeWeightFromSneakPeak(linksWeights) shall skip for now it's too slow
        
        
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
            "children_nodes": len(linksWeights),
            "traversals": [edge],                  # arrays becuase more than one agent may land on the same node
        }
        
        # let's save the node
        self.env.saveNode(node)
        
        if(depth == 1):
            #go on scraping all the links
            for link in linksWeights:
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
    
    
    def setDomainWeights(self, links, currentUrl, currentNodeAgeWeight):
         # let's now split the links based on being part of same domain, same subdomain or different domain
        # let's get the domain of the current url
        domain = get_domain(currentUrl)
        # let's get the subdomain of the current url
        subdomain = urlparse(currentUrl).hostname
        
        for link in links:
            # let's get the domain of the link
            linkDomain = get_domain(link['url'])
            # let's get the subdomain of the link
            linkSubdomain = urlparse(link['url']).hostname
            
            if(linkDomain == domain):
                # same domain
                link['domainWeight'] = self.domainDifferantiationWeights[1] * currentNodeAgeWeight
            elif(linkSubdomain == subdomain):
                # same subdomain
                link['domainWeight'] = self.domainDifferantiationWeights[0] * currentNodeAgeWeight
            else:
                # different domain
                link['domainWeight'] = self.domainDifferantiationWeights[2]
        return links
    
    def getPageAge(self, response):
        # this method could be modified in the feature. For a simple demo, we will use last modified.
        last_modified_header = response.headers.get('Last-Modified')
        return last_modified_header
    
    def getNodeAgeWeight(self, response):
        # let's find out how old is the website we are currently looking at
        last_modified_header = self.getPageAge(response)
        
        age = self.maxNodeAge + 1
        
        if last_modified_header:
            last_modified_header = headers_raw_to_dict(last_modified_header)
            last_modified_date = datetime.strptime(last_modified_header['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z')
            current_date = datetime.now()
            age = current_date - last_modified_date
            age = age.total_seconds()
            
        # let's now set the weight based on the age
        # the weight must be 0.5 if age > self.maxNodeAge, else 1 if age == 0. The remaining range must be corrispondent to the range 0.5 to 1.0
        # therefore we need to find the ratio between the two ranges
        weight = self.maxOldAgePenalization
        if(age < self.maxNodeAge):
            remaining = 1 - self.maxOldAgePenalization
            weight += (remaining - (age * remaining) / self.maxNodeAge)

        return weight

    def setLinksAgeWeightFromSneakPeak(self, links):
        for link in links:
            url = link['url']
            try:
                response = requests.head(url)
                weight = self.getNodeAgeWeight(response)
            except Exception:
                print(f"Error while getting the age of the node {url}")
                weight = 0.5
            link['ageWeight'] = weight
        return links
        
    def getNodeWeightFromEnvironment(self, url):
        node = self.env.getExistingNodeWithEdges(url)
        edges = node['traversals']
        
        # let's index the edges by parent
        edgesByParent = {}
        for edge in edges:
            if edge['parent_node'] in edgesByParent:
                # lets keep the newest edge based on createdAt attribute
                # this is important because ofc we keep the freshest informations from that specific parent
                if(edge['createdAt'] > edgesByParent[edge['parent_node']]['createdAt']):
                    edgesByParent[edge['parent_node']] = edge
            else :
                # let's index the edge by parent
                edgesByParent[edge['parent_node']] = edge
        
        numberOfInEdges = len(edgesByParent)
        

if __name__ == "__main__":
    agent = AgentAnt()
    print(agent.setLinksAgeWeightFromSneakPeak([{"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}]))