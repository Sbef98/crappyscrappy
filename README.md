# crappyscrappy
Let's try to surf the net with the ants. Maybe we could say let's ant the web?
Whatever.

## Environment
The "true" environment is simply the web, where the nodes are the classical websites and the paths are givben based on the websites interconnections. The usual web crawlers context. On the other hand, to actually leave traces in such environment, what we may need would be a solid platform on which virtualizing the real environment, something that could actually be modified and manipulated.

A possibility could be a fully functional backend, and as usual i am thinking about you parse server, something that can easily scale up and allow for complex tasks without having to waste time. This could be great as long as we are just experimenting, becuase speed is not a problem, but may be a bulky bottleneck when comes to actual data mining. In fact, if we had thousands of agents all working at the same time, we may want something more lightweight, while using parse or other backends and database engines for acutal persistence/data analysis.

### Envinronemnt duty:
[] Make the identification ofthe single web page indipendent by the database object id. Therefore, use url as its primary key (not really possibile within parse server, needs a before save and after find)
[] updatedAt field it's automatically incremented everytime we update a node, but the time update may be triggered by the parent updating the informations about its child (e.g. its quality statement). What we should rather do, is a "surf date", and therefore we should update it only when we surf it.
[] When an agent wants to sniff the quality of a direction (e.g. querying one of the webistes to check if it should follow that path), the environment should already reply with a "summarized" object, therefore if multiple parents made a quality statement for a certain node, we should return the object with one single parent quality statement with the weighted mean sqaure root.
[] check bi-directional links between kids and parents
[] when a parent is updated, apart updating its children we must also remove the info from such node on the children nodes that are not children anymore
[] foreach agent, create its own stats to know the overall quality of the computed path

## Agents duty
Let's try to sum up what an agent should do more or less.

 [x] Open an assigned website
 [x] Get all it's content and try to understand what it is about and what info are useful
 [x] Get all it's link
 [] contextualized the links (is it good based on the current page description of the link?)
 [] Check current page language
 [ ] Split the links in categories
     - Same domain
     - Same subdomain
     - Else
[] Understand if one parent is double linked with his kid
 [ ] For each link, get if it is already visited and in case get it's stats
 [ ] When choosing a direction, it should first of all filter at least a bit to do not query all of them to the environment
 [ ] Choose the best link to follow multiplying various factors, in a random way -> ofc take into account the quality of the link, also by how its parents stated it.
 [] understand when going home (also through live query)

[] keep track of his current overall path quality through livequery!

### Current nodes structure:
    edge = {
        "agent": self.agentInfo,
        "parent_node": parent_node,
        "traversal_depth": depth,
        "parentQualityStatement": parentQualityStatement,
        "updatedAt": datetime.datetime.now(),
        "parent_node_quality": value
    }
        
    node = {
        "url": url,
        "children_nodes": len(linksWithQuality),
        "traversals": [edge],                  # arrays becuase more than one agent may land on the same node
    }

#### Extra
[] What if the same link is stated more than once? we need to contextualize it with some sort of mean!
[] Multiple parents, how do we handle? E.g. multiple parents state different things on the same link, the parentQualityStatements should be computed also on the quality of the parent itself, therefore should be a mean square route evalutation based weighted by the parent's quality itself

### Calc of probability
The probability of choosing a link should have different weights, based on multiple facts:
- How fresh is the website
- If it was already considered good or bad
- How much time ago it was followed previously
- How much steps did i already take (to not make it too far, further i go more options i will have and more complex  it will be to make the way back home)
- If it is from same domain/subdomain or not
- The quality of the content compared to what i already have found and what i am looking for
- How much content did I already find on the path and how much info am i carrying currently

### Understanding information quality
Probably, one of the best things to do is that the ant finds the food (content), acquires it (scrapes and saves in the "virtual environment" aka our backend/server/database),and then it will be the environment to tell the hunt how good i the content she already found notifying her when the evaluation is done. So the ant stays simple and fast.

## Virtual Environment duties
<del> For example, the pheromons should "evaporate" as time passes. Therefore, there should be something like a scheduled job that "cleans" that takes care of evaporation, and there should also be some sort of automatic function (or more agents dedicated to that?) that updates path prizes whenever an ant acutally find good food or not once it reaches for the end of its path.</del>
Questo non ha senso. Può essere sufficiente un timestamp che mi permetta, di volta in volta, di calcolare quale sia il valore da prendere in considerazione.

