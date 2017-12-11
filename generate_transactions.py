import requests
import random
from time import sleep
import argparse
import math
import hashlib

# total number of transactions
N = 10

# endpoint to send the transactions
add_endpoint = '/add_transaction/'

parser = argparse.ArgumentParser(description='Start a number of nodes to mine blockchains')
parser.add_argument('miners', metavar='N', type=int, nargs='+', help='ports to query')
args = parser.parse_args()

ports = args.miners # ports same as miners names
miners = map(str, args.miners)

users = ['A', 'B', 'C', 'D', 'E']
ledger = { 'A' : 100, 'B' : 100, 'C' : 100, 'D' : 100, 'E' : 100 }

def update_ledger(txn):
    output_txns = txn['output']
    for value in output_txns:
        sender = value['sender']
        receiver = value['receiver']
        amount = value['amount']
        if sender and receiver in ledger:
            ledger[sender] -= amount
            ledger[receiver] += amount

VALID_PROBABILITY = 1

#generate_transaction builds a transaction to be sent to miners
def generate_transaction():
  prob = random.random()

  txn = {}
  if prob > VALID_PROBABILITY:
    # txn['legit'] = False
    # sender = random.choice(ledger.keys())
    # TODO to add some invalid transactions
    txn['legit'] = False
  else:
    txn['legit'] = True
    sender = random.choice(users)

    # Select a sender with non-zero balance
    while ledger[sender] <= 0:
      sender = random.choice(users)

    receiver = random.choice(users)
    while sender == receiver:
      receiver = random.choice(users)

    max_amt = ledger[sender]
    sending_amt = random.randint(1, int(math.ceil(max_amt/2.0)))

    output_txns = [
      {
        'sender': sender,
        'receiver': receiver,
        'amount': sending_amt
      }
    ]

    txn['output'] = output_txns
    txn_hash = hashlib.md5(str(txn['output']))
    txn['hash'] = txn_hash.hexdigest()
  return txn

for i in range(N):
    port = random.choice(ports)
    url = 'http://localhost:' + str(port) + add_endpoint
    txn = generate_transaction()
    requests.post(url, json=txn)
    print url
    update_ledger(txn)
    print ledger
    sleep(random.random() * 2)
  # txn = generate_transaction()
  # print txn
  # update_ledger(txn)
  # print ledger