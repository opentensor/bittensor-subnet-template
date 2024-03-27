verbose = False

import copy
import random
import asyncio
from conversationgenome.ConfigLib import c
from conversationgenome.MockBt import MockBt


from conversationgenome.Utils import Utils


bt = None
try:
    import bittensor as bt
except:
    if verbose:
        print("bittensor not installed")

from conversationgenome.LlmLib import LlmLib


class MinerLib:
    verbose = False

    async def doMining(self, convoWindow, minerUid, dryrun=True):
        #print("MINERCONVO", convoWindow, minerUid)
        out = {"uid":minerUid, "tags":[], "profiles":[], "convoChecksum":11}

        #print("Mine result: %ds" % (waitSec))
        if dryrun:
            llml = LlmLib()
            exampleSentences = [
                "Who's there?",
                "Nay, answer me. Stand and unfold yourself.",
                "Long live the King!",
                "Barnardo?",
                "He.",
                "You come most carefully upon your hour.",
                "Tis now struck twelve. Get thee to bed, Francisco.",
                "For this relief much thanks. Tis bitter cold, And I am sick at heart.",
                "Have you had quiet guard?",
                "Not a mouse stirring.",
                "Well, good night. If you do meet Horatio and Marcellus, The rivals of my watch, bid them make haste.",
                "I think I hear them. Stand, ho! Who is there?",
                "Friends to this ground.",
                "And liegemen to the Dane.",
            ]
            lines = copy.deepcopy(convoWindow)
            lines.append(random.choice(exampleSentences))
            lines.append(random.choice(exampleSentences))
            matches_dict = await llml.conversation_to_tags({"lines":lines})
            tags = list(matches_dict.keys())
            out["tags"] = tags
            out["vectors"] = matches_dict
            #waitSec = random.randint(0, 3)
            #await asyncio.sleep(waitSec)
        else:
            # TODO: Make this actually tag content
            exampleTags = ["realistic", "business-minded", "conciliatory", "responsive", "caring", "understanding", "apologetic", "affectionate", "optimistic", "family-oriented"]
            out["tags"].append(random.choice(exampleTags))
        return out


    def get_conversation_tags(self, convo):
        tags = {}
        return tags

