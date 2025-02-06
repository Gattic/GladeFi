import sys
#import solcx
#import web3-ethereum-defi
import asyncio
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
from chain import Chain
from contract import Contract
from publicwallet import PublicWallet
from pool import Pool
import json
import random
from eth_account import Account

        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class WalletViewer:

    def __init__(self, newChainName,  walletAddr):

        # Need to enable an unstable feature of this lib
        Account.enable_unaudited_hdwallet_features()

        self.chain = Chain(newChainName)

        self.wallet = PublicWallet(walletAddr)

        print("----------------------")

        # Wallet Address
        print(f"Wallet Address: {self.wallet.address}")
        #print(f"Private Key: {wallet.privKey}")

        # Print eth in wallet
        weiBalance = self.wallet.getBalance(self.chain)
        ethBalance = self.wallet.getBalanceETH(self.chain)
        print(f"Balance: {ethBalance} ETH")
        print(f"Balance: {weiBalance} WEI")

        print("----------------------")

        dataSendBack = {
            "ETH Balance": ethBalance,
            "WEI Balance": weiBalance
        }

        print(json.dumps(dataSendBack))
        
# Test
if len(sys.argv) > 2:
    chainName = sys.argv[1]
    walletAddr = sys.argv[2]
    
    wv = WalletViewer(chainName, walletAddr)

    # All additional contracts are arguments
    for contractAddr in sys.argv[3:]:
        contract = Contract("MyToken.sol")
        contract.loadABI(Contract.ABI_PATH_ERC20)
        contract.setContractAddress(contractAddr)
        pool = Pool(wv.chain, contract)
        pool.load(wv.wallet)
        pool.printBalance(wv.wallet)
else:
    print("Usage: python walletviewer.py <chain> <walletAddr> [contract1, contract2, ...]")
    print(json.dumps({"error": "Invalid arguments"})) 
