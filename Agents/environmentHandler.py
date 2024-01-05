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
    def to_dict(self):
        return {
            'url': self.url,
            'parent_url': self.parent_url,
            'depth': self.depth,
            'updatedAt': self.updatedAt,
            'createdAt': self.createdAt,
            'objectId': self.objectId
        }

# let's create a class that allows handling the environment.
class VirtualEnvironment:
    # initialize with a Parse Server Client
    def __init__(self):
        # load the info for the parse server client from the config file
        with open("environment.json", "r") as config:
            # load it as a json object
            self.config = json.load(config)
        # initialize the parse server client
        self.client = ParseServerClient(self.config["serverURL"], self.config["appId"], self.config["restApiKey"])
    
    def getExistingNode(self, url):
        # get the node existence
        query = ParseQuery("Node")
        query.equalTo("url", url)
        # get the result
        result = self.client.query(query)
        # if there is no result, return None
        if len(result) == 0:
            return None
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


if __name__ == "__main__":
    # let's create a new environment
    env = VirtualEnvironment()
    # let's create a new node
    node = Node("https://www.google.com", None, 0)
    # save the node
    env.saveNode(node)
    # let's create a new node
    node = Node("https://www.google.com", "https://www.google.com", 1)
    # save the node
    env.saveNode(node)