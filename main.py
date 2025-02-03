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
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class GladesDeFi:
    def __init__(self, newContractAddr):

        # Setup the chain
        self.chain = Chain("ETH")

        # Load the wallets
        wallet = Wallet(".wallet-env")

        # Setup the token contract
        contract = Contract("MyToken.sol")
        contract.loadABI(Contract.ABI_PATH_ERC20)
        contract.setContractAddress(newContractAddr)
        
# Test
glades = GladesDeFi()

fileName = sys.argv.pop(0)
if len(sys.argv) == 3:
    newContractAddr = sys.argv.pop(0)
    methodType = sys.argv.pop(0)
    fncName = sys.argv.pop(0)
    if methodType == "observe":
        glades.chain.observe(fncName, sys.argv)
    elif methodType == "interact":
        glades.chain.interact(fncName, sys.argv)
    else:
        print("Bad operation!")
elif len(sys.argv) != 0:
    print("Usage: "+fileName+" [contractAddr] {observe,interact} [sol-fncName]")
