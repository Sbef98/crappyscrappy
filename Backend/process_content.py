from flask import Flask, request
from flask_cors import CORS
import json
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.append("/home/jovyan/crappyscrappy/Agents")
from parseQuery import ParseQuery

from parseServerClient import ParseServerClient, LiveQueryClient

queryWeCareAbout = "Ingegneria Informatica AI IA Machine Learning Data Science Data Mining Big Data"


# let's init the parse server client
with open("/home/jovyan/crappyscrappy/Agents/environment.json", "r") as config:
    # load it as a json object
    config = json.load(config)
    
# initialize the parse server client
parseClient = ParseServerClient(config["serverURL"], config["appId"], config["restApiKey"])

def preprocess_node(node):
    isUpdate = False
    if("objectId" not in node or not node["objectId"]):
        # we need to try to fetch a node with same url. In such case, this is not the first time we see this node
        query = ParseQuery("Node")
        query.equalTo("url", node["url"])
        result = parseClient.query(query)
        
        if(result and len(result) > 0):
            result[0]["parent_node"] = node["parent_node"]
            result[0]["agent"] = node["agent"]
            result[0]["content"] = node["content"]
            isUpdate = True
            return node, isUpdate
    
    # now we can procede manipulating the node data
    
    if("parent_nodes" not in node or not node["parent_nodes"]):
        node["parent_nodes"] = []
    
    if("agents" not in node or not node["agents"]):
        node["agents"] = []
    
    if("parent_node" in node and node["parent_node"]):
        current_parent = node["parent_node"]
        query = ParseQuery("Node")
        query.equalTo("url", current_parent)
        result = parseClient.query(query)
        
        if(result and len(result) > 0):
            node_to_add = result[0]
            # let's check if the parent node is already among the parent nodes
            if(node_to_add["objectId"] not in [parent["objectId"] for parent in node["parent_nodes"]]):
                pointer_to_parent = parseClient.getPointerToObject(result[0], "Node")
                node["parent_nodes"].append(pointer_to_parent)
        
    if("agent" in node and node["agent"]):
        agent = node["agent"]
        query = ParseQuery("Agent")
        query.equalTo("objectId", agent)
        result = parseClient.query(query)
        
        if(result and len(result) > 0):
            agent_to_add = result[0]
            # let's check if the agent is already among the agents
            if(agent_to_add["objectId"] not in [agent["objectId"] for agent in node["agents"]]):
                pointer_to_agent = parseClient.getPointerToObject(result[0], "Agent")
                node["agents"].append(pointer_to_agent)
    
    return node, isUpdate
            
        

def process_content(content, queryOfInterest):
# we will use a simple cosine similarity approach to this problem: https://www.machinelearningplus.com/nlp/cosine-similarity/
# soft cosine would be a better metric, but this is not the place to talk about it

    #let's make content and queryOfInterest case isensitive
    content = content.lower()
    queryOfInterest = queryOfInterest.lower()
    
    docs = [content, queryOfInterest]
    count_vectorizer = CountVectorizer(stop_words="italian")
    count_vectorizer = CountVectorizer()
    sparse_matrix = count_vectorizer.fit_transform(docs)
    doc_term_matrix = sparse_matrix.todense()
    
    df = pd.DataFrame(
    doc_term_matrix,
    columns=count_vectorizer.get_feature_names_out(),
    index=["content", "queryOfInterest"],
    )
    
    # to keep it very simple, each element should be 1 if present and 0 if not
    df[df > 0] = 1
    return cosine_similarity(df, df)

app = Flask(__name__)

CORS(app = app, resources={r"/*": {"origins": ["*"]}})
@app.route('/', methods = ["PUT", "POST", "GET"])
def api():
    data = request.get_json()
    object = data["object"]
    
    object, isUpdate = preprocess_node(object)
    if(isUpdate):
        parseClient.update("Node", object["objectId"], object)
        return json.dumps({
            "error": "Object already exists, updating it"
        })
    
    if("parent_node" not in object or not object["parent_node"]):
        object["contentQuality"] = 1.0
        
    # check if content is set
    elif "content" in object and object["content"]:
        content = object["content"]
        # delete content from object
        object["content"] = None
        
        object["contentQuality"] = process_content(content, queryWeCareAbout)[0][1]


    
    return json.dumps({
        "success": object
    })
        

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)