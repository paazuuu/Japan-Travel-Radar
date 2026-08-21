"""Pydantic response/request schemas for the MVP1 API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class SpotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    name_en: str | None = None
    name_zh: str | None = None
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    best_season: str | None = None
    recommended_stay_minutes: int | None = None
    estimated_budget_min: int | None = None
    estimated_budget_max: int | None = None
    access_text: str | None = None
    official_url: str | None = None
    image_url: str | None = None
    image_license: str | None = None
    source_url: str | None = None
    status: str
    lat: float | None = None
    lng: float | None = None
    distance_m: float | None = None
    # AI analysis (MVP3) — kept clearly separate from source fields.
    ai_summary: str | None = None
    tags: list[str] = []
    travel_types: list[str] = []
    ai_confidence: float | None = None
    trend_score: float | None = None


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    spot_id: uuid.UUID
    summary: str | None = None
    categories: list[str] = []
    tags: list[str] = []
    best_season: list[str] = []
    travel_types: list[str] = []
    food_tags: list[str] = []
    confidence: float = 0
    evidence: str | None = None
    model: str
    reviewed: bool = False


class RegisterIn(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None


class PlanRequest(BaseModel):
    origin: str = "大阪"
    origin_lat: float | None = None
    origin_lng: float | None = None
    start_date: str | None = None
    days: int = 1
    budget: int | None = 5000
    party_size: int = 1
    transport: str = "train"          # train / car / walk
    purpose: str | None = None        # e.g. "絶景"
    food: str | None = None           # e.g. "魚"
    travel_type: str | None = None    # e.g. "couple"
    max_spots: int = 3


class PlanItemOut(BaseModel):
    sequence: int
    kind: str
    label: str
    start_time: str | None = None
    end_time: str | None = None
    estimated_cost: int = 0
    travel_time: int = 0
    spot_id: uuid.UUID | None = None
    restaurant_id: uuid.UUID | None = None
    source_url: str | None = None


class PlanOut(BaseModel):
    id: uuid.UUID
    origin: str
    days: int
    budget: int | None = None
    party_size: int
    transport: str
    summary: str | None = None
    total_cost: int | None = None
    within_budget: bool | None = None
    items: list[PlanItemOut] = []


class EventOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    prefecture_id: uuid.UUID | None = None
    lat: float | None = None
    lng: float | None = None
    start_at: str | None = None
    end_at: str | None = None
    official_url: str | None = None
    image_url: str | None = None
    source_url: str | None = None


class RankingItem(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None = None
    prefecture_id: uuid.UUID | None = None
    lat: float | None = None
    lng: float | None = None
    image_url: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    trend_score: float
    growth_score: float
    engagement_score: float
    recency_score: float
    seasonality_score: float
    source_diversity_score: float
    novelty_score: float
    data_confidence_score: float
    is_reference: bool
    score_date: str


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    fish: bool = False
    meat: bool = False
    vegetarian: bool = False
    vegan: bool = False
    local_specialty: bool = False
    reservation_url: str | None = None
    official_url: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    lat: float | None = None
    lng: float | None = None
    distance_m: float | None = None
