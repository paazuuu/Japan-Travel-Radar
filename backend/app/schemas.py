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
    source_url: str | None = None
    lat: float | None = None
    lng: float | None = None
    distance_m: float | None = None
