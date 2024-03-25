import pytest
import asyncio
import random
import time

#from conversationgenome.ConversationDatabase import ConversationDatabase
#from conversationgenome.MinerLib import MinerLib
#from conversationgenome.ValidatorLib import ValidatorLib

class MockBt:
    def getUids(self, num=10):
        uids = []
        for i in range(num):
            uids.append(random.randint(1000, 9999))
        return uids



class c:
    dotenv = {}

    @staticmethod
    def get(obj, path, default):
        return Utils.get(c.dotenv, path, default)



class Utils:
    @staticmethod
    def get(obj, path, default=None):
        out = default
        try:
            out = obj[path]
        except:
            pass
        return out

class LlmApi:
    async def callFunction(self, functionName, parameters):
        pass

class ApiLib:
    def reserveConversation(self, hotkey, dryrun=False):
        # Call Convo server and reserve a conversation
        if dryrun:
            convo = {"guid":"c1234", "exchanges":[1,2,3,4]}
        else:
            convo = {"guid":"c1234", "exchanges":[1,2,3,4]}
        return convo

class ConvoLib:
    async def getConversation(self, hotkey, dryrun=False):
        api = ApiLib()
        convo = api.reserveConversation(hotkey, dryrun=dryrun)
        return convo

    async def getConvoPromptTemplate(self):
        return "Parse this"


class ForwardLib:
    async def getConvo(self, hotkey):
        cl = ConvoLib()
        convo = await cl.getConversation(hotkey, dryrun=True)
        return convo

    def getConvoWindows(self, fullConvo):
        minExchanges = c.get("convo_window", "min_lines", 5)
        maxExchanges = c.get("convo_window", "max_lines", 10)
        overlapExchanges = c.get("convo_window", "overlap_lines", 2)
        # Write convo windows into local database with full convo metadata
        windows = [1,2]
        return windows


    async def sendConvo(self):
        vl = ValidatorLib()
        hotkey = "a123"
        fullConvo = await self.getConvo(hotkey)
        #print("fullConvo", fullConvo)
        fullConvoMetaData = await vl.generateFullConvoMetaData(fullConvo)
        participantProfiles = Utils.get(fullConvoMetaData, "participantProfiles", [])
        semanticTags = Utils.get(fullConvoMetaData, "semanticTags", [])
        minValidTags = vl.validateMinimumTags(semanticTags)
        convoWindows = self.getConvoWindows(fullConvo)
        await vl.handleWindows(convoWindows)



class ValidatorLib:
    async def generateFullConvoMetaData(self, convo):
        cl = ConvoLib()
        # Get prompt template
        pt = await cl.getConvoPromptTemplate()
        llml =  LlmApi()
        data = await llml.callFunction("convoParse", convo)
        data = {
            "participantProfiles": [1,2,3],
            "tags": {},
        }
        return data

    async def sendToMiners(self, convoWindow, minerUids):
        print("Send to miners", minerUids)
        results = []
        ml = MinerLib()
        tasks = [asyncio.create_task(ml.doMining(convoWindow, minerUid)) for minerUid in minerUids]
        await asyncio.wait(tasks)
        for task in tasks:
            results.append(task.result())
        return results

    def score(self):
        pass

    def validate_tags(self, tags):
        print("validate_tags")
        return True

    def validateMinimumTags(self, tags):
        return True

    async def handleWindows(self, windows):
        uids = bt.getUids()
        miners = uids[0:3]

        # Loop through rows in db
        for window in windows:
            # Send first window to 3 miners
            results = await self.sendToMiners(window, miners)
            # Each miner returns data, write data into local db
            print("Miner results", results)
            # TODO: Write up incomplete errors, such as if timeout happens for miner, send to another miner
            # When all miners have returned data for convo window
            # Eval data
            convoTags = ["realistic", "business-minded", "conciliatory", "responsive", "caring", "understanding"]
            scores = {}
            # Score each miner result
            for result in results:
                uid = result['uid']
                tags = result['tags']
                tag = None
                if len(tags) > 0:
                    tag = tags[0]
                if tag in convoTags:
                    print("FOUND!", tag)
                    if not uid in scores:
                        scores[uid] = 0
                    scores[uid] += 3
            # Send emission to forward
            print("EMISSIONS", scores)


class MinerLib:
    async def doMining(self, convo, minerUid, dryrun=False):
        exampleTags = ["realistic", "business-minded", "conciliatory", "responsive", "caring", "understanding", "apologetic", "affectionate", "optimistic", "family-oriented"]
        waitSec = random.randint(0, 3)
        out = {"uid":minerUid, "tags":[], "profiles":[], "convoChecksum":11}
        print("Mine result: %ds" % (waitSec))
        if dryrun:
            await asyncio.sleep(waitSec)
            out["tags"].append(random.choice(exampleTags))
        else:
            # TODO: Make this actually tag content
            out["tags"].append(random.choice(exampleTags))
        return out


    def get_conversation_tags(self, convo):
        tags = {}
        return tags



bt = MockBt()

@pytest.mark.asyncio
async def test_miner_no_convo():
    ml = MinerLib()
    convo = []
    uid = 1111
    result = await ml.doMining(convo, uid, dryrun=True)
    assert result["uid"] == uid, "User ID didn't match"

@pytest.mark.asyncio
async def test_validator_no_convo():
    ml = MinerLib()
    convo = []
    uid = 1111
    result = await ml.doMining(convo, uid, dryrun=True)
    assert result["uid"] == uid, "User ID didn't match"
    #assert len(participantProfiles) > 1,  "Conversation requires at least 2 participants"

    #assert minValidTags,  "Conversation didn't generate minimum valid tags"
    # TODO: Mark bad conversation in real enviroment

@pytest.mark.asyncio
async def test_get_convo():
    hotkey = "hk12233"
    cl = ConvoLib()

    convo = await cl.getConversation(hotkey)
    assert True #len(convo['exchanges']) == 3

@pytest.mark.asyncio
async def test_tags_from_convo():
    hotkey = "hk12233"
    cl = ConvoLib()
    convo = await cl.getConversation()
    ml = MinerLib()
    tags = ml.get_conversation_tags(convo)
    assert len(tags) > 1

@pytest.mark.asyncio
async def test_tags_from_convo():
    hotkey = "hk12233"
    cl = ConvoLib()
    convo = await cl.getConversation(hotkey)
    ml = MinerLib()
    tags = ml.get_conversation_tags(convo)
    vl = ValidatorLib()
    result = vl.validate_tags(tags)
    assert result == True


@pytest.mark.asyncio
async def test_full():
    fl = ForwardLib()
    await fl.sendConvo()





