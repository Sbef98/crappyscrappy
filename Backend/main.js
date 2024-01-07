Parse.Cloud.beforeSave("Node", async function (request) {
    if (!request.object.id) {
        // let's check if a node with the same URL already exists
        var query = new Parse.Query("Node");
        query.equalTo("url", request.object.get("url"));

        const existingNode = await query.first();
        if (existingNode) {
            // Update the existing object's fields
            existingNode.set("children_nodes", request.object.get("children_nodes"));
            existingNode.addAllUnique("traversals", request.object.get("traversals"));
            request.object = await existingNode.save();
            // Set the updated existing object back to request.object for saving
        }
    }
    return request.object;
});
