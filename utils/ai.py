import os
from dotenv import find_dotenv, load_dotenv

from langchain.globals import set_llm_cache
from langchain_openai.llms import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_astradb.cache import AstraDBCache

from utils.db import get_astra_credentials


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
    astra_credentials_alt = get_astra_credentials(alternative_db=True)
    if astra_credentials_alt:
        set_llm_cache(
            AstraDBCache(
                api_endpoint=astra_credentials_alt["api_endpoint"],
                token=astra_credentials_alt["token"],
                namespace=astra_credentials_alt["namespace"],
            )
        )
    else:
        print("\n\n   *** NO LLM CACHING AVAILABLE ***\n\n")

