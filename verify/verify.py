from substrateinterface import Keypair
from binascii import unhexlify


def main(args):
    file_data = open(args.file).read()
    file_split = file_data.split("\n\t")

    address_line = file_split[1]
    address_prefix = "Signed by: "
    if address_line.startswith(address_prefix):
        address = address_line[len(address_prefix) :]
    else:
        address = address_line

    keypair = Keypair(ss58_address=address, ss58_format=42)

    message = file_split[0]

    signature_line = file_split[2]
    signature_prefix = "Signature: "
    if signature_line.startswith(signature_prefix):
        signature = signature_line[len(signature_prefix) :]
    else:
        signature = signature_line

    real_signature = unhexlify(signature.encode())

    if not keypair.verify(data=message, signature=real_signature):
        raise ValueError(f"Invalid signature for address={address}")
    else:
        print(f"Signature verified, signed by {address}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify a signature")
    parser.add_argument("--file", help="The file containing the message and signature")
    args = parser.parse_args()
    main(args)
