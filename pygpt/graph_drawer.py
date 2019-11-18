"""GPT Graph drawing utils"""
from lxml import etree

import math
import matplotlib as mpl
mpl.use('Agg') # use no graphical backend
import matplotlib.pyplot as plt


def __prepare_nodes__(root):
    """
    robust to error graph builder
    """
    nodes = [] # list of nodes
    nodes_key = {} # dictionary linking node name to node index
    points = {'x':[], 'y': []} # point dictionary for geometric info

    element = root.xpath('/graph/node')
    # explore all nodes of the graph
    for elem in element:
        n_id = elem.get('id') # get node name
        node = {'refs': [], 'name': n_id} # create node
        ops = elem.xpath('./operator')
        if ops is not None:
            node['op'] = ops[0].text # extract operator text
        for src in elem.xpath('./sources/*'):
            # iterate all connected nodes
            r_id = src.get('refid') # get connected node id
            if r_id is None:
                # NOTE: in some rare cases the id is inside the node text
                r_id = src.text
            if r_id not in node['refs']:
                # add the connected node if needed (avoid multple connections)
                node['refs'].append(r_id)
        nodes.append(node) # add node to list of nodes
        nodes_key[n_id] = len(nodes) - 1 # connect id with index

    element = root.find('.//applicationData[@id="Presentation"]')
    # explore the nodes presentation to respect the correct graphical layout
    if element is None:
        return nodes, nodes_key, points

    key = '' # node id
    index = 0 # node index for workaround of line 58
    for node in element.iter():
        # iterate the nodes
        if node.tag == 'node':
            key = node.get('id')  # get node id
        if node.tag == 'displayPosition':
            # extract geometric info and added it to the node
            if key in nodes_key:
                ind = nodes_key[key]
                nodes[ind]['x'] = float(node.get('x'))
                nodes[ind]['y'] = float(node.get('y'))
                points['x'].append(nodes[ind]['x'])
                points['y'].append(nodes[ind]['y'])
            elif index < len(nodes) and not 'x' in nodes[index]:
                """
                NOTE: this is a workaround for some hand made graph
                in wich the Presentation node ids are not the same as the
                real graph nodes and so I use the index of the node instead
                """
                nodes[index]['x'] = float(node.get('x'))
                nodes[index]['y'] = float(node.get('y'))
                points['x'].append(nodes[index]['x'])
                points['y'].append(nodes[index]['y'])
            index += 1
    return nodes, nodes_key, points


def __draw_nodes__(axis, nodes, scale):
    """
    draw nodes boxes
    """
    for node in nodes:
        oper = node['op'] if 'op' in node else node['name']
        scaled_x = node['x'] * scale
        scaled_y = node['y'] * scale
        text = axis.annotate(oper, xy=(scaled_x, scaled_y), xycoords="data",
                             va="center", ha="center",
                             bbox=dict(boxstyle="round", fc="w"))
        node['text'] = text


def __draw_arrows__(axis, nodes, keys):
    """
    draw arrows from sources to target nodes
    """
    for node in nodes:
        ttxt = node['text']
        for ref in node['refs']:
            if ref in keys:
                source = nodes[keys[ref]]
                stxt = source['text']
                axis.annotate("",
                              xy=(0.0, 0.5), xycoords=ttxt,
                              xytext=(1.0, 0.5), textcoords=stxt,
                              arrowprops=dict(arrowstyle="-|>", fc=(0, 0, 0),
                                              connectionstyle="arc3"),
                             )


def draw(source, dest, dpi=90):
    """
    Draw gpt graph

    Parameters
    ----------
     - source: source xml graph path
     - dest: graph image destination path
     - dpi: resolution of the resulting image
    """
    with open(source, 'r') as file:
        root = etree.fromstring(file.read())
        nodes, keys, points = __prepare_nodes__(root)
        if not points:
            return

        # compute the size of the plot
        real_w = max(points['x']) - min(points['x'])
        real_h = max(points['y']) - min(points['y']) + 20
        ratio = real_h / real_w
        scale = 1.0 / real_w

        _, axis = plt.subplots(figsize=(5, 6*ratio), dpi=dpi)

        # set limits
        plt.xlim([min(points['x']) * scale, max(points['x']) * scale])
        plt.ylim([min(points['y']) * scale - 0.05, max(points['y']) * scale + 0.05])

        # draw nodes
        __draw_nodes__(axis, nodes, scale)
        # draw arrows
        __draw_arrows__(axis, nodes, keys)

        plt.axis('off')
        plt.savefig(dest, transparent=True)
