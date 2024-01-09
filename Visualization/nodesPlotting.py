import dash
from dash import html, dcc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import json
import sys
import networkx as nx
import random
# let's add Agents folder to the path
sys.path.append("/home/jovyan/crappyscrappy/Agents")
# let's import the Parse Server Client
from parseServerClient import ParseServerClient
# and the live query client
from parseServerClient import LiveQueryClient
from parseQuery import ParseQuery

# Create a color map for the agents
agent_colors = {}

# let's create a new parse server client
with open('/home/jovyan/crappyscrappy/Agents/environment.json') as json_file:
    credentials = json.load(json_file)
    parse = ParseServerClient(credentials['serverURL'], credentials['appId'], credentials['restApiKey'])
    liveQuery = LiveQueryClient(credentials['appId'], credentials['clientKey'], credentials['serverURL'])

query = ParseQuery("Node")
query.include(["traversals", "traversals.agent"])

# Sample data 
nodes = parse.query(query)

# Create nodes and edges for the graph
node_ids = {node['url']: idx for idx, node in enumerate(nodes)}
edges = []
edge_colors = []
for node in nodes:
    for traversal in node['traversals']:
        target_node = node['url']
        source_node = traversal['parent_node']
        if(not source_node in node_ids):
            continue
        edges.append((node_ids[source_node], node_ids[target_node]))
        agent = traversal['agent']['objectId']  # Adjust this line as needed to get the agent name
        if agent not in agent_colors:
            # Assign a random color to the agent
            agent_colors[agent] = "#"+''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        edge_colors.append(agent_colors[agent])

# Create a new directed graph
G = nx.DiGraph()

# Add nodes to the graph
for node in nodes:
    G.add_node(node['url'])

# Add edges to the graph and figure
for idx, edge in enumerate(edges):
    G.add_edge(nodes[edge[0]]['url'], nodes[edge[1]]['url'])

# Compute the layout
pos = nx.spring_layout(G, scale=2)

# Create the graph figure
fig = go.Figure()
fig.update_layout(height=4000)

# Calculate in-degrees
in_degrees = G.in_degree()

# Add nodes to the figure
for node in G.nodes:
    fig.add_trace(go.Scatter(x=[pos[node][0]], y=[pos[node][1]], mode='markers', marker=dict(size=in_degrees[node]*10), text=[node], hoverinfo='text', showlegend=False))

# Create a reverse lookup dictionary for agent_colors
color_to_agent = {v: k for k, v in agent_colors.items()}

# Create lists to hold line and annotation data
lines = []
annotations = []

for idx, edge in enumerate(edges):
    agent_name = color_to_agent[edge_colors[idx]]
    lines.append(go.Scatter(
        x=[pos[nodes[edge[0]]['url']][0], pos[nodes[edge[1]]['url']][0]],
        y=[pos[nodes[edge[0]]['url']][1], pos[nodes[edge[1]]['url']][1]],
        mode='lines',
        line=dict(width=1, color=edge_colors[idx]),
        hoverinfo='text',
        hovertext=f"From: {nodes[edge[0]]['url']}<br>To: {nodes[edge[1]]['url']}<br>Agent: {agent_name}",
        showlegend=False
    ))
    annotations.append(dict(
        ax=pos[nodes[edge[0]]['url']][0],
        ay=pos[nodes[edge[0]]['url']][1],
        axref='x',
        ayref='y',
        x=pos[nodes[edge[1]]['url']][0],
        y=pos[nodes[edge[1]]['url']][1],
        xref='x',
        yref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor=edge_colors[idx]
    ))

# Add all lines and annotations in a single call
fig.add_traces(lines)
fig.update_layout(annotations=annotations)
# Dash app layout
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True)