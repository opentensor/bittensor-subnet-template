verbose = False

bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

class MinerLib:
    verbose = True

    def __init__(self):
        pass

    def get_conversation_tags(self, conversation):
        # Create mock tag generator
        tagDict = {}
        for exchange in conversation:
            question = exchange[0]
            answer = exchange[1]
            words = question.split(' ')
            words = words + answer.split(' ')
            for word in words:
                word = word.strip().lower()
                if not word in tagDict:
                    tagDict[word] = 0
                tagDict[word] += 1
        tags = tagDict.keys()
        if self.verbose:
            print("Found %d tags" % (len(tags)))
        return tags



        return self.convo
