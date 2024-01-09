Parse.Cloud.beforeSave("Node", async function (request) {
    if (!request.object.id) {
        // updating agent
        const currentTraversal = request.object.get("traversals")[0];
        const fetchedTraversal = await currentTraversal.fetch();
        const currentAgent = fetchedTraversal.get("agent");
        // fetch the agent
        if (currentAgent) {
            const fetchedAgent = await currentAgent.fetch();
            fetchedAgent.set("current_url", request.object.get("url"));
            fetchedAgent.set("current_depth", currentTraversal.get("traversal_depth"));
            fetchedAgent.save();
        }

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

//let's create a parse job
Parse.Cloud.job("checkAgentsLiveness", async function (request) {
    // find the agents that haven't been updateed in the last 5 minutes
    const query = new Parse.Query("Agent");
    query.lessThan("updatedAt", new Date(Date.now() - 5 * 60 * 1000));
    const agents = await query.find();
    // let's change their status to "Zombie"
    agents.forEach(async agent => {
        agent.set("status", "Zombie");
    });
    await Parse.Object.saveAll(agents);
});