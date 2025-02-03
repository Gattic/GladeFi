import sys
import solcx
#import web3-ethereum-defi
import asyncio
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
from wallet import Wallet
from solcx import set_solc_version, compile_source
import json

# Set Solidity version to 0.8.19
#set_solc_version('0.8.19')

# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class Contract:

    ABI_PATH_ERC20 = "abis/erc20.abi"
    ABI_PATH_UNISWAPV2ROUTER02 = "abis/UniswapV2Router02.abi"
    ABI_PATH_UNISWAPV2FACTORY02 = "abis/UniswapV2Factory02.abi"

    def __init__(self, contractName):
        self.address = ""
        self.name = contractName
        self.abi = ""
        self.bytecode = ""

        #Check if the contract configuration is valid
        if not len(self.name):
            print("Bad contract name!")
            return

    def loadABI(self, fname):
        with open(fname, "r") as f:
            self.abi = json.load(f)

    def compile(self, contractPath, importPath):
        #Check if the contract configuration is valid
        if not len(self.name) or not len(contractPath) or not len(importPath):
            print("Bad contract configuration!")
            print("Aborting contract compilation...")
            sys.exit(1)

        # Compile the contract
        #print("Contract Path: "+contractPath+self.name)
        compiledFile = solcx.compile_files(contractPath+self.name,
            output_values=["abi", "bin", "bin-runtime", "srcmap", "srcmap-runtime"],
            allow_paths=[contractPath, contractPath, importPath],
            import_remappings={
            "@openzeppelin/": f"{importPath}/@openzeppelin/"
            }
        )
        rawName = self.name.split(".")[0]
        self.abi = compiledFile[contractPath+self.name+":"+rawName]['abi']
        self.bytecode = compiledFile[contractPath+self.name+":"+rawName]['bin']

        #print("====================================================")

    def compile_with_standard(self, contractPath, importPath):
        # Check if the contract configuration is valid
        if not len(self.name) or not len(contractPath) or not len(importPath):
            print("Bad contract configuration!")
            print("Aborting contract compilation...")
            sys.exit(1)

        # Read the contract source code
        source_code = ""
        with open(contractPath + self.name, "r") as file:
            source_code = file.read()

        blackListablePath = contractPath
        blackListableName = "Blacklistable.sol"
        blackListableSource = ""
        with open(blackListablePath + blackListableName, "r") as file:
            blackListableSource = file.read()

        # Prepare the input for compile_standard
        compiler_input = {
            "language": "Solidity",
            "sources": {
                self.name: {
                    "content": source_code
                },
                "Blacklistable.sol": {
                    "content": blackListableSource
                }
            },
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                },
                "outputSelection": {
                    "*": {
                        "*": ["abi", "bin", "bin-runtime", "srcmap", "srcmap-runtime", "metadata", "evm"]
                    }
                },
                "metadata": {
                    "useLiteralContent": True  # Embed full source code in metadata
                },
                "remappings":
					[f"@openzeppelin={importPath}/@openzeppelin/", "./=./"]
            }
        }

        # Compile using compile_standard
        compiled = solcx.compile_standard(
            compiler_input,
            solc_version="0.8.28",
            allow_paths=[contractPath, importPath]
        )

        # Extract ABI and bytecode
        rawName = self.name.split(".")[0]
        contract_data = compiled['contracts'][self.name][rawName]
        self.abi = contract_data['abi']
        self.bytecode = contract_data['evm']['bytecode']['object']

        # Save metadata (optional)
        with open("metadata.json", "w") as file:
            json.dump(json.loads(contract_data['metadata']), file, indent=4)

        print(f"Contract {self.name} compiled successfully with embedded metadata!")


    def setContractAddress(self, contractAddress):
        self.address = contractAddress
        

# Test
#contract = Contract(".env-contract-local")

