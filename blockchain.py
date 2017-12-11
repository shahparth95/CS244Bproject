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

MINE_BLOCKS = 7

def valid_blockchain(blockchain):
  # TODO
  return True

def gen_block(prev_hash, proof, state, txns = []):
  block = {}
  block['prev_hash'] = str(prev_hash)
  block['proof'] = str(proof)
  block['transactions'] = txns # init with empty list
  block['time'] = str(time())
  block['state'] = state # initial state (In Ethereum it will be for ex. an account balance)
  # try and reason about this, why this provides safety in block
  block_hash = hashlib.sha256(bytes(block['prev_hash'] + block['proof'] + str(block['transactions']) + block['time'] + str(block['state'])))
  block['block_hash'] = block_hash.hexdigest()
  return block

def valid_guess(prev_hash, prev_proof, guess):
  # TODO might be sufficient to just use prev_hash. prev_proof is part of the prev_hash
  hash_val = hashlib.sha256(bytes(str(prev_hash) + str(prev_proof) + str(guess)))
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

class Node:
  data_lock = Lock() # check about RW lock, could not find it inbuilt in threading module
  
  def __init__(self, port, neighbours = []):
    # TODO init should poll the neighbors to get the latest chain, in absence of which it should make the genesis block
    self.knownTransactions = set()
    self.outstandingTransactions = []
    self.validTxn = False
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
    # TODO with gossip, avoid adding the same transaction multiple times. Use dict for txns: hash -> txn
    new_txn = False
    self.data_lock.acquire()
    txn_hash = txn['hash']
    if txn_hash not in self.knownTransactions:
        self.knownTransactions.add(txn_hash)
        self.outstandingTransactions.append(txn)
        new_txn = True
    self.data_lock.release()

    if new_txn:
        self.gossip_data(txn, '/add_transaction/')

  def outstanding_transactions(self):
    self.data_lock.acquire()
    result = self.outstandingTransactions
    self.data_lock.release()
    return result

  # functions for block handelling
  def init_block(self, hash_val, proof):
    init_state = { 'A' : 100, 'B' : 100, 'C' : 100, 'D' : 100, 'E' : 100 }
    block = gen_block(hash_val, proof, init_state, self.outstandingTransactions)

    self.data_lock.acquire()
    self.state = init_state
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
      
      blockchain_updated = False
      if valid_guess(prev_hash, prev_proof, guess):
        self.data_lock.acquire()
        check_tail = self.blockchain[-1]
      
        # incase the chain has changed since this work started
        if check_tail == curr_tail:

          # TODO: validate a transaction here, add a read lock
          if self.outstandingTransactions.count != 0:
              for txn in self.outstandingTransactions:
                  output_txns = txn['output']
                  self.validTxn = False
                  for value in output_txns:
                      sender = value['sender']
                      receiver = value['receiver']
                      amount = value['amount']
                      if sender and receiver in self.state:
                          self.state[sender] -= amount
                          self.state[receiver] += amount
                          self.validTxn = True
                  if self.validTxn:
                      self.outstandingTransactions.remove(txn)

          block = gen_block(prev_hash, guess, self.state, self.outstandingTransactions)
          self.blockchain.append(block)

          logging.error('New block minted by '+ str(self.port) + ', len: ' + str(len(self.blockchain)))
          logging.error('Current account balance is ' + str(self.state))

          blocks += 1;
          blockchain_updated = True

        self.data_lock.release() 

      if blockchain_updated:
        self.gossip_blockchain()

  def send_block(self, latency, dst_port, blockchain):
    logging.info('Data sending beginning for ' + str(dst_port) + ' from ' + str(self.port))
    sleep(5*latency)
    url = 'http://localhost:' + str(dst_port) + '/new_blockchain/'
    data = json.dumps(blockchain)
    requests.post(url, json=data)
    logging.info('Data sent to ' + str(dst_port) + ' from ' + str(self.port) + ' with latency: ' + str(latency))

  def gossip_blockchain(self):
    self.data_lock.acquire()
    current_blockchain = self.blockchain
    self.data_lock.release()

    threads = []
    for neighbour in self.neighbours:
      latency = random.random()*min(abs(self.port - neighbour), 10)
      thread = Thread(target=self.send_block, args = (latency, neighbour, current_blockchain))
      thread.start()
      threads.append(thread)

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
      blockchain_updated = False
      self.data_lock.acquire()
      if len(self.blockchain) < len(blockchain):
        logging.error('Blockchain has been updated by port:' + str(self.port) + '. Length change: ' + str(len(self.blockchain)) + '->'+ str(len(blockchain)))
        self.blockchain = blockchain
        blockchain_updated = True
      elif len(self.blockchain) == len(blockchain) and check_different(self.blockchain, blockchain):
        logging.error('BLOCKCHAIN CONFLICT at port ' + str(self.port))
      self.data_lock.release()
      
      if blockchain_updated:
        self.gossip_blockchain()

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
    # transactions.append(txn)
    node.add_transaction(txn)
    return str(txn) + 'added successfully'

  @app.route('/outstanding_transactions/', methods=['GET'])
  def outstanding_transactions():
    return jsonify(node.outstanding_transactions())

  @app.route('/current_blockchain/', methods=['GET'])
  def current_blockchain():
    return jsonify(node.get_blockchain())

  # TODO this is the endpoint where other nodes can submit their blockchains to propogate it in the network
  @app.route('/new_blockchain/', methods=['POST'])
  def new_blockchain():
    # TODO this can take some time, spawn a new thread to do this
    blockchain = json.loads(request.get_json())
    node.merge_blockchain(blockchain)
    return "received"

  @app.route('/stop/')
  def stop():
    # this is wrong update this
    func = request.environ.get('werkzeug.server.shutdown')
    func()

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