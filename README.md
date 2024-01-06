# crappyscrappy
Let's try to surf the net with the ants. Maybe we could say let's ant the web?
Whatever.

## Environment
The "true" environment is simply the web, where the nodes are the classical websites and the paths are givben based on the websites interconnections. The usual web crawlers context. On the other hand, to actually leave traces in such environment, what we may need would be a solid platform on which virtualizing the real environment, something that could actually be modified and manipulated.

A possibility could be a fully functional backend, and as usual i am thinking about you parse server, something that can easily scale up and allow for complex tasks without having to waste time. This could be great as long as we are just experimenting, becuase speed is not a problem, but may be a bulky bottleneck when comes to actual data mining. In fact, if we had thousands of agents all working at the same time, we may want something more lightweight, while using parse or other backends and database engines for acutal persistence/data analysis.


## Agents duty
Let's try to sum up what an agent should do more or less.

 [] Open an assigned website
 [] Get all it's content and try to understand what it is about and what info are useful
 [] Get all it's link
 [] contextualized the links (is it good?)
 [] Split the links in categories
     - Same domain
     - Same subdomain
     - Else
 [] For each link, get if it is already visited and in case get it's stats
 [] Choose the best link to follow multiplying various factors, in a random way

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