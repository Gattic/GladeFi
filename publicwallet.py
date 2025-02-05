import sys
#import solcx
#import web3-ethereum-defi
import asyncio
from aiohttp import ClientSession
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
from web3 import Web3, Account
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class PublicWallet:

    def __init__(self, walletAddr):
        self.address = walletAddr

        if not len(walletAddr):
            print("Invalid wallet file!")
            return

        if PublicWallet.validate(self.address):
            print("Wallet Initialized " + self.address)
        else:
            print("Invalid wallet!")
            sys.exit(1)

    @staticmethod
    def validate(testAddr):
        return Web3.is_address(testAddr) and Web3.is_checksum_address(testAddr)

    def getBalance(self, chain):
        return chain.web3.eth.get_balance(self.address)

    def getBalanceETH(self, chain):
        return Web3.from_wei(self.getBalance(chain), 'ether')

# Test
#testWallet = PublicWallet(".env-wallet-local")

