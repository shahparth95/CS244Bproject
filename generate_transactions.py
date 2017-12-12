import requests
import random
from time import sleep, time
import argparse
import math
import hashlib

# total number of transactions
N = 500
begin_hash = hashlib.md5(bytes(1234567890)).hexdigest()

# endpoint to send the transactions
add_endpoint = '/add_transaction/'

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('miners', metavar='N', type=int, nargs='+', help='ports to query')
args = parser.parse_args()

ports = args.miners # ports same as miners names
miners = map(str, args.miners)
print miners

users = ['A', 'B', 'C', 'D', 'E']
for i in range(45):
  users.append(str(i))

UTXOs = [
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

def get_ledger(UTXOs):
  ledger = {}
  for UTXO in UTXOs:
    receiver = UTXO['receiver']
    amount = UTXO['amount']
    if receiver in ledger:
      ledger[receiver] += amount
    else:
      ledger[receiver] = amount
  return ledger

VALID_PROBABILITY = 1

def filter_UTXO(UTXO, receiver):
  return UTXO['receiver'] == receiver

#generate_transaction builds a transaction to be sent to miners
def generate_transaction(UTXOs):
  # TODO: update the transaction to send real world transaction
  ledger = get_ledger(UTXOs)
  prob = random.random()

  txn = {}
  if prob > VALID_PROBABILITY:
    # txn['legit'] = False
    # sender = random.choice(ledger.keys())
    # TODO to add some invalid transactions
    txn['legit'] = False
  else:
    txn['legit'] = True
    sender = random.choice(ledger.keys())
    while ledger[sender] <= 0:
      sender = random.choice(ledger.keys())

    receiver = random.choice(users)
    while sender == receiver:
      receiver = random.choice(users)

    # added to all the output_transactions as well
    txn_hash = hashlib.md5(str(random.random())) 
    txn['hash'] = txn_hash.hexdigest()

    max_amt = ledger[sender]
    sending_amt = random.randint(1, int(math.ceil(max_amt/2.0)))
    filtered_UTXOs = [utxo for utxo in UTXOs if utxo['receiver'] == sender]
    input_txns = []
    input_amount = 0
    for utxo in filtered_UTXOs:
      input_txns.append(utxo)
      input_amount += utxo['amount']
      if input_amount >= sending_amt:
        break

    output_txns = [
      {
        'sender': sender,
        'receiver': receiver,
        'amount': sending_amt,
        'hash': txn_hash.hexdigest()
      },
      {
        'sender': sender,
        'receiver': sender,
        'amount': input_amount - sending_amt,
        'hash': txn_hash.hexdigest()
      }
    ]

    txn['input'] = input_txns
    txn['output'] = output_txns
  return txn

def update_UTXOs(UTXOs, txn):
  input_txns = txn['input']
  output_txns = txn['output']

  for txn in input_txns:
    UTXOs.remove(txn)

  for txn in output_txns:
    UTXOs.append(txn)

  return UTXOs

def print_txn(txn):
  print 'HASH:', txn['hash']
  input_txns = txn['input']
  output_txns = txn['output']
  print "INPUT:"
  for input_txn in input_txns:
    print input_txn

  print "OUTPUT:"
  for output_txn in output_txns:
    print output_txn

for i in range(N):
  port = random.choice(ports)
  url = 'http://localhost:' + str(port) + add_endpoint
  txn = generate_transaction(UTXOs)
  UTXOs = update_UTXOs(UTXOs, txn)
  print url
  print txn['hash']
  r = requests.post(url, json=txn)
  print r.text
  print 
  sleep(random.random())

ledger = get_ledger(UTXOs)
for data in ledger:
  print data, ledger[data]