import requests
from flask import Flask, request, jsonify, render_template, send_file
import argparse
import pydot
import random
import hashlib

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('ports', metavar='N', type=int, nargs='+', help='ports to query')
parser.add_argument('--start_port', default=10000, type=int, help='Number of nodes to spawn')
args = parser.parse_args()

start_port = args.start_port
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

@app.route('/get_mining_count/')
def get_mining_count():
  url = 'http://localhost:5000' + blockchain_endpoint
  r = requests.get(url)
  blocks = r.json()
  mine_count = {}
  for index in range(1, len(blocks)):
    miner = blocks[index]['miner']
    if miner in mine_count:
      mine_count[miner] += 1
    else:
      mine_count[miner] = 1

  return jsonify(mine_count)

# def get_transactions(blockchain):
#   txns = []
#   for block in blockchain:
#     txns = txns+block['transactions']
#   return txns
# begin_hash = hashlib.md5(bytes(1234567890)).hexdigest()

# UTXOs = [
#   {
#     'sender': 'G',
#     'receiver': 'A',
#     'amount': 10,
#     'hash': begin_hash
#   },
#   {
#     'sender': 'G',
#     'receiver': 'B',
#     'amount': 10,
#     'hash': begin_hash
#   },
#   {
#     'sender': 'G',
#     'receiver': 'C',
#     'amount': 10,
#     'hash': begin_hash
#   },
#   {
#     'sender': 'G',
#     'receiver': 'D',
#     'amount': 10,
#     'hash': begin_hash
#   },
#   {
#     'sender': 'G',
#     'receiver': 'E',
#     'amount': 10,
#     'hash': begin_hash
#   }
# ]

# def state_transition_function(state, txn):
#   work_state = state[:]
#   input_txn = txn['input']
#   input_sum = 0
#   # removing the input transactions
#   for in_txn in input_txn:
#     if in_txn not in work_state:
#       return state, False
#     else:
#       work_state.remove(in_txn)
#       input_sum += in_txn['amount']

#   output_txn = txn['output']
#   output_sum = 0
#   # adding the output transactions
#   for out_txn in output_txn:
#     work_state.append(out_txn)
#     output_sum += out_txn['amount']

#   # can not generate money
#   if output_sum > input_sum:
#     return state, False

#   return work_state, True

# @app.route('/verify_txn_list/')
# def verify_txn_list():
#   url = 'http://localhost:5000' + blockchain_endpoint
#   r = requests.get(url)
#   blockchain = r.json()
#   print type(blockchain), len(blockchain)
#   transactions = get_transactions(blockchain)
#   result = {}
#   result['txn_count'] = len(transactions)
#   # result['transactions'] = transactions
#   state = UTXOs[:]
  
#   for txn in transactions:
#     state, _ = state_transition_function(state, txn)

#   ledger = {}
#   for UTXO in state:
#     receiver = UTXO['receiver']
#     amount = UTXO['amount']
#     if receiver in ledger:
#       ledger[receiver] += amount
#     else:
#       ledger[receiver] = amount 
#   result['ledger'] = ledger
#   result['state_size'] = blockchain[-1]['state']
#   return jsonify(result)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(port=start_port)