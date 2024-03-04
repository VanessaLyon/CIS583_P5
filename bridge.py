from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
import json
import sys
from pathlib import Path

from eth_account import Account
import random
from hexbytes import HexBytes

source_chain_api = 'https://api.avax-test.network/ext/bc/C/rpc'
destination_chain_api = 'https://data-seed-prebsc-1-s1.binance.org:8545/'
contract_info_path = "contract_info.json"
source_chain_name = 'avax'
destination_chain_name = 'bsc'

def connectTo(chain):
    w3 = None  # Initialize w3 to None to ensure it's always defined
	
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
	    
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if w3 is None:
        print(f"Unsupported chain: {chain}")
        # Handle the error appropriately here
        return None

    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info_path)
    try:
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]

def blockScanner_source(chain,start_block,end_block,source_contract,destination_contract):
    """
    chain - string (Either 'bsc' or 'avax')
    start_block - integer first block to scan
    end_block - integer last block to scan
    contract_address - the address of the deployed contract

	This function reads "Deposit" events from the specified contract, 
	and writes information about the events to the file "deposit_logs.csv"
    """
    w3 = None
    api_url = None
	
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    #My details
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3.eth.account.from_key(sk)
    private_key = acct._private_key


    arg_filter = {}

    # Correctly calculate start_block and end_block
    latest = w3.eth.get_block_number()


    if start_block == latest:
        start_block = w3.eth.get_block_number()
    if end_block == latest:
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print( f"Error end_block < start_block!" )
        print( f"end_block = {end_block}" )
        print( f"start_block = {start_block}" )

    if start_block == end_block:
        print( f"Scanning block {start_block} on {chain}" )
    else:
        print( f"Scanning blocks {start_block} - {end_block} on {chain}" )

    if end_block - start_block < 30:
        event_filter = source_contract.events.Deposit.create_filter(fromBlock=start_block,toBlock=end_block,argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        
        for event in events:
            token = event['args']['token']
            recipient = event['args']['recipient']
            amount = event['args']['amount']
            #tx_hash = event.transactionHash.hex()
            #address = contract_address
            print(f"Deposit event found: token={token}, recipient={recipient}, amount={amount}")

            # Building the transaction with appropriate parameters
            txn = destination_contract.functions.wrap(token, recipient, amount).build_transaction({
                'from': acct.address,
                'nonce': w3.eth.get_transaction_count(acct.address),
                'gas': 2000000,  
                'gasPrice': w3.eth.gas_price
            })

            # Signing the transaction with your private key
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)

            # Sending the signed transaction
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Wrap transaction sent: {txn_hash.hex()}")

    else:
        for block_num in range(start_block,end_block+1):
            event_filter = source_contract.events.Deposit.create_filter(fromBlock=block_num,toBlock=block_num,argument_filters=arg_filter)
            events = event_filter.get_all_entries()
            
            for event in events:
                token = event['args']['token']
                recipient = event['args']['recipient']
                amount = event['args']['amount']
                #tx_hash = event.transactionHash.hex()
                #address = contract_address
                print(f"Deposit event found: token={token}, recipient={recipient}, amount={amount}")

	    # Building the transaction with appropriate parameters
            txn = destination_contract.functions.wrap(token, recipient, amount).build_transaction({
                'from': acct.address,
                'nonce': w3.eth.get_transaction_count(acct.address),
                'gas': 2000000,  
                'gasPrice': w3.eth.gas_price
            })

            # Signing the transaction with your private key
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)

            # Sending the signed transaction
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Wrap transaction sent: {txn_hash.hex()}")


