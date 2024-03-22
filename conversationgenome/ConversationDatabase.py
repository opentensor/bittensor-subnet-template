verbose = False

bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

class ConversationDatabase:
    verbose = True

    def __init__(self):
        self.convo = [
            ["What did you buy yesterday?", "A Balenciaga dress. The best. Is that what you asked?"],
            ["Yeah. And shoes?", "Louboutins. I love them, but they hurt my feet. Ow! You know."],
            ["Do you wear them around the house?", "No way! They're expensive, y'know?"],
        ]

    def getConversation(self):
        return self.convo
