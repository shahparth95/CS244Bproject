from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

neighbours = set()
transactions= []
blockchain = []

@app.route('/add_node/<int:port>')
def add_neighbour(port):
  neighbours.add(port)
  return 'current neighbours: ' + str(neighbours)

@app.route('/add_transaction/', methods=['POST'])
def add_transaction():
  txn = request.get_json()
  # 1. add support for concurrent uses
  # 2. check for validation and if it consists of standard fields and determined later
  transactions.append(txn)
  return str(txn) + 'added successfully'

@app.route('/outstanding_transactions/', methods=['GET'])
def outstanding_transactions():
  return jsonify(transactions)