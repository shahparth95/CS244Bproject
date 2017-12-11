from flask import Flask, request, jsonify
from threading import Thread, Lock
from multiprocessing import Process
from time import sleep,time
import random
import hashlib
import json
import argparse
import requests
import math

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.basicConfig(filename='blockchain.logs',level=logging.ERROR)

MINE_BLOCKS = 10
begin_hash = hashlib.md5(bytes(1234567890)).hexdigest()

def valid_blockchain(blockchain):
  # TODO
  return True

def state_transition_function(state, txn):
  work_state = state[:]
  input_txn = txn['input']
  input_sum = 0
  # removing the input transactions
  for in_txn in input_txn:
    if in_txn not in work_state:
      return state, False
    else:
      work_state.remove(in_txn)
      input_sum += in_txn['amount']

  output_txn = txn['output']
  output_sum = 0
  # adding the output transactions
  for out_txn in output_txn:
    work_state.append(out_txn)
    output_sum += out_txn['amount']

  # can not generate money
  if output_sum > input_sum:
    return state, False

  return work_state, True

def gen_block(prev_hash, proof, state, txns = []):
  valid_txns = []
  for txn in txns:
    state, legit = state_transition_function(state, txn)
    if legit:
      valid_txns.append(txn)

  block = {}
  block['prev_hash'] = str(prev_hash)
  block['proof'] = str(proof)
  block['transactions'] = valid_txns # init with empty list
  block['time'] = str(time())
  block['state'] = state
  block_hash = hashlib.sha256(bytes(block['prev_hash'] + block['proof'] + str(block['state']) + str(block['transactions']) + block['time']))
  block['block_hash'] = block_hash.hexdigest()

  return block

def valid_guess(prev_hash, prev_proof, guess):
  hash_val = hashlib.sha256(bytes(str(prev_hash) + str(guess)))
  hash_str = hash_val.hexdigest()
  # return hash_str[:6] == '000000' or hash_str[:6] == '000001' or hash_str[:6] == '000002' or hash_str[:6] == '000003' or hash_str[:6] == '000004'
  return hash_str[:5] == '00000'

def check_different(blockchain_a, blockchain_b):
  if len(blockchain_a) != len(blockchain_b):
    return True

  for i in range(len(blockchain_a)):
    if blockchain_a[i]['block_hash'] != blockchain_b[i]['block_hash']:
      return True

  return False

def get_transactions(blockchain):
  txns = []
  for block in blockchain:
    txns = txns+block['transactions']

  return txns

