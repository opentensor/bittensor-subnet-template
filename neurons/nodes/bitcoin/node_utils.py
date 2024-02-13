from Crypto.Hash import SHA256, RIPEMD160
import base58


def pubkey_to_address(pubkey: str) -> str:
    # Step 1: SHA-256 hashing on the public key
    sha256_result = SHA256.new(bytes.fromhex(pubkey)).digest()

    # Step 2: RIPEMD-160 hashing on the result of SHA-256 using PyCryptodome
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_result)
    ripemd160_result = ripemd160.digest()

    # Step 3: Add version byte (0x00 for Mainnet)
    versioned_payload = b"\x00" + ripemd160_result

    # Step 4 and 5: Calculate checksum and append to the payload
    checksum = SHA256.new(SHA256.new(versioned_payload).digest()).digest()[:4]
    binary_address = versioned_payload + checksum

    # Step 6: Encode the binary address in Base58
    bitcoin_address = base58.b58encode(binary_address).decode("utf-8")
    return bitcoin_address


def construct_redeem_script(pubkeys, m):
    n = len(pubkeys)
    script = f"{m} " + " ".join(pubkeys) + f" {n} OP_CHECKMULTISIG"
    return script.encode("utf-8")


def hash_redeem_script(redeem_script):
    sha256 = SHA256.new(redeem_script).digest()
    ripemd160 = RIPEMD160.new(sha256).digest()
    return ripemd160


def create_p2sh_address(hashed_script, mainnet=True):
    version_byte = b"\x05" if mainnet else b"\xc4"
    payload = version_byte + hashed_script
    checksum = SHA256.new(SHA256.new(payload).digest()).digest()[:4]
    return base58.b58encode(payload + checksum).decode()


def get_tx_out_hash_table_sub_keys():
    sub_keys = []
    hex_chars = "0123456789abcdef"

    # initialize hash_table with 4096 entries (3 hex digits)
    for i in range(16):
        for j in range(16):
            for k in range(16):
                sub_keys.append(hex_chars[i] + hex_chars[j] + hex_chars[k])
    
    return sub_keys


def initialize_tx_out_hash_table():
    hash_table = {}
    sub_keys = get_tx_out_hash_table_sub_keys()
    for sub_key in sub_keys:
        hash_table[sub_key] = {}
    return hash_table


def process_in_memory_txn_for_indexing(tx, _bitcoin_node):
    in_amount_by_address = {} # input amounts by address in satoshi
    out_amount_by_address = {} # output amounts by address in satoshi
    
    for vin in tx.vins:
        if vin.tx_id == 0:
            continue
        address, amount = _bitcoin_node.get_address_and_amount_by_txn_id_and_vout_id(vin.tx_id, str(vin.vout_id))
        if address in in_amount_by_address:
            in_amount_by_address[address] += amount
        else:
            in_amount_by_address[address] = amount

    for vout in tx.vouts:
        amount = vout.value_satoshi
        address = vout.address
        if vout.address in out_amount_by_address:
            out_amount_by_address[address] += amount
        else:
            out_amount_by_address[address] = amount
    
    for address in in_amount_by_address.keys():
        if in_amount_by_address[address] == 0:
            continue
        if address in out_amount_by_address and out_amount_by_address[address] != 0:
            if in_amount_by_address[address] > out_amount_by_address[address]:
                in_amount_by_address[address] -= out_amount_by_address[address]
                out_amount_by_address[address] = 0
            elif in_amount_by_address[address] < out_amount_by_address[address]:
                out_amount_by_address[address] -= in_amount_by_address[address]
                in_amount_by_address[address] = 0
            else:
                in_amount_by_address[address] = 0
                out_amount_by_address[address] = 0
    
    input_addresses = [address for address in in_amount_by_address.keys() if in_amount_by_address[address] != 0]
    output_addresses = [address for address in out_amount_by_address.keys() if out_amount_by_address[address] != 0]
                
    in_total_amount = sum([in_amount_by_address[address] for address in input_addresses])
    out_total_amount = sum([out_amount_by_address[address] for address in output_addresses])
    
    return in_amount_by_address, out_amount_by_address, input_addresses, output_addresses, in_total_amount, out_total_amount
