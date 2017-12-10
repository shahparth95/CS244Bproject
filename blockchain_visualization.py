import requests
from flask import Flask, request, jsonify, render_template, send_file
import argparse
import pydot
import random

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('ports', metavar='N', type=int, nargs='+', help='ports to query')
args = parser.parse_args()

ports = args.ports
print ports

# Flask Enpoints
app = Flask(__name__)

neighbours_endpoint = '/get_neighbours/'
network_file = 'dot_files/network.dot'
network_graph = 'images/network.png'

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
  
  return send_file(network_graph)

blockchain_endpoint = '/current_blockchain/'
blockchain_file = 'dot_files/blockchains.dot'
blockchain_graph = 'images/blockchains.png'
node_map = {}
count = 0

@app.route('/blockchain_status/')
def show_blockchain_status():
  global count
  url = 'http://localhost:%s' + blockchain_endpoint
  f = open(blockchain_file, 'w')
  f.write('digraph blockchains {\n') 
  f.write('node [shape=box];\n') 
  f.write('rankdir = "LR";\n') 
  f.write('fixedsize = true;\n') 
  for port in ports:
    r = requests.get(url%(str(port)))
    blocks = r.json()
    for index in range(len(blocks) - 1):
      src = blocks[index]['block_hash']
      dst = blocks[index+1]['block_hash']
      if src not in node_map:
        node_map[src] = count
        count += 1
      
      if dst not in node_map:
        node_map[dst] = count
        count += 1

      f.write('block%s -> block%s;\n' % (str(node_map[src]), str(node_map[dst])))
  f.write('}\n')
  f.flush()
  f.close()
  import pydot
  (graph,) = pydot.graph_from_dot_file(blockchain_file)
  graph.write_png(blockchain_graph)
  
  return send_file(blockchain_graph)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(port=10000)