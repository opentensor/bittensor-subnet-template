import unittest
import pytest
import asyncio
import random
import time

#from conversationgenome.ConversationDatabase import ConversationDatabase
#from conversationgenome.MinerLib import MinerLib
#from conversationgenome.ValidatorLib import ValidatorLib

class c:
    dotenv = {}

    @staticmethod
    def get(obj, path):
        return Utils.get(c.dotenv, path)



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
    def reserveConversation(self, hotkey):
        # Call Convo server and get a conversation
        convo = {"guid":"c1234", "exchanges":[1,2,3,4]}
        return convo

class ConvoLib:
    def getConversation(self, hotkey):
        api = ApiLib()
        convo = api.reserveConversation(hotkey)
        return convo

    async def getConvoPromptTemplate(self):
        return "Parse this"




class ForwardLib:
    def getConvo(self, hotkey):
        cl = ConvoLib()
        convo = cl.getConversation(hotkey)
        return convo


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

    async def doMining(self, convo):
        waitSec = random.randint(0, 5)
        print("Mine result: %ds" % (waitSec))
        await asyncio.sleep(waitSec)
        return 7

    async def sendToMiners(self, convo):
        print("Send to miners")
        miners = [1, 2, 3]
        results = []
        tasks = [asyncio.create_task(self.doMining(miner)) for miner in miners]
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

class MinerLib:
    def mine(self):
        print("Mining...")

    def get_conversation_tags(self, convo):
        tags = {}
        return tags


class MockBt:
    def getUids(self, num=10):
        uids = []
        for i in range(num):
            uids.append(random.randint(1000, 9999))
        return uids

class TemplateCgTestMinerLib(): #unittest.TestCase):
    verbose = True
    hotkey = "hk12233"

    def setUp(self):
        self.CD = ConvoLib()

    def tearDown(self):
        self.CD = None

    def test_run_tag(self):
        if self.verbose:
            print("Tag: ")
        assert 1 == 1

    def test_run_eval(self):
        if self.verbose:
            print("Tag: ")
        assert 1 == 1

    def test_get_convo(self):
        if self.verbose:
            print("Test Convo")
        convo = self.CD.getConversation(self.hotkey)
        assert True #len(convo['exchanges']) == 3

    def test_tags_from_convo(self):
        if self.verbose:
            print("Test Convo")
        convo = self.CD.getConversation()
        ml = MinerLib()
        tags = ml.get_conversation_tags(convo)
        assert len(tags) > 1

    def test_tags_from_convo(self):
        if self.verbose:
            print("Test Tags")
        convo = self.CD.getConversation(self.hotkey)
        ml = MinerLib()
        tags = ml.get_conversation_tags(convo)
        vl = ValidatorLib()
        result = vl.validate_tags(tags)
        assert result == True

@pytest.mark.asyncio
async def test_start():
    fl = ForwardLib()
    vl = ValidatorLib()
    hotkey = "a123"
    fullConvo = fl.getConvo(hotkey)
    print("fullConvo", fullConvo)
    fullConvoMetaData = await vl.generateFullConvoMetaData(fullConvo)
    participantProfiles = Utils.get(fullConvoMetaData, "participantProfiles", [])
    semanticTags = Utils.get(fullConvoMetaData, "semanticTags", [])

    assert len(participantProfiles) > 1,  "Conversation requires at least 2 participants"

    minValidTags = vl.validateMinimumTags(semanticTags)
    assert minValidTags,  "Conversation didn't generate minimum valid tags"
    # Mark bad conversation in real enviroment

    minLines = c.get("convo_window", "min_lines")
    maxLines = c.get("convo_window", "max_lines")
    overlapLines = c.get("convo_window", "overlap_lines")
    #convoWindows = co.getConvoWindows(fullConvo, minLines=minLines, maxLines=maxLines, overlapLines=overlapLines)

    bt = MockBt()
    uids = bt.getUids()
    # Write convo windows into local database with full convo metadata
    rows = [1,2]
    # Loop through rows in db
    for row in rows:
        results = await vl.sendToMiners(row)
        # Send first window to 3 miners
        # Each miner returns data, write data into local db
        # TODO: Write up incomplete errors
        # If timeout happens for miner, send to another miner
        # When all miners have returned data for convo window
        # Eval data
        # Score each miner result
        # Send emission to forward



