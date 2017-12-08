from flask import Flask, request, jsonify
from threading import Thread, Lock
from multiprocessing import Process
from time import sleep,time
import random
import hashlib
import json
import argparse
import requests



def valid_blockchain(blockchain):
  # TODO
  return True

def gen_block(prev_hash, proof, txns = []):
  block = {}
  block['prev_hash'] = str(prev_hash)
  block['proof'] = str(proof)
  block['transactions'] = str(txns) # init with empty list
  block['time'] = str(time())
  # try and reason about this, why this provides safety in block
  block_hash = hashlib.sha256(bytes(block['prev_hash'] + block['proof'] + block['transactions'] + block['time']))
  block['block_hash'] = block_hash.hexdigest()

  return block

def valid_guess(prev_hash, prev_proof, guess):
  # TODO might be sufficient to just use prev_hash. prev_proof is part of the prev_hash
  hash_val = hashlib.sha256(bytes(str(prev_hash) + str(prev_proof) + str(guess)))
  hash_str = hash_val.hexdigest()
  return hash_str[:6] == '000000' or hash_str[:6] == '000001' or hash_str[:6] == '000002' or hash_str[:6] == '000003' or hash_str[:6] == '000004'

class Node:
  data_lock = Lock() # check about RW lock, could not find it inbuilt in threading module
  
  def __init__(self, port, neighbours = []):
    # TODO init should poll the neighbors to get the latest chain, in absence of which it should make the genesis block
    self.transactions = []
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
    self.data_lock.acquire()
    self.transactions.append(txn)
    self.data_lock.release()

  def outstanding_transactions(self):
    self.data_lock.acquire()
    result = self.transactions
    self.data_lock.release()
    return result

  # functions for block handelling
  def init_block(self, hash_val, proof):
    block = gen_block(hash_val, proof)

    self.data_lock.acquire()
    self.blockchain.append(block)
    self.data_lock.release()

  # mining functions, this function continuously tries to mine the new blocks
  def mine_block(self):
    blocks = 0
    while blocks < 5:
      self.data_lock.acquire()
      # get the tail block in case the block chain had changed
      curr_tail = self.blockchain[-1]
      self.data_lock.release()

      prev_hash = curr_tail['block_hash']
      prev_proof = curr_tail['proof']
      guess = random.randint(0, 2**31)
      if valid_guess(prev_hash, prev_proof, guess):
        self.data_lock.acquire()
        check_tail = self.blockchain[-1]
        # incase the chain has changed since this work started
        if check_tail == curr_tail:
          block = gen_block(prev_hash, guess, self.transactions)

          self.transactions = []
          self.blockchain.append(block)

          print '\nNew block minted by '+ str(self.port) + ', len: ' + str(len(self.blockchain)) + '\n'
          blocks += 1;
          # gossip
          for neighbour in self.neighbours:
            url = 'http://localhost:' + str(neighbour) + '/new_blockchain/'
            data = json.dumps(self.blockchain)
            requests.post(url, json=data)
        else:
          print "\nblock changed during computation\n"
        self.data_lock.release() 


  def get_blockchain(self):
    self.data_lock.acquire()
    result = self.blockchain
    self.data_lock.release()
    return result

  def merge_blockchain(self, blockchain):
    if valid_blockchain(blockchain):
      self.data_lock.acquire()
      if len(self.blockchain) < len(blockchain):
        print '\nBlockchain has been updated by port:' + str(port) + '.Length change' + str(len(self.blockchain)) + '->'+ str(len(blockchain)) + '\n'
        self.blockchain = blockchain
      self.data_lock.release()

# def mine_block():
#   node.mine_block()
  
def spawn_node(port, neighbours):
  node = Node(port, neighbours)

  # Flask Enpoints
  app = Flask(__name__)

  @app.route('/add_node/<int:port>')
  def add_neighbour(port):
    node.add_neighbour(port)
    return 'current neighbours: ' + str(node.neighbours_set())

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