import requests
from flask import Flask, request, jsonify, render_template
import argparse
import pydot

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('integers', metavar='N', type=int, nargs='+', help='ports to query')
args = parser.parse_args()

ports = args.integers
print ports

# Flask Enpoints
app = Flask(__name__)

neighbours_endpoint = '/get_neighbours/'
network_file = 'dot_files/network.dot'
network_graph = 'static/network.png'

@app.route('/network/')
def show_network():
  url = 'http://localhost:%s' + neighbours_endpoint
  f = open(network_file, 'w')
  f.write('digraph network {\n') 
  for port in ports:
    r = requests.get(url%(str(port)))
    neigbours = r.json()
    for neighbour in neigbours:
      f.write('%s -> %s;\n' % (str(port), str(neighbour)))
  f.write('}\n')
  f.flush()
  f.close()
  import pydot
  (graph,) = pydot.graph_from_dot_file(network_file)
  graph.write_png(network_graph)
  
  return render_template('show_network.html')

blockchain_endpoint = '/current_blockchain/'
blockchain_file = 'dot_files/blockchains.dot'
blockchain_graph = 'static/blockchains.png'
@app.route('/blockchain_status/')
def show_blockchain_status():
  url = 'http://localhost:%s' + blockchain_endpoint
  f = open(blockchain_file, 'w')
  f.write('digraph blockchains {\n') 
  f.write('{\n') 
  f.write('node [shape=box]\n') 
  f.write('}\n') 
  for port in ports:
    r = requests.get(url%(str(port)))
    blocks = r.json()
    for index in range(len(blocks) - 1):
      f.write('%s -> %s;\n' % (str(blocks[index]['block_hash']), str(blocks[index+1]['block_hash'])))
  f.write('}\n')
  f.flush()
  f.close()
  import pydot
  (graph,) = pydot.graph_from_dot_file(blockchain_file)
  graph.write_png(blockchain_graph)
  
  return render_template('show_blockchain_status.html')

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(port=10000)