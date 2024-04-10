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
    astra_credentials = get_astra_credentials()
    set_llm_cache(
        AstraDBCache(
            api_endpoint=astra_credentials["api_endpoint"],
            token=astra_credentials["token"],
            namespace=astra_credentials["namespace"],
        )
    )
