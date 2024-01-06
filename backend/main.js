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