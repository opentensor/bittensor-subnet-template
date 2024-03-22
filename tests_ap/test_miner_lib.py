import unittest
import pytest

from conversationgenome.ConversationDatabase import ConversationDatabase
from conversationgenome.MinerLib import MinerLib
from conversationgenome.ValidatorLib import ValidatorLib

class TemplateCgTestMinerLib(unittest.TestCase):
    verbose = True

    def setUp(self):
        self.CD = ConversationDatabase()

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
        convo = self.CD.getConversation()
        assert len(convo) == 3

    def test_tags_from_convo(self):
        if self.verbose:
            print("Test Convo")
        convo = self.CD.getConversation()
        ml = MinerLib()
        tags = ml.get_conversation_tags(convo)
        assert len(tags) > 10


