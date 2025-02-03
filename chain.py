import sys
#import solcx
#import web3-ethereum-defi
import asyncio
from aiohttp import ClientSession
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

chains = [
    "eth",
    "bsc",
    "avax",
    "ftm",
    "base",
    "local"
]

chain_ids = {
    "eth": 1,
    "bsc": 56,
    "avax": 43114,
    "ftm": 250,
    "base": 8453,
    "local": 1337
}

chain_tokens = {
    "eth": "ETH",
    "bsc": "BSC",
    "avax": "AVAX",
    "ftm": "FTM",
    "base": "ETH",
    "local": "ETH"
}

chain_gas = {
    "eth" : "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=",
    "bsc" : "https://gbsc.blockscan.com/gasapi.ashx?apikey=key&method=pendingpooltxgweidata",
    "avax" : "https://gavax.blockscan.com/gasapi.ashx?apikey=key&method=pendingpooltxgweidata",
    "ftm" : "https://gftm.blockscan.com/gasapi.ashx?apikey=key&method=pendingpooltxgweidata",
    "base": "https://www.ethgastracker.com/api/gas/latest/base",
    "local" : "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey="
}

CHAIN_GAS_SLOW = 0
CHAIN_GAS_NORMAL = 1
CHAIN_GAS_FAST = 2

chain_gas_options = {
    "eth" : ["SafeGasPrice", "ProposeGasPrice", "FastGasPrice"],
    "bsc" : ["standardgaspricegwei", "fastgaspricegwei", "rapidgaspricegwei"],
    "avax" : ["standardgaspricegwei", "fastgaspricegwei", "rapidgaspricegwei"],
    "ftm" : ["standardgaspricegwei", "fastgaspricegwei", "rapidgaspricegwei"],
    "base": ["slow", "normal", "fast"],
    "local" : ["SafeGasPrice", "ProposeGasPrice", "FastGasPrice"]
}

chain_rpcs = {
    "eth" : "https://rpc.ankr.com/eth",
    "bsc" : "https://bsc-dataseed.binance.org/",
    "avax" : "https://rpc.ankr.com/avalanche",
    "ftm" : "https://rpc.ankr.com/fantom",
    "base": "https://mainnet.base.org",
    "local" : "http://localhost:8545"
}

chain_weth = {
    "eth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "base": "0x4200000000000000000000000000000000000006",
    "local": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
}

#uniswap
chain_router = {
    "eth": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "base": "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24",
    "local": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
}

#uniswap
chain_factory = {
    "eth": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    "base": "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6",
    "local": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
}

load_dotenv(".api-etherscan")
apikeyEtherscan = getenv("API_KEY_ETHERSCAN")

