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

class TokenDeploy:

    #PAIR_CREATED_EVENT_HASH = Web3.keccak(text="PairCreated(address,address,address,uint256)").hex()

    def __init__(self, newChainName="local"):

        walletName = ".wallet-local-env"
        taxWalletName = ".wallet-local-env-tax"

        # Setup the chain
        self.chain = Chain(newChainName)
        if not self.chain.validChain():
            print("Invalid chain")
            sys.exit(1)

        # Load the wallets
        wallet = Wallet(walletName)
        taxWallet = Wallet(taxWalletName)

        # Setup the token contract
        contract = Contract("MyToken.sol")
        contract.compile("contracts/", "node_modules")

        # Estimate the gas based on an unsubmitted transaction
        deployTxn = self.chain.deploy(wallet, contract, submitTxn=False)
        gasEstimate = self.chain.estimateGas(deployTxn)
        print(f"Gas Estimate: { Web3.from_wei(gasEstimate, 'ether') }")

        # Deploy the contract
        newContractAddress = self.chain.deploy(wallet, contract)
        contract.setContractAddress(newContractAddress)

        # Set various contract parameters
        self.chain.interact(wallet, contract, "setTaxReceiver", taxWallet.address)
        self.chain.interact(wallet, contract, "setTaxes", 500, 500, 100)
        #self.chain.interact(wallet, contract, "mint", safeWallet.address, 100)

        #decimals = self.chain.observe(wallet, contract, "decimals")
        pool = Pool(self.chain, contract)

        slippage_tolerance = 2 # 2% slippage
        eth_amount = 1.5
        receipt = pool.addLiquidityETH(wallet, slippage_tolerance, eth_amount)

        # Query for the pair address using the token addresses
        pair_address = pool.getPair(wallet)
        print(f"New Liquidity Pool Address: {pair_address}")

        self.chain.interact(wallet, contract, "addTaxableSwapPair", pair_address)

        #Snipe
        tokenSniper = Sniper(self.chain.name, ".wallet-local-env2", contract.address)

        # Testing
        pool.printBalance(wallet)
        pool.printBalance(taxWallet)
        
# Test
chainName = "local"
if sys.argv[0] == "token-deploy.py" and len(sys.argv) > 1:
    chainName = sys.argv[1]
TokenDeploy = TokenDeploy(chainName)
