import json
from typing import Union

from langchain_core.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document

from utils.db import get_astra_db_client
from common_constants import USERS_COLLECTION_NAME

from utils.models import UserProfile
from utils.ai import get_llm


def read_user_profile(user_id) -> Union[UserProfile, None]:
    astra_db_client = get_astra_db_client()
    users_col = astra_db_client.collection(USERS_COLLECTION_NAME)

    user_doc = users_col.find_one(
        filter={
            "_id": user_id,
        },
        projection={
            "base_preferences": 1,
            "additional_preferences": 1,
            "travel_profile_summary": 1,
        },
    )["data"]["document"]

    if user_doc:
        profile = UserProfile(
            base_preferences=json.loads(user_doc["base_preferences"]),
            additional_preferences=user_doc["additional_preferences"],
            travel_profile_summary=user_doc.get("travel_profile_summary"),
        )
        return profile
    else:
        return None


def write_user_profile(user_id, user_profile):
    astra_db_client = get_astra_db_client()
    users_col = astra_db_client.collection(USERS_COLLECTION_NAME)

    users_col.upsert(
        {
            "_id": user_id,
            "base_preferences": json.dumps(user_profile.base_preferences),
            "additional_preferences": user_profile.additional_preferences,
        }
    )


# def update_user_desc(user_id, base_preferences, additional_preferences):
def update_user_travel_profile_summary(user_id, user_profile):
    print("Updating automated travel preferences for user ", user_id)

    summarizing_llm = get_llm()

    # leave out the prefs that are false, instead of having them as no
    #     base_profile = ", ".join(
    #         "%s=%s" % (k.upper(), "yes" if v else "no") for k, v in base_preferences.items()
    #     )
    base_profile = ", ".join(
        k.upper() for k, v in user_profile.base_preferences.items() if v
    )

    travel_preferences = ", ".join([base_profile, user_profile.additional_preferences])

    prompt_template = """
    
    Summarize the following user's travel preferences, creating a short description that will be used to search for 
    hotels that this user may like.
    
    Keep it concise and clear. Use at least two and at most three short sentences and a neutral tone. Write in first person. 
    
    Here are two example summaries with information that is not relevant to the current user. 
    Only use these example summaries to understand the style of the summary. Absolutely do not use any information 
    contained in the example summaries when summarizing the current user's travel preferences. 
    Only use the information provided in the user's travel preferences.
    
    EXAMPLE SUMMARY 1: I travel with a group of androids and enjoy going to droid repair factories and swamps. I am interested in 
    creature-friendly hotels that can accommodate aliens.
    
    EXAMPLE SUMMARY 2: I am a pixie traveller who values convenient barrows and close proximity to 
    stone circles and bell-tolling options. I am not interested in dragons, crowded cities or 
    axe-grinding. I enjoy playing the harpsichord.
    
    USER'S TRAVEL PREFERENCES:
    {travel_prefs}
    
    CONCISE SUMMARY:
    """

    query_prompt_template = PromptTemplate.from_template(prompt_template)
    populated_prompt = query_prompt_template.format(travel_prefs=travel_preferences)
    print("Travel profile summary prompt:\n", populated_prompt)

    chain = load_summarize_chain(llm=summarizing_llm, chain_type="stuff")
    docs = [Document(page_content=populated_prompt)]
    travel_profile_summary = chain.run(docs)

    print("Travel profile summary:\n", travel_profile_summary)

    # write:
    astra_db_client = get_astra_db_client()
    users_col = astra_db_client.collection(USERS_COLLECTION_NAME)

    users_col.find_one_and_update(
        filter={
            "_id": user_id
        },
        update={
            "$set": {
                "travel_profile_summary": travel_profile_summary,
            },
        },
    )
