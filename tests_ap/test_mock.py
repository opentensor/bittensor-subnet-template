import pytest
import conversationgenome as cg
from conversationgenome.Skeleton import Skeleton
import unittest

class TemplateCgTestCase(unittest.TestCase):
    verbose = True

    def setUp(self):
        pass

    def test_run_single_step(self):
        s = Skeleton()
        if self.verbose:
            print("Skeleton name: ", s.get_skeleton())
        assert 1 == 1


