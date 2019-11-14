
import matplotlib as mpl
mpl.use('Agg') # use no graphical backend
import matplotlib.pyplot as plt
from lxml import etree

def draw(source, dest):
	"""draw gpt graph"""
	with open(source, 'r') as file:
		root = etree.fromstring(file.read())
		element = root.find('.//applicationData[@id="Presentation"]')
		nodes = {}
		myDPI = 82

		if element is not None:
		    name = ''
		    xs = []
		    ys = []
		    for node in element.iter():
		        if node.tag == 'node':
		            name = node.get('id')
		        if node.tag == 'displayPosition':
		            x = float(node.get('x')) * 20
		            y = float(node.get('y')) * 20
		            nodes[name] = {
		                'x': x,
		                'y': y,
		                'refs': [],
		            }
		            xs.append(x)
		            ys.append(y)
		            

		width = max(xs) - min(xs) + 100
		height = max(ys) - min(ys) + 20
		ratio = height/width
		height = int(round(600 * ratio))
		plt.figure(figsize=(600/myDPI, height/myDPI), dpi=myDPI)

		plt.xlim([min(xs)-50, max(xs)+50])
		plt.ylim([min(ys)-10, max(ys)+10])

		elems = root.xpath('/graph/node')

		for node in elems:
		    n_id = node.get('id')
		    if n_id in nodes:
		        ops = node.xpath('./operator')
		        if len(ops):
		            nodes[n_id]['op'] = ops[0].text
		        for s in node.xpath('./sources/*'):
		            r_id = s.get('refid')
		            nodes[n_id]['refs'].append(r_id)
		            if r_id in nodes:
		                xs = [nodes[r_id]['x'], nodes[n_id]['x']]
		                ys = [nodes[r_id]['y'], nodes[n_id]['y']]
		                plt.plot(xs, ys, color='black')
		for name in nodes:
		    x = nodes[name]['x']
		    y = nodes[name]['y']
		    oper = nodes[name]['op']
		    plt.text(x, y, f'{oper}', size=14,  ha="center", va="center",
		                     bbox=dict(boxstyle="square",
		                               ec=(0.2, 0.5, 1.),
		                               fc=(0.5, 0.8, 1.),
		                               )
		                    )
		plt.axis('off')
		plt.savefig(dest, transparent=True)
