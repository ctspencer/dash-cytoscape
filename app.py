#Imports necessary libraries, files, and assigns handles

import json

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

import dash_cytoscape as cyto
from demos import dash_reusable_components as drc

app = dash.Dash(__name__)
server = app.server


# ###################### DATA PREPROCESSING ######################
#pandas is used to read in a tab-delimited data frame and store it as the variable network_data
#the data frame contains text scraped from the 2019 IMHC Proceedings and can be easily modified

network_data = pd.read_csv('demos/data/test_network.txt', sep='\t')


#Each colmumn in the pandas dataframe is assigned a variable (e.g. source, target, flavtext)
#Note that source and target refers to the directionality of nodes and respective edges. It reads from source to target and creates a linkage
#flavtext refers to the associated text of a specific target (description of best practice)
source = network_data['Source']
target = network_data['Target']
flavtext = network_data['Text']

#Columns are recombined with a tab delimiter
source_target_flavtext = source + "\t" + target + "\t" + flavtext


#Each row of the intial dataframe is converted to a list, you'll see why later
edges = source_target_flavtext.to_list()
nodes = set()



following_node_di = {}  # user id -> list of practices they are following
following_edges_di = {}  # user id -> list of cy edges starting from practice id
followers_node_di = {}  # user id -> list of practices (cy_node format)
followers_edges_di = {}  # user id -> list of cy edges ending at practice id
cy_edges = []
cy_nodes = []



for edge in edges:
    #split the combined text frame by our tab delimiter into the respective variables
    source, target, flavtext = edge.split("\t")

    #constructs dictionaries of edges, targets, and sources for visualization
    cy_edge = {'data': {'id': source+target, 'source': source, 'target': target}}
    cy_target = {"data": {"id": target, "text": flavtext}}
    cy_source = {"data": {"id": source, }}


    #The rest of the lines for this chunk of code build dictionaries to keep track of
    #the sources, targets, and edges needed for visualization
    if source not in nodes:
        nodes.add(source)
        cy_nodes.append(cy_source)
    if target not in nodes:
        nodes.add(target)
        cy_nodes.append(cy_target)

    # Process dictionary of following
    if not following_node_di.get(source):
        following_node_di[source] = []
    if not following_edges_di.get(source):
        following_edges_di[source] = []

    following_node_di[source].append(cy_target)
    following_edges_di[source].append(cy_edge)

    # Process dictionary of followers
    if not followers_node_di.get(target):
        followers_node_di[target] = []
    if not followers_edges_di.get(target):
        followers_edges_di[target] = []

    followers_node_di[target].append(cy_source)
    followers_edges_di[target].append(cy_edge)


#This is the very first node displayed, the source of all other nodes
genesis_node = {'data': {'id': 'Major Topics', 'label': 'Major-Topics', 'extra': " "}}
genesis_node['classes'] = "genesis"
default_elements = [genesis_node]


#This is a stylesheet used for the base visualizations of nodes and edges
default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.65,
            'z-index': 9999
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "bezier",
            "opacity": 0.45,
            'z-index': 5000
        }
    },
    {
        'selector': '.followerNode',
        'style': {
            'background-color': '#0074D9'
        }
    },
    {
        'selector': '.followerEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#0074D9"
        }
    },
    {
        'selector': '.followingNode',
        'style': {
            'background-color': '#393e46',
            "label": "data(id)"

        }
    },
    {
        'selector': '.followingEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#00adb5",
        }
    },
    {
        "selector": '.genesis',
        "style": {
            'background-color': '#222831',
            "border-width": 2,
            "border-color": "#393e46",
            "border-opacity": 1,
            "opacity": 1,
            "width": 50,
            "height": 50,

            "label": "data(label)",
            "color": "#000000",
            "text-opacity": 1,
            "font-size": 15,
            'z-index': 9999
        }
    },
    {
        'selector': ':selected',
        "style": {
            "border-width": 2,
            "border-color": "black",
            "border-opacity": 1,
            "opacity": 1,
            "width": 50,
            "height": 50,
            "label": "data(label)",
            "color": "black",
            "font-size": 15,
            'z-index': 9999
        }
    }
]

# ################################# APP LAYOUT ################################

#Styles created for use by html.Div 
styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'overflow-x': 'auto',
        'overflow-wrap': 'break-word',
        'border': 'thin lightgrey solid',
        'width' : '90vw'
    },
    'tab': {'height': 'calc(98vh - 80px)', 'width': '90vw'}
}

#Call cytoscape to construct the layout and elements of the graph
app.layout = html.Div([
    html.Div(className='eight columns', children=[
        cyto.Cytoscape(
            id='cytoscape',
            elements=default_elements,
            layout={ "name": "cose"},
            stylesheet=default_stylesheet,
            style={
                'height': '95vh',
                'width': '100%',
                'word-break': 'break-word',
                'overflow-wrap': 'break-word'
            }
        )
    ]),
#Create a tab to display data associated with a node (calls dictionary components)
    html.Div(className='four columns', children=[
        dcc.Tabs(id='tabs', children=[
            dcc.Tab(label='Tap Data', children=[
                html.Div(style=styles['tab'], children=[
                    html.P('Node Data'),
                    html.Pre(
                        id='tap-node-data-json-output',
                        style=styles['json-output']
                    ),
                ])
            ])
        ])

    ])
])


# ############################## CALLBACKS ####################################
#Callbacks are unique to the cytoscape library and allow interactive updating
#more information on callbacks can be found in the Dash Cytoscape reference guide    


#dump data assocaited with a node into a textbox
@app.callback(Output('tap-node-data-json-output', 'children'),
              [Input('cytoscape', 'tapNodeData')])
def displayTapNodeData(data):


        return json.dumps(data, indent=2)


#The following chunk of code keeps track of which nodes have been expanded
#based on the dictionaries constructed at the beginning
@app.callback(Output('cytoscape', 'elements'),
              [Input('cytoscape', 'tapNodeData')],
              [State('cytoscape', 'elements')])
def generate_elements(nodeData, elements):
    if not nodeData:
        return default_elements

    # If the node has already been expanded, we don't expand it again
    if nodeData.get('expanded'):
        return elements

    # This retrieves the currently selected element, and tag it as expanded
    for element in elements:
        if nodeData['id'] == element.get('data').get('id'):
            element['data']['expanded'] = True
            break

    following_nodes = following_node_di.get(nodeData['id'])
    following_edges = following_edges_di.get(nodeData['id'])

    if following_nodes:
        for node in following_nodes:
            if node['data']['id'] != genesis_node['data']['id']:
                node['classes'] = 'followingNode'
                elements.append(node)

    if following_edges:
        for follower_edge in following_edges:
            follower_edge['classes'] = 'followingEdge'
        elements.extend(following_edges)

    return elements


if __name__ == '__main__':
    app.run_server(debug=True)