class Chain:

    def __init__(self, name):
        self.name = name.lower()
        self.rpcURL = ""
        self.gasURL = ""
        self.token = ""
        self.web3 = None

        if not self.validChain():
            print("Invalid chain")
            return

        #Load the chain env vars
        self.rpcURL=self.getRPC()
        self.gasURL=self.getGasURL()
        self.token=self.getToken()

        #print(self.name)
        #print(self.rpcURL)
        #print(self.gasURL)
        #print(self.token)

        # Our web3 instances
        self.web3 = Web3(HTTPProvider(self.rpcURL))
        print(f'Connected to chain: { self.name }')

    def validChain(self):
        return self.name in chains

    def getRPC(self):
        self.name = self.name.lower()
        return chain_rpcs[self.name]

    def getGasURL(self):
        self.name = self.name.lower()
        retGasURL = chain_gas[self.name]
        if self.name == "eth" or self.name == "local":
            if 'apikeyEtherscan' in globals() or apikeyEtherscan == None:
                apikeyEtherscan = ""
            retGasURL += apikeyEtherscan
        return retGasURL

    def getToken(self):
        self.token = self.token.lower()
        return chain_tokens[self.name]

    async def getGas(self, gas_option=CHAIN_GAS_FAST):
        async with ClientSession() as session:
            async with session.get(self.getGasURL()) as response:
                print(f'Gas URL: { self.getGasURL() }')
                response.raise_for_status()
                resp = await response.json()
                if self.name == "eth" or self.name == "local":
                    result = resp['result']
                    print( int((float(result[chain_gas_options[self.name][gas_option]]) + 1) * 1e9))
                    return( int((float(result[chain_gas_options[self.name][gas_option]]) + 1) * 1e9))
                elif self.name == "base":
                    result = resp['data']['oracle']
                    print( int((result[chain_gas_options[self.name][gas_option]]['gwei']+ 1) * 1e9))
                    return int((result[chain_gas_options[self.name][gas_option]]['gwei']+ 1) * 1e9)
                else:
                    result = resp['result']
                    print( int((result[chain_gas_options[self.name][gas_option]] + 1) * 1e9))
                    return int((result[chain_gas_options[self.name][gas_option]] + 1) * 1e9)
                return 0

    def getRouter(self):
        return chain_router[self.name]

    def getFactory(self):
        return chain_factory[self.name]

    def getWETH(self):
        return chain_weth[self.name]

    def estimateGas(self, txn):
        # Fetch the gas price
        loop = asyncio.get_event_loop()
        gasPrice = loop.run_until_complete(self.getGas())
        
        # Sign and Deployment here
        gasGuess = self.web3.eth.estimate_gas(txn);

        #print(f'Estimated gas: { gasGuess }')
        #print(f'Estimated gas price: { gasPrice }')
        #print(f'Estimated cost: { gasGuess * gasPrice }')
        txnCost = gasGuess * gasPrice
        print(f'Estimated cost (ETH): { self.web3.from_wei(txnCost, "ether") }')
        return txnCost

    def deploy(self, wallet, contract, *fncParams, submitTxn=True):
        # Fetch the gas price
        loop = asyncio.get_event_loop()
        gasPrice = loop.run_until_complete(self.getGas())

        if gasPrice == None or gasPrice == 0:
            print("RPC Error")
            return None
        
        contractInstance = self.web3.eth.contract(abi=contract.abi, bytecode=contract.bytecode)

        # Build the transaction
        txn = None
        if submitTxn:
            print("----TRANSACTION----")
        else:
            print("----TRANSACTION (NO SUBMIT)----")
        print(f'Chain Name: { self.name }')
        print(f'Contract Address: { contract.address }')
        print(f'Constructor Params: { fncParams }')
        #print(f'Gas Price: { gasPrice }')
        print(f'Wallet Address: { wallet.address }')

        txnArgs = {
                'chainId': chain_ids[self.name],
                'from': wallet.address,
                'nonce': self.web3.eth.get_transaction_count(wallet.address),
                'gasPrice': gasPrice
            }
        if len(fncParams) == 0:
            txn = contractInstance.constructor().build_transaction(txnArgs)
        else:
            txn = contractInstance.constructor(*fncParams).build_transaction(txnArgs)

        if not submitTxn:
            return txn

        # Sign and Deployment here
        tx_create = self.web3.eth.account.sign_transaction(txn, wallet.privKey)
        tx_hash = self.web3.eth.send_raw_transaction(tx_create.raw_transaction)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f'Contract deployed at address: { tx_receipt.contractAddress }')
        return tx_receipt.contractAddress

    def observe(self, wallet, contract, fncName, *fncParams):
        contractInstance = self.web3.eth.contract(address=Web3.to_checksum_address(contract.address), abi=contract.abi, bytecode=contract.bytecode)
        method_to_call = getattr(contractInstance.functions, fncName)
        result = None
        if len(fncParams) == 0:
            result = method_to_call().call()
        else:
            result = method_to_call(*fncParams).call()
        print(result)
        return result

    def interact(self, wallet, contract, fncName, *fncParams, value=None, submitTxn=True):
        # Fetch the gas price
        loop = asyncio.get_event_loop()
        gasPrice = loop.run_until_complete(self.getGas())

        contractInstance = self.web3.eth.contract(address=Web3.to_checksum_address(contract.address), abi=contract.abi, bytecode=contract.bytecode)

        # Build the transaction
        txn = None
        if submitTxn:
            print("----TRANSACTION----")
        else:
            print("----TRANSACTION (NO SUBMIT)----")
        print(f'Chain Name: { self.name }')
        print(f'Contract Address: { contract.address }')
        print(f'Function Name: { fncName }')
        print(f'Function Params: { fncParams }')
        #print(f'Gas Price: { gasPrice }')
        print(f'Wallet Address: { wallet.address }')

        txnArgs = {
                'from': wallet.address,
                #'to': contract.address,
                'nonce': self.web3.eth.get_transaction_count(wallet.address),
                'gasPrice': gasPrice
            }
        if not value is None:
            txnArgs['value'] = value

        if not submitTxn:
            return txnArgs
        
        method_to_call = getattr(contractInstance.functions, fncName)
        if len(fncParams) == 0:
            txn = (method_to_call().build_transaction(txnArgs))
        else:
            txn = (method_to_call(*fncParams).build_transaction(txnArgs))

        tx_create = self.web3.eth.account.sign_transaction(txn, wallet.privKey)
        tx_hash = self.web3.eth.send_raw_transaction(tx_create.raw_transaction)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        print(f'Transaction Receipt: { tx_receipt }')
        return tx_receipt

    def getLogs(self, cAddress, fromBlock=None, toBlock="latest", event=None):
        if fromBlock is None:
            fromBlock=self.web3.eth.block_number - 100
        if event is None:
            return self.web3.eth.get_logs({
                'fromBlock': fromBlock,
                'toBlock': toBlock,
                'address': cAddress
            })

        #else
        return self.web3.eth.get_logs({
            'fromBlock': fromBlock,
            'toBlock': toBlock,
            'address': cAddress,
            'topics': [event]
        })

    def getBlockNumber(self):
        return self.web3.eth.block_number

# Test
#chain = Chain("BASE")
#loop = asyncio.get_event_loop()
#gasPrice = loop.run_until_complete(chain.getGas())