***WATCHOUT***: I enalbed client class creation

# How to solve the problem of actively retrieving the updates about the path quality
Whenever an agent starts tracing a path, the overall path quality can be easily updated b the environment who should track what are the "sites" visited by the current agent (therefore each agent should have an id, or a single path should have an id). The overall quality of the agent's path can be updated to the agent itself (e.g. to understand if the quantity/quality of the informations retrieved till that moment is good enough), and the agent can be easily updated in real time via livequery reading the elements/events regarding is own path!


# Computing weights for list of links

## Informations from within one node to other nodes
To each link in the currently evaluated page should be related to a weight, which is the probability to pick it. What we must consider, to explore the most, is:

[x] Am i on the same (sub)domain? If so, i should give a boost to such website only if i am currently having a very high quality perspective about it. Anyway, for now, the chances order should be something like that:
    - 3 times higher probability to pick a different domain: it means new fresh info
    - 2 times to pick a different subdomain: it means same domain but maybe differnt informarions
    - 1 time to pick sam subdomain. Maybe a new page could give as more sauce.

So, i assign 1,2,3 as starting weights for each one of the links.

[x] The currentnode age could be an extra penalizer for internal nodes, but this time it should be a value between 0.5 and 1.5, so that if very well updated websites should be taken into consideration more in depth

[x] How well is my current website all these new explorable nodes? Let's have a sentiment analysis of the words before such link. The sentiment analysis should return a value between -1 and 1, which gives us a "very bad" to "very positive" ratio. 
At this point, we get these evaluations multiplied by the externality weighs. An external domain should get then the following impact:
    - Very positive external url => sentiment returns 1 => 1*3 = 3
    - Neutral external site: 0*3 = 0
    - Very negative external site: -1 * 3 = -3, should not be picked at all!

[x] Turn the -3 to 3 score into 0 to 6. So we stay positive ;)

[x] We should also check how old is the website. We should then get when this page was updated the last time. If it was a long time ago, the website should get a lower score. It really depends on what we consider "old". For example, if we want very fresh news, we need to penaliza a lot websites older than one week, by something like 50%  of tis total score if it hits the limit, on the other hand leaving 100% if it is from now. **THIS WORKS ONLY IF YOU ARE ALREADY INSIDE AND SCRAPING BODOH**, unless we get a sneak peak through a head request tbh. Shall skip for now, it is toooooo slow....

[x] Let's normalize the current weights! So we have a value between 0 and 1, which is our probability weights.


## Informations that can be computed accessing the environment
But we can get more info if some nodes where already discovered. For example, if a node was already explored, we can get to know some info:
- How many "in" edges it has (len(traversals) but from different parents)
- The value of each edge, which can tell us a lot of stuff, for example:
    - parentQualityStatement -> how much confidence the agent who traced such edge had at the moment of getting to this node
    - parent_node -> It could be interesting knowing how much authority it had the site pointing to this one. It's a complicated metric! Further we go more complex it could get such computation. **Maybe we should compute the "in" authority every time we go down!** For examnple,  adding to parentQualityStatement the parentAuthorityValue which should be the final overall probability that that node had to be picked by the agent who picked it.
    - agent -> the agent who traced such edge. An agent should be coming with a "overall evaluation" of what it was able to mine. Also the overall trip value should be considered respectively to how much deep the agent had to go. It may have gathered a lot of informations, but if it had to go through 150 nodes is less valuable than one who went through just 10.
    - traversal_depth -> how deep was this node on the overall trip? Idk if this is of any usefulness 
    - createdAt -> The time of the edge creation. How much time ago was this visit? If it is a lot, it's not so good anymore
- The age of the node last time you scraped it...
- The overall evaluation of the content quality performed by the environment itself?

### Let's explain this better
[] Compute for each edge a value based on the stats
[] Multiply that edge value by as eight given by the age of the edge
[] Sum the overall value of the edges
[] The total amount of traversal will not given by the exact count but by the intensity of the pheromone on that node rapresented by the previous count
[] The node itself should rather have a value coz yes computed by the environment.
**traversals should be deleted after a while coz meaningless**