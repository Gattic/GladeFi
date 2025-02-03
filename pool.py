import sys
#import solcx
#import web3-ethereum-defi
import asyncio
from aiohttp import ClientSession
from web3 import Web3, HTTPProvider, exceptions
from os import getenv
from dotenv import load_dotenv
from chain import Chain
from contract import Contract
import json
        
# If you haven't already installed the Solidity compiler, uncomment the following line
# solcx.install_solc()

class Pool:

    def __init__(self, newChain, newContract=None):

        self.chain = newChain
        self.contract = newContract
        self.pairContract = None

        self.routerContract = Contract("UniswapV2Router02.sol")
        self.routerContract.address = self.chain.getRouter()
        self.routerContract.loadABI(Contract.ABI_PATH_UNISWAPV2ROUTER02)

        self.factoryContract = Contract("UniswapV2Factory02.sol")
        self.factoryContract.address = self.chain.getFactory()
        self.factoryContract.loadABI(Contract.ABI_PATH_UNISWAPV2FACTORY02)

    def load(self, wallet):
        pair_address = self.getPair(wallet)

        # Setup the pair contract
        self.pairContract = Contract("UniswapV2Pair.sol")
        self.pairContract.setContractAddress(pair_address)
        with open("abis/UniswapV2Pair.abi", "r") as f:
            self.pairContract.abi = json.load(f)

        # Create uniswap v2 liquidity pool
    def addLiquidityETH(self, wallet, slippage_tolerance=2, eth_amount=1.5):

        total_supply = self.getTotalSupply(wallet)
        print(f"Total Supply: { Web3.from_wei(total_supply, 'ether') }")

        token_amount = int(0.8 * total_supply)
        wei_amount = Web3.to_wei(eth_amount, "ether")

        minTokens = int(token_amount * (1 - slippage_tolerance / 100))  # Min tokens (consider slippage)
        minEth = int(wei_amount * (1 - slippage_tolerance / 100))  # Min ETH (consider slippage)

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        # Create solidity checksum address
        spender_address = Web3.to_checksum_address(self.routerContract.address)
        self.chain.interact(wallet, self.contract, "approve", spender_address, total_supply)

        # Liq fnc params
        #add_liquidity_txn = router_contract.functions.addLiquidityETH(
        #token_address,  # Your FixedToken address
            #token_amount,   # Amount of tokens to add
            #min_tokens,     # Minimum number of tokens with slippage
            #min_eth,        # Minimum ETH with slippage
            #wallet_address, # Recipient of the LP tokens
            #deadline        # Transaction deadline
        #)

        allowance = self.chain.observe(wallet, self.contract, "allowance", wallet.address, spender_address)
        print(f"Allowance: {Web3.from_wei(allowance, 'ether')}")
        print(f"Token Amount: {Web3.from_wei(token_amount, 'ether')}")
        if allowance < token_amount:
            print(f"Insufficient allowance: {Web3.from_wei(allowance, 'ether')}")
            sys.exit(1)

        eth_per_token = wei_amount / token_amount
        print(f"ETH amount: { eth_amount }")
        print(f"Token amount: {Web3.from_wei(token_amount, 'ether')}")
        print(f"ETH per token: {eth_per_token}")
        print(f"Min tokens: {Web3.from_wei(minTokens, 'ether')}")
        print(f"Min ETH: {Web3.from_wei(minEth, 'ether')}")

        receipt = self.chain.interact(wallet, self.routerContract, "addLiquidityETH", self.contract.address,
            token_amount, minTokens, minEth, wallet.address, deadline, value=wei_amount)

        # Decode the pair address
        pAddr2 = None
        logs = receipt["logs"]
        for log in logs:
            # Check if it's the PairCreated event
            if log["topics"][0].hex() == "0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9":
                contract_address_raw = log["data"].hex()[24:64]  # Skip the first 12 bytes (24 hex characters)
                #print(f"Contract Address Raw: {contract_address_raw}")
                pAddr2 = Web3.to_checksum_address("0x" + contract_address_raw)
                print(f"New Liquidity Pool Address: {pAddr2}")

        if pAddr2 is None:
            print("Error: No PairCreated event found")
            sys.exit(1)

        self.load(wallet)
        return receipt

    def removeLiquidityETH(self, wallet, slippage_tolerance=2):
		# token	address	A pool token.
		# liquidity	uint	The amount of liquidity tokens to remove.
		# amountTokenMin	uint	The minimum amount of token that must be received for the transaction not to revert.
		# amountETHMin	uint	The minimum amount of ETH that must be received for the transaction not to revert.
		# to	address	Recipient of the underlying assets.
		# deadline	uint	Unix timestamp after which the transaction will revert.
		# amountToken	uint	The amount of token received.
		# amountETH	uint	The amount of ETH received.

        token0 = self.getToken0(wallet)
        token1 = self.getToken1(wallet)
        reserves = self.getReserves(wallet)

        if token0 == self.contract.address:
            ethIndex = 1
            tokenIndex = 0
        else:
            ethIndex = 0
            tokenIndex = 1

        ethReserve = reserves[ethIndex]
        tokenReserve = reserves[tokenIndex]
        print(f"Pool Eth Reserve: {Web3.from_wei(ethReserve, 'ether')}")
        print(f"Pool Token Reserve: {Web3.from_wei(tokenReserve, 'ether')}")

        # Get the amount of LP tokens we should get
        lp_tokens = self.getLPBalance(wallet)
        print(f"LP Tokens: {Web3.from_wei(lp_tokens, 'ether')}")

        # Calculate minimum amounts based on slippage
        testMinEth = int(ethReserve * (1 - slippage_tolerance / 100))
        testMinToken = int(tokenReserve * (1 - slippage_tolerance / 100))

        print("testMinToken: " + str(Web3.from_wei(testMinToken, "ether")))
        print("testMinEth: " + str(Web3.from_wei(testMinEth, "ether")))

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        spender_address = Web3.to_checksum_address(self.routerContract.address)
        self.chain.interact(wallet, self.pairContract, "approve", spender_address, lp_tokens)

        allowance = self.chain.observe(wallet, self.pairContract, "allowance", wallet.address, spender_address)
        print(f"Allowance: {Web3.from_wei(allowance, 'ether')}")

        receipt = self.chain.interact(wallet, self.routerContract, "removeLiquidityETHSupportingFeeOnTransferTokens", self.contract.address, lp_tokens, testMinToken, testMinEth, wallet.address, deadline)

        return receipt


    # Swap by specifying number of tokens
    def swapETHForTokensViaTokens(self, wallet, token_amount=1, slippage_tolerance=2):

        tokenBid = Web3.to_wei(token_amount, "ether")
        wethAddr = self.chain.getWETH()
        addrPath = [self.contract.address, wethAddr]

        # Query the amount of tokens we should receive from the swap
        amounts = self.chain.observe(wallet, self.routerContract, "getAmountsOut", tokenBid, addrPath)

        ethAmount = amounts[1] # based on addrPath
        tokenAmount = amounts[0] # based on addrPath

        return self.swapWeiForTokens(wallet, ethAmount, slippage_tolerance)

    # Swap by specifying percent of pool
    def swapETHForTokensViaPoolPercent(self, wallet, pool_percent=100, slippage_tolerance=2):

        pool_percent -= 0.1  # Subtract 0.1% to account for weird rounding errors
        totalSupply = self.getTotalSupply(wallet)

        # Do not buy more than X% of the pool
        tokenAmount = Web3.from_wei(totalSupply*(pool_percent/100), "ether")
        return self.swapETHForTokensViaTokens(wallet, tokenAmount, slippage_tolerance)

    # Swap by specifying percent of wallet balance
    def swapETHForTokensViaWalletPercent(self, wallet, wallet_percent=100, slippage_tolerance=2):
        weiBalance = wallet.getBalance(self.chain)
        ethBid = weiBalance * (wallet_percent / 100)
        return self.swapETHForTokens(wallet, ethBid, slippage_tolerance)

    # Swap by specifying raw eth
    def swapETHForTokens(self, wallet, eth_amount=0.1, slippage_tolerance=2):
        ethBid = Web3.to_wei(eth_amount, "ether")
        return self.swapWeiForTokens(wallet, ethBid, slippage_tolerance)

    # Swap by specifying raw eth
    def swapWeiForTokens(self, wallet, eth_amount, slippage_tolerance=2):
        
        #function swapExactETHForTokens(
            #uint amountOutMin,             # Minimum amount of output tokens
            #address[] calldata path,      # Array of token addresses
            #address to,                   # Recipient address
            #uint deadline                 # Transaction deadline
        #) external payable returns (uint[] memory amounts);

        if not isinstance(eth_amount, int):
            print("Error: eth_amount must be an integer")
            sys.exit(1)

        # Check how much eth is in our wallet
        ethBalance = wallet.getBalanceETH(self.chain)
        print(f"ETH Balance: {ethBalance}")

        # Get the token0 and token1 addresses
        token0 = self.getToken0(wallet)
        token1 = self.getToken1(wallet)

        # Calculate the amount of tokens we should get
        # Check how much eth is in the pair
        reserves = self.getReserves(wallet)

        if token0 == self.contract.address:
            ethIndex = 1
            tokenIndex = 0
        else:
            ethIndex = 0
            tokenIndex = 1

        ethReserve = reserves[ethIndex]
        tokenReserve = reserves[tokenIndex]
        print(f"Pool Eth Reserve: {Web3.from_wei(ethReserve, 'ether')}")
        print(f"Pool Token Reserve: {Web3.from_wei(tokenReserve, 'ether')}")

        # Calc buy amounts
        ethBid = eth_amount
        print(f"Snipe Amount: {Web3.from_wei(ethBid, 'ether')}")

        # Upper limit of balance
        weiBalance = wallet.getBalance(self.chain)
        if ethBid > weiBalance:
            ethBid = weiBalance # We will subtract gas soon
            print("Not enough eth in the wallet, sniping all eth...")
            print(f"Altered Snipe Amount: {Web3.from_wei(ethBid, 'ether')}")

        # Upper limit of pool size
        if ethBid > ethReserve:
            ethBid = int(ethReserve * 0.95)
            print("Not enough eth in the pair, sniping all eth...")
            print(f"Altered Snipe Amount: {Web3.from_wei(ethBid, 'ether')}")

        # Query the amount of tokens we should receive from the swap
        wethAddr = self.chain.getWETH()
        addrPath = [wethAddr, self.contract.address]
        amounts = self.chain.observe(wallet, self.routerContract, "getAmountsOut", ethBid, addrPath)

        ethAmount = amounts[0] # based on addrPath
        tokenAmount = amounts[1] # based on addrPath

        totalSupply = self.getTotalSupply(wallet)
        print(f"Swap: {Web3.from_wei(ethAmount, 'ether')} -> {Web3.from_wei(tokenAmount, 'ether')} Tokens ({tokenAmount/totalSupply*100}%)")

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        testMinEth = int(ethAmount * (1 - slippage_tolerance / 100))
        testMinToken = int(tokenAmount * (1 - slippage_tolerance / 100))

        testTxn = self.chain.interact(wallet, self.routerContract, "swapExactETHForTokens", testMinToken, addrPath, wallet.address, deadline, value=ethBid, submitTxn=False)
        gasEstimate = self.chain.estimateGas(testTxn)
        print(f"Gas Estimate: { Web3.from_wei(gasEstimate, 'ether') }")

        gasBuffer = gasEstimate * 4 # 4x transactions for safety
        if weiBalance < ethBid + gasBuffer:
            ethBid = weiBalance - gasBuffer
            print("Allocating gas...")
            print(f"Altered Snipe Amount: {Web3.from_wei(ethBid, 'ether')}")

        # Too small an amount to snipe, no money in the wallet
        wallet_epsilon = 0.001
        if(weiBalance - ethBid < wallet_epsilon):
            print("Insufficient funds")
            quit()

        ethBid = int(ethBid)

        # Query the amount of tokens we should receive
        amounts= self.chain.observe(wallet, self.routerContract, "getAmountsOut", ethBid, addrPath)
        tokenAmount = amounts[1] # based on addrPath
        print(f"Swap: {Web3.from_wei(ethAmount, 'ether')} -> {Web3.from_wei(tokenAmount, 'ether')} Tokens ({tokenAmount/totalSupply*100}%)")

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        spender_address = Web3.to_checksum_address(self.routerContract.address)
        self.chain.interact(wallet, self.contract, "approve", spender_address, ethBid)
        #swapExactTokensForETHSupportingFeeOnTransferTokens?
        receipt = self.chain.interact(wallet, self.routerContract, "swapExactETHForTokens", tokenAmount, addrPath, wallet.address, deadline, value=ethBid)

        print("Swap complete:")
        self.printBalance(wallet)

        return receipt

    def swapTokensForETH(self, wallet, token_amount=1, slippage_tolerance=2):
		#function swapExactTokensForTokensSupportingFeeOnTransferTokens(
  			#uint amountIn,
  			#uint amountOutMin,
  			#address[] calldata path,
  			#address to,
  			#uint deadline
		#) external;

        if not isinstance(token_amount, int):
            print("Error: token_amount must be an integer")
            sys.exit(1)

        # Check how much eth is in our wallet
        ethBalance = wallet.getBalanceETH(self.chain)
        print(f"ETH Balance: {ethBalance}")

        # Get the token0 and token1 addresses
        token0 = self.getToken0(wallet)
        token1 = self.getToken1(wallet)

        # Calculate the amount of tokens we should get
        # Check how much eth is in the pair
        reserves = self.getReserves(wallet)

        if token0 == self.contract.address:
            ethIndex = 1
            tokenIndex = 0
        else:
            ethIndex = 0
            tokenIndex = 1

        ethReserve = reserves[ethIndex]
        tokenReserve = reserves[tokenIndex]
        print(f"Pool Eth Reserve: {Web3.from_wei(ethReserve, 'ether')}")
        print(f"Pool Token Reserve: {Web3.from_wei(tokenReserve, 'ether')}")

        # Calc buy amounts
        tokenBid = Web3.to_wei(token_amount, "ether")
        print(f"Snipe Amount: {Web3.from_wei(tokenBid, 'ether')}")

        # Upper limit of balance
        tokenBalance = self.getBalance(wallet)
        if tokenBid > tokenBalance:
            tokenBid = tokenBalance
            print("Not enough tokens in the wallet, swapping all tokens...")
            print(f"Altered Swap Amount: {Web3.from_wei(tokenBid, 'ether')}")

        # Upper limit of pool size
        if tokenBid > tokenReserve:
            tokenBid = int(tokenReserve * 0.95)
            print("Not enough tokens in the pair, swapping all tokens...")
            print(f"Altered Swap Amount: {Web3.from_wei(tokenBid, 'ether')}")

        # Query the amount of tokens we should receive from the swap
        wethAddr = self.chain.getWETH()
        addrPath = [self.contract.address, wethAddr]
        amounts = self.chain.observe(wallet, self.routerContract, "getAmountsOut", tokenBid, addrPath)

        ethAmount = amounts[1] # based on addrPath
        tokenAmount = amounts[0] # based on addrPath

        totalSupply = self.getTotalSupply(wallet)
        print(f"Swap: {Web3.from_wei(tokenAmount, 'ether')} Tokens ({tokenAmount/totalSupply*100}%) -> {Web3.from_wei(ethAmount, 'ether')}")

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        testMinEth = int(ethAmount * (1 - slippage_tolerance / 100))
        testMinToken = int(tokenAmount * (1 - slippage_tolerance / 100))

        testTxn = self.chain.interact(wallet, self.routerContract, "swapExactTokensForETH", tokenBid, testMinEth, addrPath, wallet.address, deadline, submitTxn=False)
        gasEstimate = self.chain.estimateGas(testTxn)
        print(f"Gas Estimate: { Web3.from_wei(gasEstimate, 'ether') }")

        ethBid = ethAmount
        gasBuffer = gasEstimate * 4 # 4x transactions for safety
        weiBalance = wallet.getBalance(self.chain)
        if weiBalance < ethBid + gasBuffer:
            ethBid = weiBalance - gasBuffer
            print("Allocating gas...")
            print(f"Altered Snipe Amount: {Web3.from_wei(ethBid, 'ether')}")

        # Too small an amount to snipe, no money in the wallet
        wallet_epsilon = 0.001
        if(weiBalance - ethBid < wallet_epsilon):
            print("Insufficient funds")
            quit()

        ethBid = int(ethBid)

        # Query the amount of tokens we should receive
        amounts = self.chain.observe(wallet, self.routerContract, "getAmountsOut", tokenBid, addrPath)
        ethAmount = amounts[1] # based on addrPath
        print(f"Swap: {Web3.from_wei(tokenAmount, 'ether')} Tokens ({tokenAmount/totalSupply*100}%) -> {Web3.from_wei(ethAmount, 'ether')}")
        testMinEth = int(ethAmount * (1 - slippage_tolerance / 100))

        deadline = self.chain.web3.eth.get_block("latest")["timestamp"] + 300  # 5 minutes from now

        spender_address = Web3.to_checksum_address(self.routerContract.address)
        self.chain.interact(wallet, self.contract, "approve", spender_address, tokenBid)
        receipt = self.chain.interact(wallet, self.routerContract, "swapExactTokensForTokensSupportingFeeOnTransferTokens", tokenBid, testMinEth, addrPath, wallet.address, deadline)

        print("Swap complete:")
        self.printBalance(wallet)

        return receipt

    def getPair(self, wallet):
        # Query for the pair address using the token addresses
        wethAddr = self.chain.getWETH()
        pair_address = self.chain.observe(wallet, self.factoryContract, "getPair", self.contract.address, wethAddr)
        if pair_address is None:
            print("Error: No PairCreated event found")
            sys.exit(1)

        #print(f"Liquidity Pool Address: {pair_address}")
        return pair_address

    def isEmpty(self, wallet):
        # Check if the liquidity pool has anything in it
        totalLPSupply = self.getTotalLPSupply(wallet)
        print(f"Pool Total LP Supply: {totalLPSupply}")

        totalSupply = self.getTotalSupply(wallet)
        print(f"Pool Total Supply: {totalSupply}")

        # regular tokens not lp tokens
        MINIMUM_LP_TOKEN_SUPPLY = 1000  # Default locked LP tokens
        return totalSupply <= MINIMUM_LP_TOKEN_SUPPLY

    def getToken0(self, wallet):
        return self.chain.observe(wallet, self.pairContract, "token0")

    def getToken1(self, wallet):
        return self.chain.observe(wallet, self.pairContract, "token1")

    def getReserves(self, wallet):
        return self.chain.observe(wallet, self.pairContract, "getReserves")

    def getTotalSupply(self, wallet):
        return self.chain.observe(wallet, self.contract, "totalSupply")

    def getTotalLPSupply(self, wallet):
        return self.chain.observe(wallet, self.pairContract, "totalSupply")

    def getBalance(self, wallet):
        return self.chain.observe(wallet, self.contract, "balanceOf", wallet.address)

    def getLPBalance(self, wallet):
        return self.chain.observe(wallet, self.pairContract, "balanceOf", wallet.address)

    def printBalance(self, wallet):
        #TODO also the price of the token in the pool
        totalTokenSupply = self.getTotalSupply(wallet)
        print("Total Supply: " + str(Web3.from_wei(totalTokenSupply, "ether")))

        tokenBalance = self.getBalance(wallet)
        print("Token Balance: " + str(Web3.from_wei(tokenBalance, "ether")))
        print("Percent Supply: " + str(tokenBalance / totalTokenSupply * 100) + "%")

        print("---")

        if self.isEmpty(wallet):
            print("------")
            return

        totalLPSupply = self.getTotalLPSupply(wallet)
        print("Total Supply: " + str(Web3.from_wei(totalLPSupply, "ether")))

        lpBalance = self.getLPBalance(wallet)
        print("LP Balance: " + str(Web3.from_wei(lpBalance, "ether")))
        print("Percent Supply: " + str(lpBalance / totalLPSupply * 100) + "%")

        print("------")

# Test
#pool = Pool("BASE", newContractAddr)
