# WARNING

TEST EVERYTHING IN A LOCAL ENVIRONMENT BEFORE USING IT IN ANY LIVE SITUATION!!
ALL FEATURES ARE TO BE CONSIDERED EXPERIMENTAL AND MAY NOT WORK AS INTENDED.
USE AT YOUR OWN RISK.

# Setup

`pip install --use-deprecated=legacy-resolver -r requirements.txt`

-Put your etherscan api key in .api-etherscan
`API_KEY_ETHERSCAN=apiKey`

# Info


Chains:
ETH
BASE
local (ganache)

Safe (Still recommend further testing):
Pair listener
Token deploy
Wallet Creator
Wallet Viewer
Wallet Loader
Sniper

UNSAFE:
Proxy deploy will not allow us to interact with the contract properly


#TODO

- Test and clean "Remove liquidity script"
- Add more chains
- Add more features
- Add more documentation
- Remove all the hardcoding and magic numbers

-Fix Home dir code:
import os
import subprocess
home_dir = os.path.expanduser("~")


https://web3py.readthedocs.io/en/stable/web3.eth.html
