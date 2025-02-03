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
from pool import Pool
import json
import random
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class Sniper:

    def __init__(self, newChainName, snipeWalletName, newContractAddr):

        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        wallet = Wallet(snipeWalletName)

        # Setup the token contract
        contract = Contract("MyToken.sol")
        contract.loadABI(Contract.ABI_PATH_ERC20)
        contract.setContractAddress(newContractAddr)

        pool = Pool(self.chain, contract)
        pool.load(wallet)
        pool.printBalance(wallet)

        # Check if the liquidity pool has anything in it
        if pool.isEmpty(wallet):
            print("Pool is empty...")
            sys.exit(1)

        print("Sniping...")

        #pool.swapETHForTokens(wallet, 0.001, 10)
        #pool.swapETHForTokensViaTokens(wallet, 1, 10)
        #pool.swapETHForTokensViaWalletPercent(wallet, 100, 10)
        pool.swapETHForTokensViaPoolPercent(wallet, 1, 10)
        #pool.swapTokensForETH(wallet, 100000, 20)

# Test
chainName = "local"
if sys.argv[0] == "sniper.py" and len(sys.argv) > 2:
    newContractAddr = sys.argv[1]
    Sniper = Sniper(chainName, ".wallet-local-env2", newContractAddr)

