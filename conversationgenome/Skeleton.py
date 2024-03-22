verbose = False

bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

class Skeleton:
    def __init__(self):
        pass

    def get_skeleton(self):
        return "Skeleton"