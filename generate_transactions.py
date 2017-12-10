import requests
import random
from time import sleep
import argparse
import math

# total number of transactions
N = 10

# endpoint to send the transactions
add_endpoint = '/add_transaction/'

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('miners', metavar='N', type=int, nargs='+', help='ports to query')
args = parser.parse_args()

ports = args.miners # ports same as miners names
miners = map(str, args.miners)
print miners

users = ['A', 'B', 'C', 'D', 'E']
for miner in miners:
  users.append(miner)

UTXOs = [
  {
    'sender': 'G',
    'receiver': 'A',
    'amount': 10,
  },
  {
    'sender': 'G',
    'receiver': 'B',
    'amount': 10,
  },
  {
    'sender': 'G',
    'receiver': 'C',
    'amount': 10,
  },
  {
    'sender': 'G',
    'receiver': 'D',
    'amount': 10,
  },
  {
    'sender': 'G',
    'receiver': 'E',
    'amount': 10,
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

  for user in users:
    if user not in ledger:
      ledger[user] = 0
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
    receiver = random.choice(ledger.keys())
    while sender == receiver:
      receiver = random.choice(ledger.keys())

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
        'amount': sending_amt
      },
      {
        'sender': sender,
        'receiver': sender,
        'amount': input_amount - sending_amt
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

for i in range(N):
  # for port in ports:
  #   url = 'http://localhost:' + str(port) + add_endpoint
  #   data = generate_transaction()
  #   requests.post(url, json=data)
  #   sleep(2*random.random())
  txn = generate_transaction(UTXOs)
  UTXOs = update_UTXOs(UTXOs, txn)
  ledger = get_ledger(UTXOs)
  print txn
  for data in ledger:
    print data, ledger[data]
  print