from Crypto.Hash import SHA256, RIPEMD160
import base58


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


# Example usage
# pubkeys = ['04cc71eb30d653c0c3163990c47b976f3fb3f37cccdcbedb169a1dfef58bbfbfaff7d8a473e7e2e6d317b87bafe8bde97e3cf8f065dec022b51d11fcdd0d348ac4', '0461cbdcc5409fb4b4d42b51d33381354d80e550078cb532a34bfa2fcfdeb7d76519aecc62770f5b0e4ef8551946d8a540911abe3e7854a26f39f58b25c15342af']
# m = 2  # Number of required signatures

# redeem_script = construct_redeem_script(pubkeys, m)
# hashed_script = hash_redeem_script(redeem_script)
# p2sh_address = create_p2sh_address(hashed_script)

# print(p2sh_address)
