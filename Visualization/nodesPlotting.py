import networkx as nx
import matplotlib.pyplot as plt
# let's import from the agents folder the eparse server client class
from Agents.parseServerClient import ParseServerClient
import json


# Create a directed graph
G = nx.DiGraph()

with open("environment.json", "r") as config:
            # load it as a json object
    config = json.load(config)

# let's create the parse server client
client = ParseServerClient(config["serverURL"], config["appId"], config["restApiKey"])
# let's get all the nodes
nodes = client.getAll("Node")


# Add nodes and edges to the graph
# For example, if 'parent_url' is the parent of 'url', you can add an edge from 'parent_url' to 'url'
for node in nodes:
    G.add_edge(node["parent_url"], node["url"])

# Draw the graph
nx.draw(G, with_labels=True)
plt.show()