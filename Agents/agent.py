import scrapy
from urllib.parse import urlparse
from environmentHandler import VirtualEnvironment
import re

import tldextract, random
from scrapy.exceptions import CloseSpider

import pandas as pd
import numpy as np

from twisted.internet import defer



def get_domain(url):
    extracted = tldextract.extract(url)
    return "{}.{}".format(extracted.domain, extracted.suffix)

class AgentAnt(scrapy.Spider):
    name = 'grogubila'
    # start_urls = ["https://www.unimore.it/"] #, , "https://www.ferrari.com/"] 'https://www.comune.modena.it/'
    custom_settings = {
    'DEPTH_LIMIT': 999999  # A very large number to practically make it unlimited
    }

    def __init__(self, *args, **kwargs):
        # call the parent constructor
        super().__init__()
        # initialize the environment
        self.env = VirtualEnvironment()
        self.agentInfo, self.liveQueryClient = self.env.initializeAgent(self.liveQueryUpdateCallback)
        self.subscription_id = ""
        self.start_urls = kwargs.get('start_urls').split(',') if 'start_urls' in kwargs else []
        # let's clean the start urls, keeping only non empty sequences
        self.start_urls = [url for url in self.start_urls if url and url!='']
        print(self.start_urls)
        

    def killIfShamefulPath(self):
        if(self.agentInfo["pathQuality"] == 0):
                self.die("Path quality is 0")

    def killIfCircularPath(self):
        if("numberOfNodesInPath" in self.agentInfo and self.agentInfo["numberOfNodesInPath"] < 2*self.agentInfo["max_depth"]):
            self.die("Circular path")
    
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
            self.killIfShamefulPath()
        # elif operation == 'delete':
        #     # this agent shall die
        #     self.agentInfo = None
        #     exit()

    def closed(self, reason):
        self.agentInfo["state"] = "dead"
        if(not self.agentInfo["pathQuality"]):
            self.agentInfo["pathQuality"] = 0
        self.env.updateAgent(self.agentInfo)
        self.liveQueryClient.unsubscribe(self.subscription_id)
        # self.initFunction()
        # for url in self.start_urls:
        #     yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_node': None}, dont_filter=True)
        raise CloseSpider(reason)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'depth': 1, 'parent_node': None}, dont_filter=True)
            
    def die(self, reason):
        return self.closed(reason)
        
            
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
        else:    
            # let's find all the urls
            all_links = response.css('a::attr(href)').getall()
            # doing a basic clean out, to make sure we'll ignore the useless links
            links = []
            for link in all_links:
                try:
                    if not self.should_skip_url(link) and link != response.url:
                        links.append(link)
                except ValueError:
                    print(f"Skipping {link}")
            
            if(len(links) == 0 or not links):
                self.die("No more ways to go")
            
            else: 
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
        self.die("some website is not reachable")
        
    def getDfOfLinks(self, links, nodes):
        # let's first of all fetch the links
        
        
        links_df = pd.DataFrame(links, columns=['url'])
        nodes_df = pd.DataFrame(nodes)
        merged_df = pd.merge(links_df, nodes_df, on='url', how='left')
        return merged_df
    
    def normalizeQuality(self, df):
        # let's get the lowest contentQuality that is not nan
        lowest_contentQuality = df['contentQuality'].min()
        
        # let's fill the nan values with the lowest contentQuality
        df['contentQuality'] = df['contentQuality'].fillna(lowest_contentQuality)
        
        return df
    
    def computeAgentOverallPathQuality(self, agent):
        # let's check if the agent is the one we are running now
        if(agent["objectId"] == self.agentInfo["objectId"]):
            # let's return 0, so that we lower as much as possible the probability of picking the same path again
            return 0
        if "pathQuality" not in agent or not agent["pathQuality"]:
            return 0
        if "max_depth" not in agent or not agent["max_depth"]:
            return 0
        return agent["pathQuality"] * agent["max_depth"]
    
    def elaborateAgents(self, df):
        # each agent contains a pathQuality variable and a depth variable
        # we should turn the agents object into an array of variable, which should be represented
        # by it's pathQuality * depth
        
        df["agents"] = df["agents"].apply(lambda d: d if isinstance(d, list) else [])
        df["agents"] = df["agents"].apply(lambda x: [self.computeAgentOverallPathQuality(agent) for agent in x])
        
        # now we should create a new column called pheromone strength, which is the median of the agents
        df["pheromone_strength"] = df["agents"].apply(lambda x: np.median(x) if len(x) > 0 else None)
        
        # let's find the lowest pheromone strength
        lowest_pheromone_strength = df['pheromone_strength'].min()
        # apply it to the nones
        df['pheromone_strength'] = df['pheromone_strength'].fillna(lowest_pheromone_strength)
        
        return df   
        
        
        

    def pickNextLink(self, links):
        nodes = self.env.getExistingNodesWithAgents(links)
        if(len(nodes) == 0):
            # random
            return random.choice(links)
        df = self.getDfOfLinks(links, nodes)
        df = self.normalizeQuality(df)
        df = self.elaborateAgents(df)
        
        # check if any nan among contentQuality
        if(df['contentQuality'].isnull().values.any()):
            # set them all to 1
            df['contentQuality'] = 1 # equal value for all
        if(df['pheromone_strength'].isnull().values.any()):
            # set them all to 1
            df['pheromone_strength'] = 1 # equal value for all

        # at this point we should have a df with all the links and their quality
        content_Quality = df['contentQuality'].to_numpy() + 0.000001 # we add by a very small number to avoid the 0
        pheromone_strength = df['pheromone_strength'].to_numpy() + 0.000001 # we add by a very small number to avoid the 0
        
        # let's normalize the two series
        content_Quality = content_Quality / content_Quality.sum()
        pheromone_strength = pheromone_strength / pheromone_strength.sum()
        
        # these two vectors represent the set of weights to use for the weighted random choice
        # let's dot product them
        weights = content_Quality * pheromone_strength
        # let's normalize the weights
        weights = weights / weights.sum()  # Normalize the weights so they sum to 1
        # let's make a random weighted choice
        choice = np.random.choice(links, p=weights)
        return choice
        
        
        
        

        

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