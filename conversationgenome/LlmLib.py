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
            matches_dict = await self.simple_text_to_tags(json.dumps(convo['lines']))
        else:
            print("Send conversation to the LLM")
        return matches_dict



    async def simple_text_to_tags(self, body):
        nlp = self.nlp
        if not nlp:
            # python -m spacy download en_core_web_sm
            #nlp = spacy.load("en_core_web_sm")
            #nlp = spacy.load("en_core_web_md")
            nlp = spacy.load("en_core_web_lg") # ~600mb
            #print(f"Vector dimensionality: {nlp.vocab.vectors_length}")
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
