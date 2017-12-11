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

ledger_endpoint = '/get_ledger/'
colors = ['#a6ff4d', '#ffff33', '#ff1a1a', '#3377ff', '#ffffff']
@app.route('/get_ledger/')
def get_ledger():
  accounts = set()
  port_ledgers = {}
  url = 'http://localhost:%s' + ledger_endpoint
  for port in ports:
    r = requests.get(url%(str(port)))
    ledger = r.json()
    names = set(ledger.keys())
    accounts = accounts | names
    port_ledgers[port] = ledger

  for account in accounts:
    for port in ports:
      if account not in port_ledgers[port]:
        port_ledgers[port][account] = 'Not Seen'

  color_ledger = {}
  for account in accounts:
    values_color_map = {}
    port_color = {}
    for port in ports:
      val = port_ledgers[port][account]
      if val in values_color_map:
        port_color[port] = values_color_map[val]
      else:
        color = colors[len(values_color_map)]
        values_color_map[val] = color
        port_color[port] = values_color_map[val]
    color_ledger[account] = port_color


  return render_template('ledger_table.html', accounts=list(accounts), ports=ports, ledgers=port_ledgers, color_scheme=color_ledger)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(port=10000)