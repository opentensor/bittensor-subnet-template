
from conversationgenome.ApiLib import ApiLib


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

