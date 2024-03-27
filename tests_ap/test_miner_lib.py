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
#from conversationgenome.ValidatorLib import ValidatorLib

class MockBt:
    def getUids(self, num=10, useFullGuids=False):
        uids = []
        for i in range(num):
            # useGuids is more realistic, but harder to read in testing
            if useFullGuids:
                uids.append(Utils.guid())
            else:
                uids.append(random.randint(1000, 9999))

        return uids

bt = MockBt()


proto = {
    "interests_of_q": [],
    "hobbies_of_q": [],
    "personality_traits_of_q": [],
    "interests_of_a": [],
    "hobbies_of_a": [],
    "personality_traits_of_a": [],
}


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

    @staticmethod
    def compare_arrays(arr1, arr2):
        result_dict = {}

        set1 = set(arr1)
        set2 = set(arr2)

        result_dict["both"] = list(set1.intersection(set2))
        result_dict["unique_1"] = list(set1.difference(set2))
        result_dict["unique_2"] = list(set2.difference(set1))

        return result_dict

    @staticmethod
    def pluck(dicts, key):
        values = []
        for dictionary in dicts:
            if key in dictionary:
                values.append(dictionary[key])
        return values

    @staticmethod
    def guid():
        current_time = int(round(time.time() * 1000))
        guid = uuid.uuid1(node=current_time)
        guid_int = int(guid.int)
        return guid_int

    @staticmethod
    def split_overlap_array(array, size=10, overlap=2):
        result = []
        lenArray = len(array)
        num_splits = lenArray//(size-overlap) + 1

        for i in range(num_splits):
            start = i*(size-overlap)
            end = start + size
            window = array[start:end]
            #print("Start/end/elements", start, end, window)
            result.append(array[start:end])
            if end >= lenArray:
                break
        return result


class LlmApi:
    nlp = None
    async def callFunction(self, functionName, parameters):
        pass

    async def conversation_to_tags(self,  convo, dryrun=True):
        # Get prompt template
        #pt = await cl.getConvoPromptTemplate()
        #llml =  LlmApi()
        #data = await llml.callFunction("convoParse", convo)
        if dryrun:
            matches_dict = await self.simple_text_to_tags(json.dumps(convo['exchanges']))
        else:
            print("Send conversation to the LLM")
        return matches_dict



    async def simple_text_to_tags(self, body):
        nlp = self.nlp
        if not nlp:
            nlp = spacy.load("en_core_web_sm")
            self.nlp = nlp

        # Define patterns
        adj_noun_pattern = [{"POS": "ADJ"}, {"POS": "NOUN"}]
        pronoun_pattern = [{"POS": "PRON"}]
        unique_word_pattern = [{"POS": {"IN": ["NOUN", "VERB", "ADJ"]}, "IS_STOP": False}]

        # Initialize the Matcher with the shared vocabulary
        matcher = Matcher(nlp.vocab)
        matcher.add("ADJ_NOUN_PATTERN", [adj_noun_pattern])
        matcher.add("PRONOUN_PATTERN", [pronoun_pattern])
        matcher.add("UNIQUE_WORD_PATTERN", [unique_word_pattern])

        doc = nlp( body )
        #print("DOC", doc)
        matches = matcher(doc)
        matches_dict = {}
        for match_id, start, end in matches:
            span = doc[start:end]
            #matchPhrase = span.text
            matchPhrase = span.lemma_
            if len(matchPhrase) > 5:
                #print(f"Original: {span.text}, Lemma: {span.lemma_} Vectors: {span.vector.tolist()}")
                if not matchPhrase in matches_dict:
                    matches_dict[matchPhrase] = {"tag":matchPhrase, "count":0, "vectors":span.vector.tolist()}
                matches_dict[matchPhrase]['count'] += 1

        return matches_dict


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
            #print("convoTotal", selectedConvo)
            participants = [
                "Emily is a bubbly chatter who loves to talk about fashion and beauty. She enjoys trying out new makeup looks and sharing her tips and tricks with others. She is always up for a good laugh and her positive energy is contagious.",
                "John is a sports enthusiast who can always be found discussing the latest game or match. He is competitive and passionate about his favorite teams, but also enjoys trying out different sports himself. He is a great listener and always offers insightful perspectives on any topic.",
            ]


            convo = {
                "guid":"c"+str(selectedConvoKey),
                "participants": participants,
                "exchanges":selectedConvo['exchanges']
            }
        else:

            convo = {"guid":"c1234", "exchanges":[1,2,3,4], "participants":["Emily", "John"]}
        return convo

    async def completeConversation(self, hotkey, guid, dryrun=False):
        return True

