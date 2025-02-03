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
import random
from eth_account import Account
import secrets

        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class WalletCreator:

    def __init__(self, newWalletFName):

        # Need to enable an unstable feature of this lib
        Account.enable_unaudited_hdwallet_features()

        print("----------------------")

        # Generate a random private key
        private_key = "0x" + secrets.token_hex(32)
        
        # Create an account object from the private key
        account = Account.from_key(private_key)
        
        # Wallet Address
        address = account.address
        print(f"Wallet Address: {address}")
        print(f"Private Key: {private_key}")

        print("----------------------")
        
        # Mnemonic Phrase
        #mnemonic, mnemonic_phrase = Account.create_with_mnemonic()
        #mnemonic_address = mnemonic.address

        #print(f"Generated Address from Mnemonic: {mnemonic_address}")
        #print(f"Mnemonic Phrase: {mnemonic_phrase}")

        # Save keys securely
        with open(newWalletFName, "w") as file:
            #file.write(f"{address}\n")
            file.write(f"{private_key}\n")
            #file.write(f"Mnemonic Phrase: {mnemonic}\n")
            #file.write(f"Mnemonic Address: {mnemonic_address}\n")
        
        print("Wallet details saved to " + newWalletFName +"!")
        
# Test
if sys.argv[0] == "walletcreator.py" and len(sys.argv) > 1:
    walletName = sys.argv[1]
    if walletName == "":
        print("Use: python walletcreator.py <walletName>")
        sys.exit(1)
    WalletCreator = WalletCreator(walletName)
else:
    print("Use: python walletcreator.py <walletName>")
