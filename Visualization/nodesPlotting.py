import dash
from dash import html, dcc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import json
import sys
# let's add Agents folder to the path
sys.path.append("../Agents")
# let's import the Parse Server Client
from parseServerClient import ParseServerClient
# and the live query client
from parseServerClient import LiveQueryClient
import threading,random
from numpy import inf
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Store(id='nodes', storage_type='session'),  # Store nodes data
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=30000,  # Update every 5 seconds
        n_intervals=0
    )
])

@app.callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals')  # Update graph when interval changes
)
def update_graph(n):
    # Fetch nodes data here
    global nodes
    print(len(nodes))
    # Create nodes and edges based on updated data
    # Inside the callback function for updating the graph
    node_trace = go.Scatter(
        x=[node['depth'] for node in nodes],
        y=[node['children_nodes'] for node in nodes],
        hovertext=[f"URL: {node['url']}<br>Parent URL: {node['parent_node']}<br>Depth: {node['depth']}" for node in nodes],
        mode="markers",
        hoverinfo="text",
        marker=dict(color='blue', size=6),  # Decrease marker size
    )

    edge_trace = go.Scatter(
        x=[node['depth'] for node in nodes],
        y=[node['children_nodes'] for node in nodes],
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='Real-time Graph of Nodes',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
                    autosize=True,  # This will make the graph responsive
                    height=inf,  # This will set the height of the graph to 800 pixels
                    width=inf  # This will set the width of the graph to 1200 pixels
                )
            )

    return fig

def liveQueryUpdateCallback(operation, data):
    if operation == 'connected':
            print("Connected to LiveQuery")
    elif operation == 'error':
        print(f"Error: {data}")
    elif operation == 'subscribed':
        print(f"Subscribed to query: {data}")
    elif operation == 'create':
        print("new node created!")
        nodes.append(data)
    elif operation == 'update':
        for i in range(len(nodes)):
            if nodes[i]['url'] == data['url']:
                nodes[i] = data
                break
    elif operation == 'delete':
        print("Node deleted!")
        for i in range(len(nodes)):
            if nodes[i]['url'] == data['url']:
                del nodes[i]
                break

if __name__ == '__main__':
    with open('../Agents/environment.json', 'r') as f:
        environment = json.load(f)
    # let's create the ParseServerClient object
    parseServerClient = ParseServerClient(environment['serverURL'], environment['appId'], environment['restApiKey'])
    nodes = parseServerClient.queryAll("Node")
    # print(nodes)
    # let's crtate the live query client
    live_query_client = LiveQueryClient(environment['appId'], environment['clientKey'], environment['serverURL'])
    # # start live_query_client.subscribe("Node", liveQueryUpdateCallback) on different thread
    thread = threading.Thread(target=live_query_client.subscribe, args=("Node", liveQueryUpdateCallback))
    thread.start()  # Start the thread
    app.run_server(debug=True)