class Node:
  data_lock = Lock() # check about RW lock, could not find it inbuilt in threading module
  
  def __init__(self, port, neighbours = []):
    # TODO init should poll the neighbors to get the latest chain, in absence of which it should make the genesis block
    self.transactions_seen = set()
    self.blockchain = []
    self.neighbours = set(neighbours)
    self.port = port

    # Create the genesis block
    self.init_block(1, 1)

  '''
  function to add neighbour to the current node
  '''
  def add_neighbour(self, port):
    self.data_lock.acquire()
    self.neighbours.add(port)
    self.data_lock.release()    

  '''
  return the list of current neighbours
  '''
  def neighbours_set(self):
    self.data_lock.acquire()
    result = self.neighbours
    self.data_lock.release()
    
    return result

  # functions for adding and listing outstanding transactions
  def add_transaction(self, txn):
    # TODO sanity check for transactions here
    new_txn = False
    self.data_lock.acquire()
    txn_hash = txn['hash']
    if txn_hash not in self.transactions_seen:
      self.transactions_seen.add(txn_hash)
      self.transactions.append(txn)      
      new_txn = True
    self.data_lock.release()

    if new_txn:
      self.gossip_data(txn, '/add_transaction/')

  def outstanding_transactions(self):
    self.data_lock.acquire()
    result = self.transactions
    self.data_lock.release()
    return result

  # functions for block handelling
  def init_block(self, hash_val, proof):
    genesis_state = [
      {
        'sender': 'G',
        'receiver': 'A',
        'amount': 10,
        'hash': begin_hash
      },
      {
        'sender': 'G',
        'receiver': 'B',
        'amount': 10,
        'hash': begin_hash
      },
      {
        'sender': 'G',
        'receiver': 'C',
        'amount': 10,
        'hash': begin_hash
      },
      {
        'sender': 'G',
        'receiver': 'D',
        'amount': 10,
        'hash': begin_hash
      },
      {
        'sender': 'G',
        'receiver': 'E',
        'amount': 10,
        'hash': begin_hash
      }
    ]
    block = gen_block(prev_hash=hash_val, proof=proof, state=genesis_state)

    self.data_lock.acquire()
    # state is not made as set of UTXOs to avoid removing duplicate transactions
    self.state = genesis_state
    self.transactions = []
    self.blockchain.append(block)
    self.data_lock.release()

  # mining functions, this function continuously tries to mine the new blocks
  def mine_block(self):
    blocks = 0
    while blocks < MINE_BLOCKS:
      self.data_lock.acquire()
      curr_tail = self.blockchain[-1]
      self.data_lock.release()

      prev_hash = curr_tail['block_hash']
      prev_proof = curr_tail['proof']
      guess = random.randint(0, 2**31)
      
      send_blockchain = None
      if valid_guess(prev_hash, prev_proof, guess):
        self.data_lock.acquire()
        check_tail = self.blockchain[-1]
      
        # incase the chain has changed since this work started
        if check_tail == curr_tail:
          block = gen_block(prev_hash, guess, self.state, self.transactions)
          self.state = block['state']
          self.transactions = []
          self.blockchain.append(block)

          logging.error('New block minted by '+ str(self.port) + ', len: ' + str(len(self.blockchain)))
          blocks += 1;
          send_blockchain = self.blockchain[:]
        self.data_lock.release() 

      if send_blockchain != None:
        self.gossip_data(json.dumps(send_blockchain), '/new_blockchain/')

    logging.error(('Port: %s Finished')%(str(port)))

  def send_data(self, latency, dst_port, data, dst_endpoint):
    logging.info('Data sending beginning for ' + str(dst_port) + ' from ' + str(self.port))
    sleep(latency)
    url = 'http://localhost:' + str(dst_port) + dst_endpoint
    # data = json.dumps(data)
    requests.post(url, json=data)
    logging.info('Data sent to ' + str(dst_port) + ' from ' + str(self.port) + ' with latency: ' + str(latency))

  def gossip_data(self, data, dst_endpoint):
    threads = []
    for neighbour in self.neighbours:
      latency = 2*random.random()*min(abs(self.port - neighbour), 10)
      thread = Thread(target=self.send_data, args = (latency, neighbour, data, dst_endpoint))
      thread.start()
      threads.append(thread)

  def get_blockchain(self):
    self.data_lock.acquire()
    result = self.blockchain
    self.data_lock.release()
    return result

  def merge_blockchain(self, blockchain):
    if valid_blockchain(blockchain):
      send_blockchain = False
      self.data_lock.acquire()
      if len(self.blockchain) < len(blockchain):
        # make list of uncommitted transactions
        new_committed_txns = get_transactions(blockchain)
        current_committed_txns = get_transactions(self.blockchain)
        uncommitted_txns = [txn for txn in current_committed_txns if txn not in new_committed_txns]
        
        logging.error('Blockchain has been updated by port:' + str(self.port) + '. Length change: ' + str(len(self.blockchain)) + '->'+ str(len(blockchain)) + '. Uncommitted txns: ' + str(len(uncommitted_txns)))

        # update transaction list, state and blockchain
        self.transactions = self.transactions + uncommitted_txns 
        self.blockchain = blockchain[:]
        self.state = blockchain[-1]['state'] # update state to new state
        # TODO retrieve the lost transactions
        send_blockchain = True
      elif len(self.blockchain) == len(blockchain) and check_different(self.blockchain, blockchain):
        logging.error('BLOCKCHAIN CONFLICT at port ' + str(self.port))
      self.data_lock.release()
      
      if send_blockchain:
        self.gossip_data(json.dumps(blockchain), '/new_blockchain/')

  def get_ledger(self):
    self.data_lock.acquire()
    current_state = self.blockchain[-1]['state']
    self.data_lock.release()

    ledger = {}
    for UTXO in current_state:
      receiver = UTXO['receiver']
      amount = UTXO['amount']
      if receiver in ledger:
        ledger[receiver] += amount
      else:
        ledger[receiver] = amount

    return ledger

def spawn_node(port, neighbours):
  node = Node(port, neighbours)

  # Flask Enpoints
  app = Flask(__name__)

  @app.route('/add_node/<int:port>')
  def add_neighbour(port):
    node.add_neighbour(port)
    return 'current neighbours: ' + str(node.neighbours_set())

  @app.route('/get_neighbours/')
  def get_neighbours():
    return jsonify(list(node.neighbours_set()))

  @app.route('/add_transaction/', methods=['POST'])
  def add_transaction():
    txn = request.get_json()
    # 1. add support for concurrent uses
    # 2. check for validation and if it consists of standard fields and determined later
    #     need to have 'input' and 'output' keys
    # transactions.append(txn)
    node.add_transaction(txn)
    return str(txn) + 'added successfully'

  @app.route('/outstanding_transactions/', methods=['GET'])
  def outstanding_transactions():
    return jsonify(node.outstanding_transactions())

  @app.route('/current_blockchain/', methods=['GET'])
  def current_blockchain():
    return jsonify(node.get_blockchain())

  @app.route('/new_blockchain/', methods=['POST'])
  def new_blockchain():
    # TODO this can take some time, spawn a new thread to do this
    blockchain = json.loads(request.get_json())
    node.merge_blockchain(blockchain)
    return "received"

  @app.route('/get_ledger/', methods=['GET'])
  def get_ledger():
    # ledger is a dict, mapping 'account' to their current balances
    ledger = node.get_ledger()
    return jsonify(ledger)

  def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
  
  @app.route('/stop/')
  def stop():
    shutdown_server()
    return 'Server shutting down...'

  thread1 = Thread(target = node.mine_block)
  thread1.start()
  app.run(port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
  parser.add_argument('--nodes', default=5, type=int, help='Number of nodes to spawn')
  args = parser.parse_args()
  nodes = args.nodes

  processes = []
  for i in range(nodes):
    ports = [5000+j for j in range(nodes)]
    port = ports[i]
    ports.remove(port)
    p = Process(target = spawn_node, args = (port, ports))
    p.start()