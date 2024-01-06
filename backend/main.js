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
    daughter_nodes: {
        get: function () {
            return this.get("daughter_urls");
        },
        set: function (value) {
            this.set("daughter_urls", value);
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
        this.daughter_urls = attrs.daughter_urls;
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
    links = request.object.get("daughter_urls");
    
    if(!links)
        return request.object;

    const existingDaughterUrlsQuery = new Parse.Query("Node");
    existingDaughterUrlsQuery.containedIn("url", links);
    const existingDaughterUrls = await existingDaughterUrlsQuery.find();
    const nonExistingDaugtherUrls = links.filter(link => !existingDaughterUrls.some(existingLink => existingLink.get("url") === link));
    const newNodes = nonExistingDaugtherUrls.map(url => {
        const node = new Parse.Object("Node");
        node.set("url", url);
        return node;
    });
    const savedNewNotes = await Parse.Object.saveAll(newNodes);
    request.object.set("daughter_nodes", existingDaughterUrls.concat(savedNewNotes));
    return request.object;
});

// let's add a after FInd for the class Node, to map the daughter_urls to daughter_nodes
Parse.Cloud.afterFind("Node", async function (request) {
    const nodes = request.objects;
    nodes.forEach(node => {
        const daughterNodes = node.get("daughter_nodes");
        if(daughterNodes)
            node.set("daughter_urls", daughterNodes.map(daughterNode => daughterNode.get("url")));
    });
    return nodes;
});