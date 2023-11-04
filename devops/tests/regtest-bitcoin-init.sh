#!/bin/bash

bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword createwallet "wallet1"
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword createwallet "wallet2"
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword createwallet "wallet3"
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword createwallet "wallet4"

ADDRESS1=$(bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet1 getnewaddress)
ADDRESS2=$(bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet2 getnewaddress)
ADDRESS3=$(bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet3 getnewaddress)
ADDRESS4=$(bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet4 getnewaddress)

# Mine 101 blocks to address1 (50 BTC per block, but the first 100 blocks' rewards are not spendable yet)
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword generatetoaddress 101 $ADDRESS1

# Distribute rewards among addresses
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet1 sendtoaddress $ADDRESS2 10
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet1 sendtoaddress $ADDRESS3 10
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet1 sendtoaddress $ADDRESS4 10

# Mine a block to confirm the above transactions
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword generatetoaddress 1 $ADDRESS1

# Further transactions can be added below

# Example: Sending 5 BTC from Address2 to Address3
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword -rpcwallet=wallet2 sendtoaddress $ADDRESS3 5

# Mine a block to confirm the above transaction
bitcoin-cli -regtest -rpcuser=bitcoinrpc -rpcpassword=rpcpassword generatetoaddress 1 $ADDRESS1
