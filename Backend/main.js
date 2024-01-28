// let's create some paramters, Such parameters may be set from the dashboard. For testing purposes only, we can set them from here
const authorityPenalty = 0.5;
const nodeQualityThreshold = 0.04;  // minimum quality to consider good

// let's add an afterSave for the Node class
Parse.Cloud.afterSave("Node", async function (request) {
    // updating agent
    const current_agent = request.object.get("agent");
    // fetch the agent
    if (current_agent) {
        const query = new Parse.Query("Agent");
        const agent = await query.get(current_agent);

        // request.object.unset("agent"); # we should do this but fine for now, it will be a temp field

        // let's also add the node to the agent, because we need to know the overall path
        const agentNodeRelation = agent.relation("nodesInPath");
        agentNodeRelation.add(request.object);
        await agent.save();
    }
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
        const parents = node.get("parent_nodes") ?? [];

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
Parse.Cloud.beforeSave("Agent", async function (request) {
    // we need to compute the overall agent quality
    const agent = request.object;

    if(agent.relation("nodesInPath") == null)
        return request.object;

    const nodesQuery = agent.relation("nodesInPath").query();
    const nodes = await nodesQuery.find() ?? [];

    const numberOfNodes = nodes.length;

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

    const currentQuality = nodesContentQuality[-1] // let's check if it's under threshold. If so, we will penalize the agent
    if (currentQuality < nodeQualityThreshold) {
        median -= (nodeQualityThreshold - currentQuality);
    }

    agent.set("pathQuality", median);
    agent.set("numberOfNodesInPath", numberOfNodes);
});