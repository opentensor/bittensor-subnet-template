import pytest
import asyncio
import random
import json
import copy
import math
import uuid
import time

spacy = None
Matcher = None
try:
    import spacy
    from spacy.matcher import Matcher
except:
    print("Please install spacy to run locally")
    # en_core_web_sm model vectors = 96 dimensions.
    # en_core_web_md and en_core_web_lg = 300 dimensions

#from conversationgenome.ConversationDatabase import ConversationDatabase
#from conversationgenome.MinerLib import MinerLib
from conversationgenome.ValidatorLib import ValidatorLib


bt = MockBt()


proto = {
    "interests_of_q": [],
    "hobbies_of_q": [],
    "personality_traits_of_q": [],
    "interests_of_a": [],
    "hobbies_of_a": [],
    "personality_traits_of_a": [],
}

@pytest.mark.asyncio
async def test_miner_no_convo():
    ml = MinerLib()
    convo = []
    uid = 1111
    result = await ml.doMining(convo, uid, dryrun=True)
    assert result["uid"] == uid, "User ID didn't match"

def test_utils_split_overlap_array():
    testArray = [1,2,3,4,5,6,7,8,9,10]
    result = Utils.split_overlap_array(testArray, size=5, overlap=2)
    assert len(result) == 3, "Length of split didn't match"



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
    assert True #len(convo['lines']) == 3

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
    vl = ValidatorLib()
    await vl.requestConvo()



"""
TODO: Error happened once. Debug.
tests_ap\test_miner_lib.py:489:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
tests_ap\test_miner_lib.py:270: in requestConvo
    await self.sendWindowsToMiners(fullConvoTags, convoWindows)
tests_ap\test_miner_lib.py:376: in sendWindowsToMiners
    await self.calculate_emission_rewards(minerResults, 'score')
tests_ap\test_miner_lib.py:242: in calculate_emission_rewards
    pdf_value = normal_pdf(score, mean, stdev)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

x = 0.5805194805194805, mean = 0.5805194805194805, stdev = 0.0

    def normal_pdf(x, mean, stdev):
>       return math.exp(-(x - mean) ** 2 / (2 * stdev ** 2)) / (stdev * math.sqrt(2 * math.pi))
E       ZeroDivisionError: float division by zero

tests_ap\test_miner_lib.py:237: ZeroDivisionError
========================================================================= short test summary info =========================================================================
FAILED tests_ap/test_miner_lib.py::test_full - ZeroDivisionError: float division by zero
======================================================================= 1 failed, 5 passed in 6.05s =======================================================================

"""

