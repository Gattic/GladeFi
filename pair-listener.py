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
import os
from datetime import datetime, timezone
import json
import platform

if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl

# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

PAIR_CREATED_EVENT_HASH = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()
SYNCING_EVENT_HASH = Web3.keccak(text="Sync(uint112,uint112,uint256)").hex()
TRANSFER_EVENT_HASH = Web3.keccak(text="Transfer(address,address,uint256)").hex()

class PairListener:

    def __init__(self, newChainName="ETH"):

        self.chain_name = newChainName
        self.pairs = {}
        self.processed_pairs = set()
        self.processed_blocks = 0 #Track processed block count for resetting set, so it doesn't go indefinitely
        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        self.wallet = Wallet(".wallet-env")

        # Setup the token contract
        self.contract = Contract("FixedToken.sol")
        self.contract.loadABI(Contract.ABI_PATH_ERC20)

        # Pool object
        self.pool = Pool(self.chain)

        print("Listening for new pairs...")

        self.listen_for_pairs()


    def listen_for_pairs(self):
        # Loop through the logs and find created pools:
        pairCreatedEvent = "0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"

        # Listen to the uniswap factory for new pairs by searching for the event PairCreated in the logs
        currentBlock = self.chain.getBlockNumber()
        utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        while True:
            # Get the latest block
            latestBlock = self.chain.getBlockNumber()
            if latestBlock > currentBlock:
                logs = self.chain.getLogs(self.pool.factoryContract.address, currentBlock)

                for log in logs:
                    print(f"Log: {log}")
                    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                    # Check if the first topic matches the PairCreated event signature
                    if log["topics"][0].hex() == pairCreatedEvent:
                        print(f"Pair created! Data: {log['data'].hex()}")

                        # Set token0
                        token0Addr = Web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])
                        token0Contract = copy.deepcopy(self.contract)
                        token0Contract.setContractAddress(token0Addr)

                        token0Name = self.chain.observe(self.wallet, token0Contract, "name")
                        print("Token0 Name: " + token0Name)
                        print("Token0 Address: " + token0Addr)
                        print("https:https://etherscan.io/address/" + token0Addr)

                        print("-----------------")

                        # Set token1
                        token1Addr = Web3.to_checksum_address('0x' + log['topics'][2].hex()[-40:])
                        token1Contract = copy.deepcopy(self.contract)
                        token1Contract.setContractAddress(token1Addr)

                        token1Name = self.chain.observe(self.wallet, token1Contract, "name")
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

                        if pairAddr in self.processed_pairs:
                            continue
                        self.processed_pairs.add(pairAddr)

                        log_entry = {
                            "timestamp": utc_now,
                            "token0": {
                                "name": token0Name,
                                "address": token0Addr,
                            },
                            "token1": {
                                "name": token1Name,
                                "address": token1Addr,
                            },
                            "pair": {
                                "address": pairAddr,
                                "etherscan": f"https://etherscan.io/address/{pairAddr}"
                            }
                        }

                        log_entry_json = json.dumps(log_entry, indent = 4)
                        print(log_entry_json)
                        self.write_to_file_with_lock(today_date, log_entry_json)

                currentBlock = latestBlock
                self.processed_blocks += 1

                if self.processed_blocks >= 100:
                    print("Clearing processed_pairs to free memory")
                    self.processed_pairs.clear()
                    self.processed_blocks = 0

    def write_to_file_with_lock(self, date, content):
        """Writes to a daily log file with file locking to prevent read/write conflicts"""
        log_dir = os.path.join("pair_logs", self.chain_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_path = os.path.join(log_dir, f"{date}_pairs.txt")

        #Convert content to NDJSON (Newline-Delimited JSON)
        json_content = json.dumps(content, separators=(",", ":")) #Minified JSON format

        with open(file_path, "a", encoding="utf-8") as f:
            self.lock_file(f)
            f.write(content + "\n")
            self.unlock_file(f)

    def lock_file(self, file):
        """Locks the file to prevent a simultaneous write (cross-platform support)."""
        if platform.system() == "Windows":
            msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)


    def unlock_file(self, file):
        """Unlock the file after writing is complete."""
        if platform.system() == "Windows":
            msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file.fileno(), fcntl.LOCK_UN)

# Test
chainName = "ETH"
if len(sys.argv) > 1:
    chainName = sys.argv[1]
PairListener = PairListener(chainName)
