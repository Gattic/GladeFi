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
import random
import copy
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

PAIR_CREATED_EVENT_HASH = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()
SYNCING_EVENT_HASH = Web3.keccak(text="Sync(uint112,uint112,uint256)").hex()
TRANSFER_EVENT_HASH = Web3.keccak(text="Transfer(address,address,uint256)").hex()

class PairListener:

    def __init__(self, newChainName="ETH"):

        self.pairs = {}

        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        wallet = Wallet(".wallet-env")

        # Setup the token contract
        contract = Contract("FixedToken.sol")
        contract.loadABI(Contract.ABI_PATH_ERC20)

        # Pool object
        pool = Pool(self.chain)

        # Loop through the logs and find created pools:
        pairCreatedEvent = "0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"

        print("Listening for new pairs...")

        # Listen to the uniswap factory for new pairs by searching for the event PairCreated in the logs
        currentBlock = self.chain.getBlockNumber()
        while True:
            # Get the latest block
            latestBlock = self.chain.getBlockNumber()
            if latestBlock > currentBlock:
                logs = self.chain.getLogs(pool.factoryContract.address, currentBlock)

                for log in logs:
                    print(f"Log: {log}")
                    # Check if the first topic matches the PairCreated event signature
                    if log["topics"][0].hex() == pairCreatedEvent:
                        print(f"Pair created! Data: {log['data'].hex()}")

                        # Set token0
                        token0Addr = Web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
                        token0Contract = copy.deepcopy(contract)
                        token0Contract.setContractAddress(token0Addr)

                        token0Name = self.chain.observe(wallet, token0Contract, "name")
                        print("Token0 Name: " + token0Name)
                        print("Token0 Address: " + token0Addr)
                        print("https:https://etherscan.io/address/" + token0Addr)

                        print("-----------------")

                        # Set token1
                        token1Addr = Web3.to_checksum_address('0x' + log['topics'][2].hex()[-40:])
                        token1Contract = copy.deepcopy(contract)
                        token1Contract.setContractAddress(token1Addr)

                        token1Name = self.chain.observe(wallet, token1Contract, "name")
                        print("Token1 Name: " + token1Name)
                        print("Token1 Address: " + token1Addr)
                        print("https:https://etherscan.io/address/" + token1Addr)

                        print("-----------------")

                        pairAddrRaw = log["data"].hex()[24:64]  # Skip the first 12 bytes (24 hex characters)
                        pairAddr = Web3.to_checksum_address("0x" + pairAddrRaw)
                        self.pairs[token1Name] = pairAddr

                        print("Pair Address: " + pairAddr)
                        print("https:https://etherscan.io/address/" + pairAddr)
                        print("===========================")

                currentBlock = latestBlock

# Test
chainName = "ETH"
if len(sys.argv) > 1:
    chainName = sys.argv[1]
PairListener = PairListener(chainName)
