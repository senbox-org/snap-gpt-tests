"""GPT Graph drawing utils"""
from lxml import etree

import matplotlib as mpl
mpl.use('Agg') # use no graphical backend
import matplotlib.pyplot as plt


def __prepare_nodes__(root):
    nodes = {}
    points = {'x':[], 'y': []}

    element = root.find('.//applicationData[@id="Presentation"]')
    if element:
        key = ''
        for node in element.iter():
            if node.tag == 'node':
                key = node.get('id')
            if node.tag == 'displayPosition':
                nodes[key] = {
                    'x': float(node.get('x')) * 20,
                    'y': float(node.get('y')) * 20,
                    'refs': [],
                }
                points['x'].append(nodes[key]['x'])
                points['y'].append(nodes[key]['y'])

        element = root.xpath('/graph/node')
        for node in element:
            n_id = node.get('id')
            if n_id in nodes:
                ops = node.xpath('./operator')
                if ops:
                    nodes[n_id]['op'] = ops[0].text
                for src in node.xpath('./sources/*'):
                    r_id = src.get('refid')
                    if r_id in nodes and r_id not in nodes[n_id]['refs']:
                        nodes[n_id]['refs'].append(r_id)
    return nodes, points


def draw(source, dest, dpi=82):
    """draw gpt graph"""
    with open(source, 'r') as file:
        root = etree.fromstring(file.read())
        nodes, points = __prepare_nodes__(root)
        if not points:
            return

        width = max(points['x']) - min(points['x']) + 100
        height = max(points['y']) - min(points['y']) + 200
        ratio = height/width
        height = int(round(600 * ratio))
        plt.figure(figsize=(600/dpi, height/dpi), dpi=dpi)

        plt.xlim([min(points['x'])-50, max(points['x'])+50])
        plt.ylim([min(points['y'])-50, max(points['y'])+50])

        for name in nodes:
            node = nodes[name]
            for ref in node['refs']:
                source = nodes[ref]
                l_xs = [source['x'], node['x']]
                l_ys = [source['y'], node['y']]
                plt.plot(l_xs, l_ys, color='black')
            oper = node['op']
            plt.text(node['x'], node['y'], f'{oper}', size=14,
                     ha="center", va="center",
                     bbox=dict(boxstyle="square",
                               ec=(0.2, 0.5, 1.),
                               fc=(0.5, 0.8, 1.),
                               )
                    )
        plt.axis('off')
        plt.savefig(dest, transparent=True)
