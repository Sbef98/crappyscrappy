from arrow import get
import scrapy
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
from textblob import TextBlob
import re, requests
from datetime import datetime
from w3lib.http import headers_raw_to_dict
import numpy as np

import tldextract, random

def get_domain(url):
    extracted = tldextract.extract(url)
    return "{}.{}".format(extracted.domain, extracted.suffix)

class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    start_urls = ['https://www.unimore.it/', "https://www.comune.modena.it/", "https://www.ferrari.com/"]
    custom_settings = {
    'DEPTH_LIMIT': 999999  # A very large number to practically make it unlimited
    }

    def __init__(self):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()
        self.agentInfo, self.liveQueryClient = self.env.initializeAgent(self.liveQueryUpdateCallback)
        
        self.maxNodeAge = 31536000 # max age of a node in seconds (current 1 year, 60*60*24*365)
        self.maxOldAgePenalization = 0.5 # max penalization for old age (current 0.5)
        
        self.domainDifferantiationWeights = [1,2,3]
        self.edgeAgePenality = 1.0 # max penalization for old age (current 0.5)
        self.maxEdgeAgeBooster = 3 # max booster for old age (current 3)

        self.activeEdgesBooster = 2 # max booster for active edges, which means how much is the maximum pheromon booster 
                                   # if there are a lot of edges
        self.maximumActiveEdgesForMaxBooster = 10 # maximum number of active edges to reach the maximum booster

        # i want edges not older than 1 day
        self.maxEdgeAge = 86400 # max age of an edge in seconds (current 1 day, 60*60*24)
    
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
        # elif operation == 'delete':
        #     # this agent shall die
        #     self.agentInfo = None
        #     exit()

    def closed(self, reason):
        self.agentInfo["state"] = "dead"
        self.env.updateAgent(self.agentInfo)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_node': None, 'parent_node_quality': None, "parentQualityStatement": 1}, dont_filter=True)
            
    def goBackToParent(self, parent_node, depth):
        # get the parent from the environment
        parent_node = self.env.getExistingNode(parent_node)
        try:
            return scrapy.Request(parent_node['url'], callback=self.parse, meta={'depth': depth - 1, 'parent_node': None,  'parentQualityStatement': 0, 'parent_node_quality': 0.5}, dont_filter=True)
        except Exception as e:
            print(e)
            return scrapy.Request(self.start_urls[0], callback=self.parse, meta={'depth': 1, 'parent_node': None, 'parent_node_quality': None, "parentQualityStatement": 1}, dont_filter=True)

    def parse(self, response):
        # let's get the depth
        depth = response.meta['depth']
        try:
            # let's read the whole content of the page
            try:
                content = response.css('body').get()
            except:
                # go back to parent
                # get the parent from the environment
                parent_node = response.meta['parent_node']
                #go back to parent
                yield self.goBackToParent(parent_node, depth)
                
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
                # go back to parent
                # get the parent from the environment
                parent_node = response.meta['parent_node']
                #go back to parent
                yield self.goBackToParent(parent_node, depth)
                return
                
            currentNodeAgeWeight = self.getNodeAgeWeight(response)
            # the weight of the current node is a value between 0 and 1. Let's stretch it to something between 1.0 and 1.5
            # so that it's actually a + if it is very well updated
            currentNodeAgeWeight = self.maxOldAgePenalization + currentNodeAgeWeight
            
            linksWeights = self.checkLinksQuality(links, content)
            linksWeights = self.setDomainWeights(linksWeights, response.url, currentNodeAgeWeight)
            #linksWeights = self.setLinksAgeWeightFromSneakPeak(linksWeights) shall skip for now it's too slow

            parent_node_quality = response.meta['parent_node_quality']
            linksWeightsFromEnvironment = self.getWeightsForNodesFromEnvironment([link['url'] for link in linksWeights], parent_node_quality)

            linksWeights = self.setLinksQualityStatements(linksWeights, linksWeightsFromEnvironment)

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
                "parentQualityStatement": parentQualityStatement,
                "parent_node_quality": parent_node_quality,
            }
            
            node = {
                "url": url,
                "children_nodes": len(linksWeights),
                "traversals": [edge],                  # arrays becuase more than one agent may land on the same node
                "content": content
            }
            
            # let's save the node
            self.env.saveNode(node)
            
            
            nextLink = self.pickNextLink(linksWeights)
            # let's create the request
            request = scrapy.Request(nextLink['url'], callback=self.parse, meta={'depth': depth + 1, 'parent_node': url, 'parentQualityStatement': nextLink['qualityStatement'], 'parent_node_quality': parentQualityStatement}, dont_filter=True, errback=self.handle_error)

            # let's yield the request
            yield request
        except Exception as e:
            print(e)
            # go back to parent
            # get the parent from the environment
            parent_node = response.meta['parent_node']
            #go back to parent
            yield self.goBackToParent(parent_node, depth)

    def handle_error(self, failure):
        # go back to parent
        # get the parent from the environment
        parent_node = failure.request.meta['parent_node']
        depth = failure.request.meta['depth']
        #go back to parent
        yield self.goBackToParent(parent_node, depth)

    def pickNextLink(self, links):
        # each link as a parameter called qualityStatement, which is a value between 0 and 1. Higher it is, higher shoukd be the probability to pick it
        # let's get the qualityStatements
        qualityStatements = [link['qualityStatement'] for link in links]
        # Pick a link at random, considering the qualityStatement as the weight
        chosen_link = random.choices(links, weights=qualityStatements, k=1)[0]

        return chosen_link

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

    
    def checkLinksQuality(self, links, content):
        # let's find in which part of content the links are
        # let's find the index of the links
        links_index = [content.find(link) for link in links]
        # let's read the 10 words before the link
        links_words_before = [content[index - 10:index] for index in links_index]
        # let's do a sentiment analysis on the 10 words before the link, if it is positive then it is a good link
        # let's return a dictionary with the link and the quality and the language
        return [{"url": link, "sentiment": sentiment} for link, sentiment in zip(links, [self.sentimentAnalysis(words) for words in links_words_before])]
    
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
            if('Last-Modified' in last_modified_header):
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

    def getEdgeAgeWeight(self, edge):
        # let's find out how old is the website we are currently looking at
        if('updatedAt' not in edge):
            return 1
        last_modified = edge['updatedAt']
        
        age = self.maxEdgeAge + 1
        
        if last_modified:
            last_modified_date = datetime(last_modified)
            current_date = datetime.now()
            age = current_date - last_modified_date
            age = age.total_seconds()
            
        # let's now set the weight based on the age
        # the weight must be 0.5 if age > self.maxNodeAge, else 1 if age == 0. The remaining range must be corrispondent to the range 0.5 to 1.0
        # therefore we need to find the ratio between the two ranges
        weight = self.maxOldAgePenalization
        if(age < self.maxEdgeAge):
            remaining = self.maxEdgeAgeBooster - self.maxOldAgePenalization
            weight += (remaining - (age * remaining) / self.maxEdgeAge)

        return weight

    def computeEdgeWeight(self, edge):
        """
        Should return a value between 1 and maxEdgeAgeBooster.
        1 if the edge is very old, maxEdgeAgeBooster if the edge is very young.
        Choosing 1 as mean value should return a neutral weight.
        """
        if('agent' not in edge):
            return 1
        agent = edge['agent']
        agent = self.env.fetchAgent(agent)
        # let's get the agent quality
        # check if agent is the same as the current agent
        if(agent['objectId'] == self.agentInfo['objectId']):
            agentQuality = 0 #should make the probability to make a circle as low as possible!
        else:
            agentQuality = agent['overallPathQuality'] # value between 0 and 1
        # let's get the parent quality
        if('parentQualityStatement' not in edge):
            parentQuality = 0
        parentQuality = edge['parentQualityStatement'] # value between 0 and 1
        # let's get the age weight
        ageWeight = self.getEdgeAgeWeight(edge) # value between maxEdgeAgePenality and maxEdgeAgeBooster (1 and 2)
        # let's compute the weight
        try:
            weight = np.mean([agentQuality, parentQuality]) * ageWeight
        except Exception as e:
            print(e)
            weight = 1
        if weight < 1:
            weight = 1
        return weight
        
        
    def getNodePheromoneBoosterFromEnvironment(self, url, parent_node_quality):
        """
        The final value should be something between 1 and maxEdgeAgeBooster * activeEdgesBooster

        """
        node = self.env.getExistingNodeWithEdges(url)
        if(node == None):
            return 1
        if('trversals' not in node):
            return 1
        edges = node['traversals']
        try:
            weights = np.array([self.computeEdgeWeight(edge) for edge in edges])
        except Exception as e:
            print(e)
            return 1
        activeWeights = weights[weights > 1]

        # activeEdgesBooster
        # maximumActiveEdgesForMaxBooster
        activeEdgesBooster = self.activeEdgesBooster
        if(activeWeights < self.maximumActiveEdgesForMaxBooster):
            activeEdgesBooster = 1 + (activeWeights * (self.activeEdgesBooster - 1))/self.maximumActiveEdgesForMaxBooster
        
        try:
            meanWeightsValue = np.mean(weights) * activeEdgesBooster * parent_node_quality # if the parent node was not such high quality it should be ignored, it's noe "belieavable"
        except Exception as e:
            print(e)
            meanWeightsValue = 1

        return meanWeightsValue
    
    def getWeightsForNodesFromEnvironment(self, urls, parent_node_quality):
        return [self.getNodePheromoneBoosterFromEnvironment(url, parent_node_quality) for url in urls]
    

    def computeOverallLinkQualityStatement(self, link, linkQualityFromEnvironment):
        # let's get the domain weight
        domainWeight = self.domainDifferantiationWeights[1]
        if('domainWeight' in link):
            domainWeight = link['domainWeight'] # between min(self.domainDifferantiationWeights) and max(self.domainDifferantiationWeights
                                                # currently 1 to 3
        # ageWeight = 1
        # if('ageWeight' in link):
        #     # let's get the age weight
        #     ageWeight = link['ageWeight'] # between self.maxOldAgePenalization and 1

        sentiment = link['sentiment'] # value between -1 and 1

        # let's compute the overall weight
        domainByQualityWeight = domainWeight * sentiment + max(self.domainDifferantiationWeights) # so it's a positive value, currentlu something between 0 and 6 apprently


        # let's get the pheromone booster
        pheromoneBooster = linkQualityFromEnvironment # value between 1 and maxEdgeAgeBooster * activeEdgesBooster, currently 6!

        
        # let's compute the overall weight
        try:
            weight = np.mean([domainByQualityWeight, pheromoneBooster])
        except Exception as e:
            print(e)
            weight = 1
        return weight
    
    def setLinksQualityStatements(self, links, linksQualityFromEnvironment):
        qualityStatements = np.array([])
        for link, quality in zip(links, linksQualityFromEnvironment):
            qualityStatement = self.computeOverallLinkQualityStatement(link, quality)
            qualityStatements = np.append(qualityStatements, qualityStatement)
        # the overall qualityStatements should be normalized to a value between 0 and 1
        # let's find the max value
        try:
            maxQuality = np.max(qualityStatements)
            # let's normalize
            qualityStatements = qualityStatements / maxQuality
            # let's set the qualityStatements
            for link, qualityStatement in zip(links, qualityStatements):
                link['qualityStatement'] = qualityStatement
        except Exception as e:
            print(e)
            for link in links:
                link['qualityStatement'] = 0.5
        return links
        

if __name__ == "__main__":
    agent = AgentAnt()
    print(agent.setLinksAgeWeightFromSneakPeak([{"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}, {"url": "https://www.unimore.it/", "parentQualityStatement": 0.5}]))