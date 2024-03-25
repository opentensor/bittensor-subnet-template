import pytest
import conversationgenome as cg
from conversationgenome.Skeleton import Skeleton
import unittest

class TemplateCgForwardTestCase(unittest.TestCase):
    verbose = True

    def setUp(self):
        pass

    def test_create_convo_packet(self):
        if self.verbose:
            print("Setting up convo packet")
        assert 1 == 1


