from typing import Dict, List, Union

from fastapi import BackgroundTasks, FastAPI, HTTPException

from utils.ai import enable_llm_cache
from utils.db import get_database
from utils.hotels import find_hotel_by_id, find_hotels_by_location
from utils.localCORS import permitReactLocalhostClient
from utils.models import (
    CustomizedHotelDetails,
    Hotel,
    HotelDetailsRequest,
    HotelReview,
    HotelSearchRequest,
    HotelSummary,
    UserProfile,
    UserProfileSubmitRequest,
    UserRequest,
)
from utils.review_llm import summarize_reviews_for_hotel, summarize_reviews_for_user
from utils.reviews import (
    insert_review_for_hotel,
    select_general_hotel_reviews,
    select_hotel_reviews_for_user,
    select_review_count_by_hotel,
)
from utils.strings import DEFAULT_TRAVEL_PROFILE_SUMMARY
from utils.users import (
    read_user_profile,
    update_user_travel_profile_summary,
    write_user_profile,
)


def init() -> None:
    get_database()
    enable_llm_cache()


init()
app = FastAPI()
permitReactLocalhostClient(app)


@app.post("/v1/get_user_profile")
def get_user_profile(payload: UserRequest) -> Union[UserProfile, None]:
    """
    Endpoint that retrieves the travel preferences
    (base + additional prefs) of the specified user.
    """

    return read_user_profile(payload.user_id)


@app.post("/v1/set_user_profile")
def set_user_profile(
    payload: UserProfileSubmitRequest, bg_tasks: BackgroundTasks
) -> Dict[str, bool]:
    """
    Endpoint that stores the travel preferences (base + additional prefs)
    of the specified user.

    It also calls the LLM to create the travel profile summary,
    and stores the summary in the user's profile.
    """

    try:
        write_user_profile(
            payload.user_id,
            payload.user_profile,
        )
        bg_tasks.add_task(
            update_user_travel_profile_summary,
            user_id=payload.user_id,
            user_profile=payload.user_profile,
        )
        return {
            "success": True,
        }
    except Exception:
        return {
            "success": False,
        }


@app.post("/v1/find_hotels")
def get_hotels(hotel_request: HotelSearchRequest) -> List[Hotel]:
    """
    Endpoint that retrieves a list of hotels located in the specified city.

    TODO implement geo search based on proximity to a point
    """

    hotels = find_hotels_by_location(hotel_request.city, hotel_request.country)
    for hotel in hotels:
        hotel.review_count = select_review_count_by_hotel(hotel.id)
    return hotels


@app.post("/v1/base_hotel_summary")
def get_base_hotel_summary(payload: HotelDetailsRequest) -> HotelSummary:
    """
    Endpoint that selects the most recent reviews + some featured ones
    and creates a general concise summary.
    """

    hotel_reviews = select_general_hotel_reviews(payload.id)
    hotel_review_summary = summarize_reviews_for_hotel(hotel_reviews)
    return HotelSummary(
        request_id=payload.request_id,
        reviews=hotel_reviews,
        summary=hotel_review_summary,
    )


# Endpoint that inserts a review for a hotel.
@app.post("/v1/{hotel_id}/add_review")
def add_review(hotel_id: str, payload: HotelReview) -> Dict[str, bool]:
    try:
        insert_review_for_hotel(
            hotel_id=hotel_id,
            review_title=payload.title,
            review_body=payload.body,
            review_rating=payload.rating,
        )
        return {
            "success": True,
        }
    except Exception:
        return {
            "success": False,
        }


# Endpoint that selects the three reviews of this hotel that are most relevant to this user
# and generates a user-tailored summary of these reviews.
@app.post("/v1/customized_hotel_details/{hotel_id}")
def get_customized_hotel_details(
    hotel_id: str, payload: UserRequest
) -> CustomizedHotelDetails:
    """
    1. retrieve user data (esp. textual description)
    2. retrieve *user-relevant* reviews with ANN search
    3. retrieve hotel details
    4. stuff 1 and 2 into a prompt "get me a short summary"
    5. call the LLM to get the short summary (which takes advantage of the auto cache prompt->response)
    6. return the summary and the reviews used (+ name), as in the structure below
    """

    hotel_details = find_hotel_by_id(hotel_id)

    if hotel_details is None:
        raise HTTPException(status_code=404, detail=f"Hotel '{hotel_id}' not found")

    user_profile = read_user_profile(payload.user_id)

    if user_profile:
        travel_profile_summary = (
            user_profile.travel_profile_summary or DEFAULT_TRAVEL_PROFILE_SUMMARY
        )
    else:
        travel_profile_summary = DEFAULT_TRAVEL_PROFILE_SUMMARY

    hotel_reviews_for_user = select_hotel_reviews_for_user(
        hotel_id=hotel_id,
        user_travel_profile_summary=travel_profile_summary,
    )

    customized_review_summary = summarize_reviews_for_user(
        reviews=hotel_reviews_for_user,
        travel_profile_summary=travel_profile_summary,
    )

    return CustomizedHotelDetails(
        name=hotel_details.name,
        summary=customized_review_summary,
        reviews=hotel_reviews_for_user,
    )
