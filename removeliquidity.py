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
from sniper import Sniper
from walletcreator import WalletCreator
from pool import Pool
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

# NEEDS TESTING!!!!!!!!!!!!!!!!!!!!!!!!!!!

class RemoveLiq:

    #PAIR_CREATED_EVENT_HASH = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()

    def __init__(self, newChainName, newContractAddress):

        walletName = ".wallet-deployer"

        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        wallet = Wallet(walletName)

        # Setup the token contract
        contract = Contract("MyToken.sol")
        contract.loadABI(Contract.ABI_PATH_ERC20)
        contract.setContractAddress(newContractAddress)

        # Testing
        pool = Pool(self.chain, contract)
        pool.load(wallet)
        pool.printBalance(wallet)

        pool.removeLiquidityETH(wallet, 2)

        if pool.isEmpty(wallet):
            print("Pool is empty!")
        else:
            print("Pool is NOT empty!")
        
# Test
if sys.argv[0] == "removeliquidity.py" and len(sys.argv) > 2:
    chainName = sys.argv[1]
    newContractAddress = sys.argv[2]
    RemoveLiq = RemoveLiq(chainName, newContractAddress)
