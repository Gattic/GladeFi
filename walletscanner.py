import sys
from datetime import datetime
from web3 import Web3
from wallet import Wallet
from chain import Chain

PAIR_CREATED_EVENT_HASH = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()
SYNCING_EVENT_HASH = Web3.keccak(text="Sync(uint112,uint112,uint256)").hex()
TRANSFER_EVENT_HASH = "0x"+Web3.keccak(text="Transfer(address,address,uint256)").hex()

TS_DAY = 86400
TS_WEEK = 604800
TS_MONTH = 2592000

class WalletScanner:

    def __init__(self, newWalletName):

        self.chain = Chain("ETH")
        
        # Wallet address
        wallet = Wallet(newWalletName)
        print("Wallet address:", wallet.address)
        walletAddress = Web3.to_checksum_address(wallet.address)
        
        # Vars for the loop
        cBlock = self.chain.web3.eth.block_number
        transactions = []

        # Fetch logs
        while(True):
            
            block = self.chain.web3.eth.get_block(cBlock, full_transactions=True)
            ts = block["timestamp"]
            print(f"Formatted Datetime: {datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
        
            tCounter = 0
            for tx in block.transactions:
                if tx["from"] == walletAddress or tx["to"] == walletAddress:
                    if tCounter == 0:
                        print("===========================")
                    print(tx)
                    print("-----")
                    print(f"Transaction {tx['hash'].hex()} at block {tx['blockNumber']}")
                    print(f"from {tx['from']} to {tx['to']} value {tx['value']}")
                    print("-----")
                    transactions.append(tx)
                    tCounter = tCounter + 1
        
            if tCounter > 0:
                print("===========================")
        
            cBlock -= 1

#Test
if len(sys.argv) > 1:
    walletName = sys.argv[1]
    WalletScanner = WalletScanner(walletName)
else:
    print("Usage: python walletscanner.py <wallet_name>")