class ConvoLib:
    async def getConversation(self, hotkey, dryrun=False):
        api = ApiLib()
        convo = await api.reserveConversation(hotkey, dryrun=dryrun)
        return convo

    async def getConvoPromptTemplate(self):
        return "Parse this"

    async def markConversionComplete(self, hotkey, cguid, dryrun=False):
        api = ApiLib()
        result = await api.completeConversation(hotkey, cguid, dryrun=dryrun)
        return result

class ValidatorLib:
    hotkey = "v1234"

    async def calculate_base_score(self, result_dict):
        total_1 = result_dict['total_1']
        total_2 = result_dict['total_2']
        unique_1_count = len(result_dict['unique_1'])
        unique_2_count = len(result_dict['unique_2'])
        both_count = len(result_dict['both'])

        # If all elements match, return a very low score
        if unique_1_count == 0 and unique_2_count == 0:
            return 0.1

        # If a large percentage of array 2 is unique, return a low score
        unique_2_ratio = unique_2_count / total_2
        if unique_2_ratio > 0.5:
            return 0.2

        # Calculate the percentage of matches
        matches_ratio = both_count / max(total_1, total_2)

        # Calculate the percentage of desired unique elements in array 2
        desired_unique_ratio = min(unique_2_count / (total_1 + unique_2_count), 0.2)

        # Combine the two ratios to get the final score
        score = (matches_ratio * 0.8) + (desired_unique_ratio * 0.2)

        return score

    async def calculate_emission_rewards(self, dicts, scoreKey):
        scores = Utils.pluck(dicts, scoreKey)
        total_scores = sum(scores)
        mean = total_scores / len(scores)
        stdev = math.sqrt(sum((x - mean) ** 2 for x in scores) / len(scores))

        def normal_pdf(x, mean, stdev):
            return math.exp(-(x - mean) ** 2 / (2 * stdev ** 2)) / (stdev * math.sqrt(2 * math.pi))

        rewards = []
        for cur_dict in dicts:
            score = Utils.get(cur_dict, scoreKey)
            pdf_value = normal_pdf(score, mean, stdev)
            reward_percentage = pdf_value / sum(normal_pdf(x, mean, stdev) for x in scores)
            cur_dict['reward'] = reward_percentage
            rewards.append(reward_percentage)

        return rewards

    async def requestConvo(self):
        minConvWindows = 1
        hotkey = "a123"
        fullConvo = await self.getConvo(hotkey)
        #print("fullConvo", fullConvo)

        if fullConvo:
            # Do overview tagging and participant profiles
            fullConvoMetaData = await self.generateFullConvoMetaData(fullConvo)
            #print("fullConvoMetaData", fullConvoMetaData)
            participantProfiles = Utils.get(fullConvoMetaData, "participantProfiles", [])
            fullConvoTags = Utils.get(fullConvoMetaData, "tags", [])
            fullConvoTagVectors = Utils.get(fullConvoMetaData, "tag_vectors", {})

            # Make sure there are enough tags to make processing worthwhile
            minValidTags = self.validateMinimumTags(fullConvoTags)
            if minValidTags:
                convoWindows = self.getConvoWindows(fullConvo)
                numWindows = len(convoWindows)
                if numWindows > minConvWindows:
                    print("Found %d convo windows. Sending to miners..." % (numWindows))
                    await self.sendWindowsToMiners(fullConvoTags, convoWindows, fullConvo)
                else:
                    print("Not enough convo windows -- only %d. Passing." % (numWindows))
            else:
                print("Not enough valid tags for conversation. Passing.")
                return

    async def eventLoop(self):
        while True:
            await self.requestConvo()

    async def getConvo(self, hotkey):
        cl = ConvoLib()
        convo = await cl.getConversation(hotkey, dryrun=True)
        return convo

    def getConvoWindows(self, fullConvo):
        minLines = c.get("convo_window", "min_lines", 5)
        maxLines = c.get("convo_window", "max_lines", 10)
        overlapLines = c.get("convo_window", "overlap_lines", 2)

        windows = Utils.split_overlap_array(fullConvo['exchanges'], size=maxLines, overlap=overlapLines)
        if len(windows) < 2:
            windows = Utils.split_overlap_array(fullConvo['exchanges'], size=minLines, overlap=overlapLines)

        # TODO: Write convo windows into local database with full convo metadata
        return windows



    async def generateFullConvoMetaData(self, convo):
        cl = ConvoLib()
        #print("METACONVO participants", convo['participants'])

        llml = LlmApi()
        matches_dict = await llml.conversation_to_tags(convo)
        tags = list(matches_dict.keys())

        half = int(len(tags) / 2)
        tagsQ = tags[0:half]
        tagsA = tags[half:]
        info = copy.deepcopy(proto)
        #info["interests_of_q"] = tagsQ
        #info["interests_of_a"] = tagsA
        ##print("FullConvo tags",  tags)
        print("Found %d FullConvo tags" % len(tags) )
        data = {
            "participantProfiles": convo['participants'],
            "tags": tags,
            "tag_vectors": matches_dict,
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

    def selectStage1Miners(self, uids, num=3):
        selectedMiners = random.sample(uids, num)
        return selectedMiners

    async def outputEmissions(self, convoId, windowId, emissionRewards):
        print("EMISSIONS for %d window %d" % (convoId, windowId), emissionRewards)


    async def sendWindowsToMiners(self, fullConvoTags, windows, fullConvo=None):
        cguid = Utils.get(fullConvo, "uid")
        # Get uids of available miners
        uids = bt.getUids()
        if len(uids) < 6:
            print("Not enough miners available.")
            return

        print("Full convo tags", fullConvoTags)

        # Loop through rows in db
        success = True
        for idx, window in enumerate(windows):
            # Pick initial minors
            miners = self.selectStage1Miners(uids, 5)
            # Send first window to 3 miners
            minerResults = await self.sendToMiners(window, miners)
            # Each miner returns data, write data into local db
            #print("Miner results", minerResults)
            # TODO: Write up incomplete errors, such as if timeout happens for miner, send to another miner
            # When all miners have returned data for convo window
            for minerResult in minerResults:
                uid = Utils.get(minerResult, 'uid')
                tags = Utils.get(minerResult, 'tags')
                compareResults = Utils.compare_arrays(fullConvoTags, tags)
                compareResults['total_1'] = len(fullConvoTags)
                compareResults['total_2'] = len(tags)
                #print("COMPARE", compareResults)
                scoreToFullConvo = await self.calculate_base_score(compareResults)
                minerResult['score'] = scoreToFullConvo

            await self.calculate_emission_rewards(minerResults, 'score')
            rewards = {}
            for minerResult in minerResults:
                rewards[minerResult['uid']] = minerResult['reward']
            # Send emissions
            await self.outputEmissions(1, idx, rewards)
        if success == True:
            cl = ConvoLib()
            await cl.markConversionComplete(self.hotkey, cguid)


class MinerLib:
    async def doMining(self, convoWindow, minerUid, dryrun=True):
        #print("MINERCONVO", convoWindow, minerUid)
        out = {"uid":minerUid, "tags":[], "profiles":[], "convoChecksum":11}

        #print("Mine result: %ds" % (waitSec))
        if dryrun:
            llml = LlmApi()
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
            exchanges = copy.deepcopy(convoWindow)
            exchanges.append([random.choice(exampleSentences), random.choice(exampleSentences)])
            matches_dict = await llml.conversation_to_tags({"exchanges":exchanges})
            tags = list(matches_dict.keys())
            out["tags"] = tags
            waitSec = random.randint(0, 3)
            #await asyncio.sleep(waitSec)
            if False:
                out["tags"].append(random.choice(exampleTags))
        else:
            # TODO: Make this actually tag content
            exampleTags = ["realistic", "business-minded", "conciliatory", "responsive", "caring", "understanding", "apologetic", "affectionate", "optimistic", "family-oriented"]
            out["tags"].append(random.choice(exampleTags))
        return out


    def get_conversation_tags(self, convo):
        tags = {}
        return tags


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

