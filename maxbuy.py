import sys
#import solcx
#import web3-ethereum-defi
import asyncio
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
from chain import Chain
from contract import Contract
from wallet import Wallet
import json
import random
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class UpdateMaxBuy:

    def __init__(self, newChainName, snipeWalletName, newContractAddr):

        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        wallet = Wallet(snipeWalletName)

        # Setup the token contract
        #contract = Contract("BuyAI.sol")
        #contract.setContractAddress(newContractAddr)
        #with open("abis/erc20.abi", "r") as f:
            #contract.abi = json.load(f)
        contract = Contract("MyToken.sol")
        contract.compile("contracts/", "node_modules")
        contract.setContractAddress(newContractAddr)

        #pool = Pool(self.chain, contract)

        self.chain.interact(wallet, contract, "setMaxBuy", 100)
        
# Test
if len(sys.argv) > 2:
    chainName = sys.argv[1]
    contractAddress = sys.argv[2]
    UpdateMaxBuy = UpdateMaxBuy(chainName, ".wallet-local", contractAddress)
else:
    print("Usage: maxbuy.py <chain> <contract address>")
    sys.exit(1)


