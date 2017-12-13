# CS244Bproject

## Blockchain consenseus protocol

Implementation of Proof-Of-Work consensus protocol using Python (Ver. 2.7)

Tested working of consensus protocol using both UTXO(Bitcoin) and Account(Ethereum)
based transactions and implementing a simple ledger over the blockchain

### Prerequisites

Make sure to install Flask and the Requests library:

```
$ pip install Flask==0.12.2 requests==2.18.4 
```

Run blockchain.py to start node servers (default = 5) that start
listening on ports default starting from 5000

```
$ python blockchain.py 
```

Run generate_transactions.py specifying port numbers that send
transactions as http requests to above ports
Run above script from "transactions" branch for UTXO(Bitcoin)
based transactions or from "account_transactions" for account
(Ethereum) based transactions

```
$ python generate_transactions.py 5000 5001 5002 5003 5004
```

Live visualization of blockchain and ledger using html files
in templates directory.