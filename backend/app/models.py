"""SQLAlchemy models for the MVP1 core schema.

Mirrors database/migrations/0002_core_schema.sql. Spatial columns use
GeoAlchemy2 Geography(Point, 4326).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prefectures: Mapped[list[Prefecture]] = relationship(back_populates="region")


class Prefecture(Base):
    __tablename__ = "prefectures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"), nullable=False)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    region: Mapped[Region] = relationship(back_populates="prefectures")


class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    prefecture_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prefectures.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    license_note: Mapped[str | None] = mapped_column(Text)
    collection_method: Mapped[str | None] = mapped_column(Text)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Spot(Base):
    __tablename__ = "spots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str | None] = mapped_column(Text)
    name_zh: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    prefecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prefectures.id"))
    city_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cities.id"))
    location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    category: Mapped[str | None] = mapped_column(Text)
    subcategory: Mapped[str | None] = mapped_column(Text)
    best_season: Mapped[str | None] = mapped_column(Text)
    recommended_stay_minutes: Mapped[int | None] = mapped_column(Integer)
    estimated_budget_min: Mapped[int | None] = mapped_column(Integer)
    estimated_budget_max: Mapped[int | None] = mapped_column(Integer)
    access_text: Mapped[str | None] = mapped_column(Text)
    official_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"))
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tags: Mapped[list[SpotTag]] = relationship(back_populates="spot", cascade="all, delete-orphan")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False)
    prefecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prefectures.id"))
    city_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cities.id"))
    location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    category: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[int | None] = mapped_column(Integer)
    price_max: Mapped[int | None] = mapped_column(Integer)
    fish: Mapped[bool] = mapped_column(Boolean, server_default="false")
    meat: Mapped[bool] = mapped_column(Boolean, server_default="false")
    vegetarian: Mapped[bool] = mapped_column(Boolean, server_default="false")
    vegan: Mapped[bool] = mapped_column(Boolean, server_default="false")
    local_specialty: Mapped[bool] = mapped_column(Boolean, server_default="false")
    reservation_url: Mapped[str | None] = mapped_column(Text)
    official_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"))
    source_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    food_tags: Mapped[list[FoodTag]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False)
    prefecture_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prefectures.id"))
    location: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    category: Mapped[str | None] = mapped_column(Text)
    official_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"))
    source_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SpotTag(Base):
    __tablename__ = "spot_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    spot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spots.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[str] = mapped_column(Text, server_default="manual")  # manual / ai
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))

    spot: Mapped[Spot] = relationship(back_populates="tags")


class SpotAnalysis(Base):
    __tablename__ = "spot_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    spot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spots.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary: Mapped[str | None] = mapped_column(Text)
    categories: Mapped[list] = mapped_column(JSONB, server_default="[]")
    tags: Mapped[list] = mapped_column(JSONB, server_default="[]")
    best_season: Mapped[list] = mapped_column(JSONB, server_default="[]")
    travel_types: Mapped[list] = mapped_column(JSONB, server_default="[]")
    food_tags: Mapped[list] = mapped_column(JSONB, server_default="[]")
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), server_default="0")
    evidence: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed: Mapped[bool] = mapped_column(Boolean, server_default="false")
    override: Mapped[dict | None] = mapped_column(JSONB)


class FoodTag(Base):
    __tablename__ = "food_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    tag: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    source_url: Mapped[str | None] = mapped_column(Text)

    restaurant: Mapped[Restaurant] = relationship(back_populates="food_tags")
