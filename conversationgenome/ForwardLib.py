verbose = False

bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

class ForwardLib:
    verbose = True

    def __init__(self):
        pass

    def get_embedding(self):
        if self.verbose:
            print("Get embedding"))

