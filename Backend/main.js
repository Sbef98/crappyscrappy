// let's define a model for the class Node
const Node = Parse.Object.extend("Node", {
    // instance properties
    url: {
        get: function () {
            return this.get("url");
        },
        set: function (value) {
            this.set("url", value);
        }
    },
    children_nodes: {
        get: function () {
            return this.get("children_nodes");
        },
        set: function (value) {
            this.set("children_nodes", value);
        }
    },
    parent_url: {
        get: function () {
            return this.get("parent_url");
        },
        set: function (value) {
            this.set("parent_url", value);
        }
    },
    depth: {
        get: function () {
            return this.get("depth");
        },
        set: function (value) {
            this.set("depth", value);
        }
    },
    content: {
        get: function () {
            return this.get("content");
        },
        set: function (value) {
            this.set("content", value);
        }
    },
    content_language: {
        get: function () {
            return this.get("content_language");
        },
        set: function (value) {
            this.set("content_language", value);
        }
    },
    updatedAt: {
        get: function () {
            return this.get("updatedAt");
        },
        set: function (value) {
            this.set("updatedAt", value);
        }
    },
    createdAt: {
        get: function () {
            return this.get("createdAt");
        },
        set: function (value) {
            this.set("createdAt", value);
        }
    },
    lastTraversedAt: {
        get: function () {
            return this.get("lastTraversedAt");
        },
        set: function (value) {
            this.set("lastTraversedAt", value);
        }
    },

    // Instance methods
    initialize: function (attrs, options) {
        this.url = attrs.url;
        this.children_nodes = attrs.children_nodes;
    }
}, {
    // Class methods
    new: function (attrs, options) {
        return new Node(attrs, options);
    }
});

// let's add a before save for the clas Node
Parse.Cloud.beforeSave("Node", async function (request, response) {
    // let's check if a node with same url already exists
    var query = new Parse.Query("Node");
    query.equalTo("url", request.object.get("url"));
    await query.first({
        success: function (object) {
            if (object) {
                // if it exists, we return an error
                request.object.id = object.id;
                response.success();
            } else {
                // if it doesn't exist, we continue the save
                response.success();
            }
        },
        error: function (error) {
            response.error("Could not validate existence for this node object.");
        }
    });
    
    // links = request.object.get("children_nodes");
    
    // if(!links)
    //     return request.object;

    // const linksMap = {};
    // links.forEach(link => {
    //     linksMap[link.get("url")] = link;
    // });

    // const existingDaughterUrlsQuery = new Parse.Query("Node");
    // linksUrls = linksMap.keys();
    // existingDaughterUrlsQuery.containedIn("url", linksUrls);

    // const existingDaughterUrls = await existingDaughterUrlsQuery.find({useMasterKey: true});

    // // now i can add the correct id to each one of the links
    // existingDaughterUrls.forEach(existingDaughterUrl => {
    //     const existingDaughterUrlId = existingDaughterUrl.objectId;
    //     linksMap[existingDaughterUrl.get("url")].objectId = existingDaughterUrlId;
    // });

    // const linksToUpdate = linksMap.values();
    

    // const newNodes = nonExistingDaugtherUrls.map(link => {
    //     const node = new Parse.Object("Node");
    //     node.set("url", link.get("url"));
    //     node.set("parentQualityStatement", link.get("parentQualityStatement"));
    //     return node;
    // });
    // const savedNewNodes = await Parse.Object.saveAll(newNodes);
    // request.object.set("children_nodes", existingDaughterUrls.concat(savedNewNodes));
    return request.object;
});

// let's add a after FInd for the class Node, to map the children_nodes to children_nodes
Parse.Cloud.afterFind("Node", async function (request) {
    const nodes = request.objects;
    // nodes.forEach(node => {
    //     const daughterNodes = node.get("children_nodes");
    //     if(daughterNodes)
    //         node.set("children_nodes", daughterNodes.map(daughterNode => daughterNode.get("url")));
    // });
    return nodes;
});