import pytest
from conversationgenome.ValidatorLib import ValidatorLib

@pytest.mark.asyncio
async def test_full():
    vl = ValidatorLib()
    await vl.requestConvo()
    #await vl.neighborhood_test()

