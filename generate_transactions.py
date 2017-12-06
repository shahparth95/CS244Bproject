import requests
import random
import json

# list of ports to send the transactions to
ports = [5000]

# total number of transactions
N = 100

# endpoint to send the transactions
add_endpoint = '/add_transaction/'

#generate_transaction builds a transaction to be sent to miners
def generate_transaction():
  # TODO: update the transaction to send real world transaction
  txn = {}
  txn['sender'] = random.randint(0,100)
  return txn

for i in range(N):
  for port in ports:
    url = 'http://localhost:' + str(port) + add_endpoint
    data = generate_transaction()
    requests.post(url, json=data)