def blockScanner_destination(chain,start_block,end_block,source_contract,destination_contract):
    """
    chain - string (Either 'bsc' or 'avax')
    start_block - integer first block to scan
    end_block - integer last block to scan
    contract_address - the address of the deployed contract

	This function reads "Deposit" events from the specified contract, 
	and writes information about the events to the file "deposit_logs.csv"
    """
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    #My details
    w3_source = Web3(Web3.HTTPProvider(f"https://api.avax-test.network/ext/bc/C/rpc"))
    sk = "b6b07402191ac2a961ce645d303b1b5e1a6c73afdf8b953d18ff1ab1cf61cbd2"
    acct = w3_source.eth.account.from_key(sk)
    private_key = acct._private_key


    arg_filter = {}

    # Correctly calculate start_block and end_block
    latest = w3.eth.get_block_number()


    if start_block == latest:
        start_block = w3.eth.get_block_number()
    if end_block == latest:
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print( f"Error end_block < start_block!" )
        print( f"end_block = {end_block}" )
        print( f"start_block = {start_block}" )

    if start_block == end_block:
        print( f"Scanning block {start_block} on {chain}" )
    else:
        print( f"Scanning blocks {start_block} - {end_block} on {chain}" )

    if end_block - start_block < 30:

        # Listen for "Unwrap" events on the destination contract
        unwrap_event_filter = destination_contract.events.Unwrap.create_filter(fromBlock=start_block, toBlock=end_block)
        unwrap_events = unwrap_event_filter.get_all_entries()

        for event in unwrap_events:
          # Extract necessary information from the event
          wrapped_token, recipient, amount = event['args'].values()
          
          # Prepare the transaction for calling the `withdraw` function
          txn_dict = source_contract.functions.withdraw(wrapped_token, recipient, amount).build_transaction({
            'from': w3_source.eth.acct.address,  
            'nonce': w3_source.eth.get_transaction_count(w3_source.eth.acct.address),
            'gas': 2000000,  
            'gasPrice': w3_source.eth.gas_price  
          })

          # Sign the transaction with the private key of the account
          signed_txn = w3_source.eth.account.sign_transaction(txn_dict, private_key=private_key)

          # Send the signed transaction
          txn_receipt = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

          # Wait for the transaction to be mined and get the transaction receipt
          txn_receipt = w3_source.eth.wait_for_transaction_receipt(txn_receipt)

          print(f"Withdraw transaction successful with tx hash: {txn_receipt.transactionHash.hex()}")
          
    else:
        for block_num in range(start_block,end_block+1):
            # Listen for "Unwrap" events on the destination contract
            unwrap_event_filter = destination_contract.events.Unwrap.create_filter(fromBlock=block_num, toBlock=block_num)
            unwrap_events = unwrap_event_filter.get_all_entries()

            for event in unwrap_events:
                # Extract necessary information from the event
                wrapped_token, recipient, amount = event['args'].values()
        
                #Call the withdraw function on the source contract
          
                # Prepare the transaction for calling the `withdraw` function
                txn_dict = source_contract.functions.withdraw(wrapped_token, recipient, amount).build_transaction({
                    'from': w3_source.eth.acct.address,  
                    'nonce': w3_source.eth.get_transaction_count(w3_source.eth.acct.address),
                    'gas': 2000000,  
                    'gasPrice': w3_source.eth.gas_price  
                })

                # Sign the transaction with the private key of the account
                signed_txn = w3_source.eth.account.sign_transaction(txn_dict, private_key=private_key)

                # Send the signed transaction
                txn_receipt = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

                # Wait for the transaction to be mined and get the transaction receipt
                txn_receipt = w3_source.eth.wait_for_transaction_receipt(txn_receipt)

                print(f"Withdraw transaction successful with tx hash: {txn_receipt.transactionHash.hex()}")
          




def scanBlocks(chain):
    """
    chain - (string) should be either "source" or "destination"
    Scan the last 5 blocks of the source and destination chains
    Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
    When Deposit events are found on the source chain, call the 'wrap' function on the destination chain
    When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """
    if chain == 'source':
        w3 = connectTo(source_chain_name)
        chain_api = source_chain_api
    elif chain == 'destination':
        w3 = connectTo(destination_chain_name)
        chain_api = destination_chain_api
    else:
        print(f"Invalid chain: {chain}")
        return

    if w3 is None:
        print(f"Failed to connect to the {chain} chain.")
        return

    # Load contract information
    source_contract_info = getContractInfo('source')
    destination_contract_info = getContractInfo('destination')

    # Create contract instances
    source_contract = w3.eth.contract(
        address=source_contract_info['address'],
        abi=source_contract_info['abi']
    )
    destination_contract = w3.eth.contract(
        address=destination_contract_info['address'],
        abi=destination_contract_info['abi']
    )

    # Correctly calculate start_block and end_block
    current_block = w3.eth.block_number
	
    start_block = max(1, current_block - 100)  # Ensure start_block is not negative
    end_block = current_block  # Use the current block number as end_block

    if chain == 'source':
        blockScanner_source(source_chain_name, start_block, end_block, source_contract, destination_contract)
    elif chain == 'destination':
        blockScanner_destination(destination_chain_name, start_block, end_block, source_contract, destination_contract)
