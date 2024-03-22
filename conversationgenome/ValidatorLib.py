verbose = False

bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

class ValidatorLib:
    verbose = True

    def __init__(self):
        pass

    def validate_tags(self, tags):
        if self.verbose:
            print("Validating %d tags" % (len(tags)))
        if len(tags) > 10:
            return True
        else:
            return False

