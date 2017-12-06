from flask import Flask, request, jsonify
from threading import Thread, Lock
from time import sleep,time
import random
import hashlib
import json
import argparse
import requests



def valid_blockchain(blockchain):
  # TODO
  return True

class Node:
  data_lock = Lock()
  
  def __init__(self, neighbours = []):
    # TODO init should poll the neighbors to get the latest chain, in absence of which it should make the genesis block
    self.transactions = []
    self.blockchain = []
    self.neighbours = set()

    # Create the genesis block
    self.init_block(1, 1)

  # functions for adding and listing neighbours for the node
  def add_neighbour(self, port):
    self.data_lock.acquire()
    self.neighbours.add(port)
    self.data_lock.release()    

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
    block = {}
    block['prev_hash'] = str(hash_val)
    block['proof'] = str(proof)
    block['transactions'] = str([]) # init with empty list
    block['time'] = str(time())
    block_hash = hashlib.sha256(bytes(block['prev_hash'] + block['proof'] + block['transactions'] + block['time']))
    block['block_hash'] = block_hash.hexdigest()

    self.data_lock.acquire()
    self.blockchain.append(block)
    self.data_lock.release()

  # mining functions, this function continuously tries to mine the new blocks
  def valid_guess(self, prev_hash, prev_proof, guess):
    hash_val = hashlib.sha256(bytes(str(prev_hash) + str(prev_proof) + str(guess)))
    hash_str = hash_val.hexdigest()
    return hash_str[:6] == '000000' or hash_str[:6] == '000001' or hash_str[:6] == '000002' or hash_str[:6] == '000003' or hash_str[:6] == '000003'

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
      if self.valid_guess(prev_hash, prev_proof, guess):
        self.data_lock.acquire()
        check_tail = self.blockchain[-1]
        if check_tail == curr_tail:
          block = {}
          block['prev_hash'] = str(prev_hash)
          block['proof'] = str(guess)
          block['transactions'] = str(self.transactions) # TODO check validity here
          block['time'] = str(time())
          block_hash = hashlib.sha256(bytes(block['prev_hash'] + block['proof'] + block['transactions'] + block['time']))
          block['block_hash'] = block_hash.hexdigest()

          self.transactions = []
          self.blockchain.append(block)

          print '\nNew block minted '+ str(len(self.blockchain)) + '\n'
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
        print '\nBlockchain has been updated.' + str(len(self.blockchain)) + '->'+ str(len(blockchain)) + '\n'
        self.blockchain = blockchain
      self.data_lock.release()

node = Node()


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


def mine_block():
  node.mine_block()
  
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Start a node at a given port')
  parser.add_argument('--port', metavar='P', default=5000, type=int, help='port on which to start node')
  args = parser.parse_args()
  port = args.port

  print port
  thread1 = Thread(target = mine_block)
  thread1.start()
  app.run(port=port, debug=False, use_reloader=False)
