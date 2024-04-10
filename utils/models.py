from typing import Dict, List, Optional

from pydantic import BaseModel


class ReviewRequest(BaseModel):
    review: str


class HotelSearchRequest(BaseModel):
    city: str
    country: str


class HotelDetailsRequest(BaseModel):
    request_id: str
    city: str
    country: str
    id: str


class HotelReview(BaseModel):
    title: str
    body: str
    rating: int
    id: str


class CustomizedHotelDetails(BaseModel):
    name: str
    reviews: List[HotelReview]
    summary: List[str]


class HotelSummary(BaseModel):
    request_id: str
    reviews: List[HotelReview]
    summary: List[str]


class CappedCounter(BaseModel):
    count: int
    at_ceiling: bool = False


class Hotel(BaseModel):
    city: str
    country: str
    name: str
    id: str
    review_count: Optional[CappedCounter] = None


class UserRequest(BaseModel):
    user_id: str


class UserProfile(BaseModel):
    base_preferences: Dict[str, bool]
    additional_preferences: str
    travel_profile_summary: Optional[str] = None


class UserProfileSubmitRequest(BaseModel):
    user_id: str
    user_profile: UserProfile
