import unittest
import pytest
import asyncio

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

    def getConvoPromptTemplate(self):
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
        pt = cl.getConvoPromptTemplate()
        llml =  LlmApi()
        data = await llml.callFunction("convoParse", convo)

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


class TemplateCgTestMinerLib(): #unittest.TestCase):
    verbose = True
    hotkey = "hk12233"

    def setUp(self):
        self.CD = ConvoLib()

    def tearDown(self):
        self.CD = None

    # Convo
    def start(self):
        fl = ForwardLib()
        hotkey = "a123"
        fullConvo = fl.getConvo(hotkey)

        vl = ValidatorLib()
        fullConvoMetaData = vl.generateFullConvoMetaData(convo)
        participantProfiles = Utils.get(fullConvoMetaData, "participantProfiles", [])
        #semanticTags = Utils.get(fullConvoMetaData, "semanticTags", [])

        #assert(len(participantProfiles) > 1,  "Conversation requires at least 2 participants")

        minValidTags = self.validateMinimumTags(semanticTags)
        #assert(minValidTags,  "Conversation didn't generate minimum valid tags")
        # Mark bad conversation in real enviroment

        minLines = c.get("convo_window", "min_lines")
        maxLines = c.get("convo_window", "max_lines")
        overlapLines = c.get("convo_window", "overlap_lines")
        convoWindows = co.getConvoWindows(fullConvo, minLines=minLines, maxLines=maxLines, overlapLines=overlapLines)

        # Write convo windows into local database with full convo metadata
        # Loop through rows in db
            # Send first window to 3 miners
            # Each miner returns data, write data into local db
            # TODO: Write up incomplete errors
            # If timeout happens for miner, send to another miner
            # When all miners have returned data for convo window
            # Eval data
            # Score each miner result
            # Send emission to forward




    # Validator
    # Miner

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

# function to add two numbers
def add(x, y):
    return x + y

async def divide(x, y):
    return x / y

@pytest.mark.asyncio
async def test_divide():
    result = await divide(15, 5)
    assert result == 3, "Division failed: the result should be 3"

def test_add():
    print("\nTest add")
    assert add(2, 3) == 5, "Addition failed: the result should be 6"

@pytest.mark.asyncio
async def test_start():
    fl = ForwardLib()
    hotkey = "a123"
    fullConvo = fl.getConvo(hotkey)
    print("fullConvo", fullConvo)
    vl = ValidatorLib()
    fullConvoMetaData = await vl.generateFullConvoMetaData(fullConvo)
    participantProfiles = Utils.get(fullConvoMetaData, "participantProfiles", [])
    semanticTags = Utils.get(fullConvoMetaData, "semanticTags", [])

    #assert(len(participantProfiles) > 1,  "Conversation requires at least 2 participants")

    minValidTags = vl.validateMinimumTags(semanticTags)
    #assert(minValidTags,  "Conversation didn't generate minimum valid tags")
    # Mark bad conversation in real enviroment

    minLines = c.get("convo_window", "min_lines")
    maxLines = c.get("convo_window", "max_lines")
    overlapLines = c.get("convo_window", "overlap_lines")
    #convoWindows = co.getConvoWindows(fullConvo, minLines=minLines, maxLines=maxLines, overlapLines=overlapLines)

    # Write convo windows into local database with full convo metadata
    # Loop through rows in db
        # Send first window to 3 miners
        # Each miner returns data, write data into local db
        # TODO: Write up incomplete errors
        # If timeout happens for miner, send to another miner
        # When all miners have returned data for convo window
        # Eval data
        # Score each miner result
        # Send emission to forward



