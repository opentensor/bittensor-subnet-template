# Create a coldkey for the owner role
btcli wallet new_coldkey --wallet.name owner

# Set up the miner's wallets
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default

# Set up the validator's wallets
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default

# Mint tokens for the owner
btcli wallet faucet --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Balance: τ0.000000000 ➡ τ100.000000000
# Mint tokens to your validator.
btcli wallet faucet --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Balance: τ0.000000000 ➡ τ100.000000000

btcli subnet create --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946 
>> Your balance is: τ200.000000000
>> Do you want to register a subnet for τ100.000000000? [y/n]: 
>> Enter password to unlock key: [YOUR_PASSWORD]
>> ✅ Registered subnetwork with netuid: 1


---------------------------------
owner:
btcli w regen_coldkey --mnemonic wait genre spend city face exhaust cycle bubble feature zero torch harsh

miner:
btcli w regen_coldkey --mnemonic supreme kitten blue type achieve rhythm inch student arrest vocal awake erase

miner hotkey:
btcli w regen_hotkey --mnemonic absorb huge switch clinic later cable horror helmet giant swim large possible

validator:
btcli w regen_coldkey --mnemonic gun grace protect start ladder mansion emerge brave glory core toward venture

validator hotkey:
btcli w regen_hotkey --mnemonic forward immune dinner fatal uphold index engage forward hen project taxi skirt

Wallets
├──
│   miner (5ECy3yv3UJhvWkZ1emZiBxdHPrvmRdGEgWTXbBY9ZiAZkXz5)
│   └── default (5E7A6HT9amCey47z8u7wDcS5UuWGfWtgoyCxLrrq4hK5oJGR)
├──
│   owner (5EbxqtFMJQoYkoCzUYShWM6ergGkK8HhsRDnZq2HeoS7F8Xq)
└──
    validator (5CFcVc8WeHZn482QBiZpjPz7dzDw25q4gsM3pstG7WV3Q8pz)
    └── default (5DjnVHSU4GtXiyWtQd65StRj22TLF3K4pA7rc3FPTduHt4fY)

