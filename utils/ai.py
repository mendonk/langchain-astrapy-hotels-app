import os
from dotenv import find_dotenv, load_dotenv

import langchain
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.cache import AstraDBCache

from utils.db import get_astra_db_client


LLM_PROVIDER = "OpenAI"

dotenv_file = find_dotenv(".env")
load_dotenv(dotenv_file)

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

EMBEDDING_DIMENSION = 1536

llm = None
embeddings = None


def get_llm():
    global llm
    if llm is None:
        llm = OpenAI(openai_api_key=OPENAI_API_KEY)
    #
    return llm


def get_embeddings():
    global embeddings
    if embeddings is None:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    #
    return embeddings


def enable_llm_cache():
    # This is a strange trick to circumvent the 5-collection limit
    # well... 'circumvent' actually means we use TWO DATABASES lol
    astra_db_client2 = get_astra_db_client(alternative_db=True)
    if astra_db_client2:
        langchain.llm_cache = AstraDBCache(astra_db_client=astra_db_client2)
    else:
        print("\n\n   *** NO LLM CACHING AVAILABLE ***\n\n")

