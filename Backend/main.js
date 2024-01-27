// let's create some paramters, Such parameters may be set from the dashboard. For testing purposes only, we can set them from here
const authorityPenalty = 0.5;

Parse.Cloud.beforeSave("Node", async function (request) {

    if (!request.object.id) {
        // let's check if the node exists already
        const nodeQuery = new Parse.Query("Node");
        nodeQuery.equalTo("url", request.object.get("url"));
        const nodes = await nodeQuery.find();
        if (nodes && nodes.length > 0) {
            // we already have a node with this url
            // let's update it
            request.object.id = nodes[0].id;
        }
    }

    // updating agent
    const current_agent = request.object.get("agent");
    const current_parent = request.object.get("parent_node"); // it's an id!

    // fetch the agent
    if (current_agent) {
        const query = new Parse.Query("Agent");
        const agent = await query.get(current_agent);
        // let's add the agent to the node
        request.object.agents.addUnique("agents", agent);

        request.object.unset("agent");

        // let's also add the node to the agent, because we need to know the overall path
        const agentNodeRelation = agent.relation("nodesInPath");
        agentNodeRelation.add(request.object);
        await agent.save();
    }

    if (current_parent) {
        // fetch the parent
        const query = new Parse.Query("Node");
        query.equalTo("url", current_parent);
        const parent_node = await query.first();
        // let's add the parent to the node
        request.object.addUnique("parent_nodes", parent_node);
        request.object.unset("parent_node");
    }

    return request.object;
});

// before find for the node
Parse.Cloud.beforeFind("Node", async function (request) {
    const query = request.query;
    query.include("agents");
    query.include("parent_nodes");
});

// after find for the node
Parse.Cloud.afterFind("Node", function (request) {
    // let's just return parents_authorities, contentQuality and Agents Path Quality

    for (let node of request.objects) {
        const parents = node.get("parent_nodes");

        const parents_authorities = [];

        for (const parent of parents) {
            parents_authorities.push(parent.get("authority"));
        }

        const contentQuality = node.get("contentQuality");

        const agents = node.get("agents");
        const agentsPathQuality = [];
        for (const agent of agents) {
            agentsPathQuality.push(agent.get("pathQuality"));
        }

        const agents_depths = [];
        for (const agent of agents) {
            agents_depths.push(agent.get("depth"));
        }

        const url = node.get("url");

        node = {
            parents_authorities,
            contentQuality,
            agentsPathQuality,
            agents_depths,
            url
        }
    }
});

// let's do an afterFind for the Agent class
Parse.Cloud.afterFind("Agent", async function (request) {
    // we need to compute the overall agent quality
    for (const agent of request.objects) {
        const nodesQuery = agent.relation("nodesInPath").query();
        const nodes = await nodesQuery.find();

        // the overall agent quality is the median of the nodes contentQuality
        const nodesContentQuality = [];
        for (const node of nodes) {
            nodesContentQuality.push(node.get("contentQuality"));
        }

        // let's sort the array
        nodesContentQuality.sort();

        // let's compute the median
        let median = 0;
        if (nodesContentQuality.length % 2 === 0) {
            // even
            median = (nodesContentQuality[nodesContentQuality.length / 2 - 1] + nodesContentQuality[nodesContentQuality.length / 2]) / 2;
        } else {
            // odd
            median = nodesContentQuality[(nodesContentQuality.length - 1) / 2];
        }

        agent.set("pathQuality", median);
    }
});