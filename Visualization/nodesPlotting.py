import networkx as nx
import matplotlib.pyplot as plt
# let's import from the agents folder the eparse server client class
import sys
sys.path.insert(0, '../Agents')

from parseServerClient import ParseServerClient
import json
from flask import Flask, send_file
import networkx as nx
import io

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
        <body>
            <img id="plot" src="/plot" alt="Plot">
            <script>
                setInterval(function(){
                    document.getElementById('plot').src = "/plot?" + new Date().getTime();
                }, 5000);
            </script>
        </body>
    </html>
    """
@app.route("/plot")
def plot():
    # Create a directed graph
    G = nx.DiGraph()

    with open("environment.json", "r") as config:
            # load it as a json object
        config = json.load(config)

    # let's create the parse server client
    client = ParseServerClient(config["serverURL"], config["appId"], config["restApiKey"])
    # let's get all the nodes
    nodes = client.queryAll("Node")


    # Add nodes and edges to the graph
    # For example, if 'parent_url' is the parent of 'url', you can add an edge from 'parent_url' to 'url'
    for node in nodes:
        # if the node has a parent
        if node["parent_url"] is not None:
            # add the edge
            G.add_edge(node["parent_url"], node["url"])
        else:
            # add the node
            G.add_node(node["url"])

    # Draw the graph
    plt.figure(figsize=(8, 6))
    nx.draw(G, with_labels=True)

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    return send_file(img, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

# # Create a directed graph
# G = nx.DiGraph()



# # Draw the graph
# nx.draw(G, with_labels=True)
# plt.show()