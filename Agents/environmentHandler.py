import json
from parseServerClient import ParseServerClient
from parseQuery import ParseQuery

class Node:
    def __init__(self, url, parent_url, depth):
        self.url = url
        self.parent_url = parent_url
        self.depth = depth
        self.updatedAt = None
        self.createdAt = None
        self.objectId = None


# let's create a class that allows handling the environment.
class VirtualEnvironment:
    # initialize with a Parse Server Client
    def __init__(self):
        # load the info for the parse server client from the config file
        with open("enviroment.json", "r") as config:
            # load it as a json object
            self.config = json.load(config)
        # initialize the parse server client
        self.client = ParseServerClient(self.config["server_url"], self.config["app_id"], self.config["master_key"])
    
    def getExistingNode(self, url):
        # get the node existence
        query = ParseQuery("Node")
        query.equalTo("url", url)
        # get the result
        result = self.client.query(query)
        # if there is no result, return false
        if len(result) == 0:
            return False
        # otherwise, return the first result
        return result[0]

    def saveNode(self, node):
        # check if the node already exists
        existingNode = self.getExistingNode(node.url)
        # if it does, update it
        if existingNode:
            existingNode["parent_url"] = node.parent_url
            existingNode["depth"] = node.depth
            self.client.update("Node", existingNode.objectId, existingNode)
        else:
            # otherwise, create it
            self.client.create("Node", node)
