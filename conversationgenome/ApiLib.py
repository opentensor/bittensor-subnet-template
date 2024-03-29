import json
import random

from conversationgenome.Utils import Utils


class ApiLib:
    async def reserveConversation(self, hotkey, dryrun=False):
        # Call Convo server and reserve a conversation
        if dryrun:
            path = 'facebook-chat-data.json'
            f = open(path)
            body = f.read()
            f.close()
            convos = json.loads(body)
            convoKeys = list(convos.keys())
            convoTotal = len(convoKeys)
            #print("convoTotal", convoTotal)
            selectedConvoKey = random.choice(convoKeys)
            selectedConvo = convos[selectedConvoKey]
            #print("selectedConvo", selectedConvo)


            convo = {
                "guid":Utils.get(selectedConvo, "guid"),
                "participants": Utils.get(selectedConvo, "participants"),
                "lines":Utils.get(selectedConvo, "lines"),
            }
        else:

            convo = {"guid":"c1234", "lines":[1,2,3,4], "participants":["Emily", "John"]}
        return convo

    async def completeConversation(self, hotkey, guid, dryrun=False):
        return True


