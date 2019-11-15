"""GPT Graph drawing utils"""
from lxml import etree

import matplotlib as mpl
mpl.use('Agg') # use no graphical backend
import matplotlib.pyplot as plt

def draw(source, dest, dpi=82):
    """draw gpt graph"""
    with open(source, 'r') as file:
        root = etree.fromstring(file.read())
        element = root.find('.//applicationData[@id="Presentation"]')
        nodes = {}

        if element is not None:
            name = ''
            n_xs = []
            n_ys = []
            for node in element.iter():
                if node.tag == 'node':
                    name = node.get('id')
                if node.tag == 'displayPosition':
                    nodes[name] = {
                        'x': float(node.get('x')) * 20,
                        'y': float(node.get('y')) * 20,
                        'refs': [],
                    }
                    n_xs.append(node[name]['x'])
                    n_ys.append(node[name]['y'])

            width = max(n_xs) - min(n_xs) + 100
            height = max(n_ys) - min(n_ys) + 20
            ratio = height/width
            height = int(round(600 * ratio))
            plt.figure(figsize=(600/dpi, height/dpi), dpi=dpi)

            plt.xlim([min(n_xs)-50, max(n_xs)+50])
            plt.ylim([min(n_ys)-10, max(n_ys)+10])

            elems = root.xpath('/graph/node')

            for node in elems:
                n_id = node.get('id')
                if n_id in nodes:
                    ops = node.xpath('./operator')
                    if ops:
                        nodes[n_id]['op'] = ops[0].text
                    for src in node.xpath('./sources/*'):
                        r_id = src.get('refid')
                        nodes[n_id]['refs'].append(r_id)
                        if r_id in nodes:
                            l_xs = [nodes[r_id]['x'], nodes[n_id]['x']]
                            l_ys = [nodes[r_id]['y'], nodes[n_id]['y']]
                            plt.plot(l_xs, l_ys, color='black')
            for name in nodes:
                oper = nodes[name]['op']
                plt.text(nodes[name]['x'], nodes[name]['y'], f'{oper}', size=14,
                         ha="center", va="center",
                         bbox=dict(boxstyle="square",
                                   ec=(0.2, 0.5, 1.),
                                   fc=(0.5, 0.8, 1.),
                                   )
                        )
            plt.axis('off')
            plt.savefig(dest, transparent=True)
