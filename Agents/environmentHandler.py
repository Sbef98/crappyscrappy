import json
from parseServerClient import ParseServerClient, LiveQueryClient
from parseQuery import ParseQuery

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
        # we can simply use create node because anyway it will be translate into a save. Our primary key is the
        # URL, therefore any node with the same URL will be overwritten as if it was an update.
        self.client.create("Node", node)
        
    def initializeAgent(self, updateCallBack):
        #let's create a new agent
        agent = {
            "name": "agent",
            "state": "idle",
            "current_url": None,
            "current_depth": None,
            "overallPathQuality": 0,
        }
        # let's save the agent
        response = self.client.create("Agent", agent)
        # let's merge the response with the agent
        agent.update(response)
        self.runAgentLiveQuery(agent, updateCallBack)
        return agent
    
    def runAgentLiveQuery(self, agent, callBack):
        # let's create the query
        query = ParseQuery("Agent")
        query.equalTo("objectId", agent["objectId"])
        # let's subscribe to the query
        liveQueryClient = LiveQueryClient(self.config["appId"], self.config["clientKey"], self.config["serverURL"])
        liveQueryClient.subscribe("Agent", callBack, query)   
        


if __name__ == "__main__":
    # let's create a new environment
    env = VirtualEnvironment()
    # let's create a new agent
    agent = env.initializeAgent()
    print(agent)
    