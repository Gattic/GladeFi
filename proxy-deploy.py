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

class ProxyDeploy:
    def __init__(self):

        # Setup the chain
        self.chain = Chain("local")

        # Load the wallets
        wallet = Wallet(".wallet-local-env")
        taxWallet = Wallet(".wallet-local-env-tax")
        safeWallet = Wallet(".wallet-local-env-safe")

        #Test with a basic counter contract
        #counterContract = Contract(".env-contract-local2")
        #newContractAddress = self.chain.deploy(wallet, counterContract)
        #counterContract.setContractAddress(newContractAddress)
        #self.chain.observe(wallet, counterContract, "get")

        # 1. Setup the token contract, we deploy later
        contract = Contract("TestToken.sol")
        contract.compile("contracts/", "node_modules")

        # 2. Setup the proxy admin contract, we deploy later
        proxyAdminContract = Contract("ProxyAdmin.sol")
        proxyAdminContract.compile("node_modules/@openzeppelin/contracts/proxy/transparent/", "node_modules")

        # 3. Setup the proxy contract, we deploy later
        proxyContract = Contract("TransparentUpgradeableProxy.sol")
        proxyContract.compile("node_modules/@openzeppelin/contracts/proxy/transparent/", "node_modules")

        # 1. Deploy the contract
        newContractAddress = self.chain.deploy(wallet, contract)
        contract.setContractAddress(newContractAddress)

        # 2. Deploy the proxy admin contract with the implementation contract address as a parameter
        proxyAdminContractAddress = self.chain.deploy(wallet, proxyAdminContract, contract.address)
        proxyAdminContract.setContractAddress(proxyAdminContractAddress)

        # 3. Deploy the proxy contract and initialize it
        # We initialize the proxy contract with the implementation contract address and the proxy admin contract address
        # This is done by calling the initialize function of the proxy contract
        contractInstance = self.chain.web3.eth.contract(address=contract.address, abi=contract.abi, bytecode=contract.bytecode)
        initializer_data = contractInstance.encode_abi("initialize")
        proxyContractAddress = self.chain.deploy(wallet, proxyContract,
            contract.address,
            proxyAdminContractAddress,
            initializer_data)
        proxyContract.setContractAddress(proxyContractAddress)

        #web3.exceptions.ContractLogicError: ('execution reverted: VM Exception while processing transaction: invalid opcode', {'hash': None, 'programCounter': 1680, 'result': '0x', 'reason': None, 'message': 'invalid opcode'})
        # Fix:


        #self.chain.interact(wallet, proxyContract, "initialize")

        # Set various contract parameters
        self.chain.interact(wallet, proxyContract, "setTaxReceiver", taxWallet.address)
        self.chain.interact(wallet, contract, "setTaxes", 500, 500, 100)
        #self.chain.interact(wallet, contract, "mint", safeWallet.address, 100)
        #self.chain.interact(wallet, contract, "addTaxableSwapPair". pairAddress)

        # Testing
        #self.chain.observe(wallet, contract, "name")
        print("Balance:")
        self.chain.observe(wallet, contract, "balanceOf", wallet.address)
        self.chain.observe(taxWallet, contract, "balanceOf", taxWallet.address)
        self.chain.observe(safeWallet, contract, "balanceOf", safeWallet.address)

        #Check number of total tokens
        print("Total Supply:")
        self.chain.observe(wallet, contract, "totalSupply")

        role = Web3.keccak(text="DEFAULT_ADMIN_ROLE")
        is_admin = self.chain.observe(wallet, contract, "hasRole", role, wallet.address)
        print("Is Admin:", is_admin)

        
# Test
proxyDeploy = ProxyDeploy()
