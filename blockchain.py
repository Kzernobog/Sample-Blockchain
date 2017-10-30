from time import time
import hashlib
import json
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse
import requests
from textwrap import dedent

class Blockchain(object):

    chain = []
    current_transactions = []

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set() # to keep the list of nodes idempotent - keep only a singular copy
        self.new_block(proof=1, previous_hash=100)

    # Add nodes to keep track of all the nodes within the network
    def register_node(self, address):
        """
        Add a node to the list of nodes
        :param address:<str> Eg. 'http://192.168.101.23:5000'
        :return:
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    # Implementation of consensus algorithm
    def valid_chain(self, chain):
        """
        To determine the longest valid chain
        :param chain: <list> list of blocks
        :return:<bool> whether or not it is a valid chain - longest chain consensus
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    # Resolve conflicts
    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if the chain was replaced, False otherwise
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    # Create a new block
    def new_block(self, proof: int, previous_hash=None):
        """
        Create a new block
        :param proof:
        :param previous_hash:
        :return:
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    # Create a new transaction
    def new_transaction(self, sender, recipient, amount):
        """
        Adds a transaction to the list of current transactions
        :param sender:
        :param recipient:
        :param amount:
        :return index of the block to be created next:
        """
        self.current_transactions.append({'sender': sender, 'recipient': recipient, 'amount': amount})
        return self.last_block['index'] + 1

    # hash a string
    @staticmethod
    def hash(block):
        """
        Creates a SHA256 hash of the entire block
        :param block:
        :return:
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # Proof of Work
    def proof_of_work(self, last_proof, difficulty):
        """
        Sample proof of work algorithm
        :param last_proof: <int>
        :param difficulty: <int>
        :return:
        """
        proof = 0
        while self.valid_proof(last_proof, proof, difficulty) == False:
            proof += 1

        return proof

    # check for valid hash
    @staticmethod
    def valid_proof(last_proof, proof, difficulty):
        """
        Check the hash for required number leading 0s
        :param last_proof: <int>
        :param proof: <int>
        :param difficulty: number of leading zeros required <int>
        :return:
        """
        var = '0'
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == difficulty * var

    # property to keep track of last block
    @property
    def last_block(self):
        return self.chain[-1]

# instantiate the flask node
app = Flask(__name__)

# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# instantiate the blockchain
blockchain = Blockchain()

"""
Code to instantiate a web server 
The server will serve up the blockchain on GET requests and make new transactions on POST requests
"""

# Implements the mining endpoint
@app.route('/mine', methods=['GET'])
def mine():
    """
    Mining endpoint
    :return:<block data>
    """
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof, 5)

    # Code to recieve 1 bitcoin as reward
    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)
    block = blockchain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

# Implements the transaction endpoint
@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json()

    # check whether the request is as per a transaction blueprint
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return  'Missing values', 400

    # create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to block {index}'}

    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response= {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# If statement returns True if blockchain.py is run on the Python shell
# If statement returns False if blockchain.py is imported as a module into another python file
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)