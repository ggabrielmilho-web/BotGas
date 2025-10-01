"""
Address cache service - Manages cached addresses to reduce API calls
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database.models import AddressCache

logger = logging.getLogger(__name__)


class AddressCacheService:
    """
    Manages address cache to reduce Google Maps API calls

    Features:
    - Cache validated addresses for 30 days
    - Fuzzy matching for similar addresses
    - Statistics tracking (cache hit rate)
    - Automatic cleanup of expired entries
    """

    DEFAULT_CACHE_DAYS = 30

    def __init__(self, db: Session, cache_days: int = DEFAULT_CACHE_DAYS):
        self.db = db
        self.cache_days = cache_days

    async def get_cached_address(
        self,
        address: str,
        tenant_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached address if exists and valid

        Returns:
            {
                "normalized_address": str,
                "coordinates": dict,
                "neighborhood": str,
                "delivery_fee": float,
                "is_deliverable": bool,
                "cached_at": datetime,
                "age_days": int
            }
        """

        # Normalize address for lookup
        normalized_input = self._normalize_address(address)

        # Exact match first
        cached = self.db.query(AddressCache).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.address_text == normalized_input
            )
        ).first()

        if cached:
            # Check if still valid
            age = datetime.utcnow() - cached.validated_at
            if age <= timedelta(days=self.cache_days):
                logger.info(f"Cache HIT (exact): {address[:50]}")

                return {
                    "normalized_address": cached.normalized_address,
                    "coordinates": cached.coordinates,
                    "neighborhood": cached.neighborhood,
                    "city": cached.city,
                    "state": cached.state,
                    "zip_code": cached.zip_code,
                    "delivery_fee": float(cached.delivery_fee or 0),
                    "is_deliverable": cached.is_deliverable,
                    "cached_at": cached.validated_at,
                    "age_days": age.days,
                    "cache_hit": "exact"
                }
            else:
                # Expired - delete
                self.db.delete(cached)
                self.db.commit()
                logger.info(f"Cache expired and deleted: {address[:50]}")

        # Try fuzzy match
        fuzzy_match = await self._fuzzy_match(normalized_input, tenant_id)

        if fuzzy_match:
            logger.info(f"Cache HIT (fuzzy): {address[:50]}")
            fuzzy_match["cache_hit"] = "fuzzy"
            return fuzzy_match

        logger.info(f"Cache MISS: {address[:50]}")
        return None

    async def save_to_cache(
        self,
        address: str,
        tenant_id: UUID,
        validation_result: Dict[str, Any]
    ) -> bool:
        """
        Save validated address to cache
        """

        try:
            normalized_input = self._normalize_address(address)

            # Check if already exists
            existing = self.db.query(AddressCache).filter(
                and_(
                    AddressCache.tenant_id == tenant_id,
                    AddressCache.address_text == normalized_input
                )
            ).first()

            if existing:
                # Update existing
                existing.normalized_address = validation_result.get("normalized_address")
                existing.coordinates = validation_result.get("coordinates")
                existing.neighborhood = validation_result.get("neighborhood")
                existing.city = validation_result.get("city")
                existing.state = validation_result.get("state")
                existing.zip_code = validation_result.get("zip_code")
                existing.delivery_fee = validation_result.get("delivery_fee", 0)
                existing.is_deliverable = validation_result.get("is_deliverable", False)
                existing.validated_at = datetime.utcnow()

                logger.info(f"Cache updated: {address[:50]}")

            else:
                # Create new
                cache_entry = AddressCache(
                    tenant_id=tenant_id,
                    address_text=normalized_input,
                    normalized_address=validation_result.get("normalized_address"),
                    coordinates=validation_result.get("coordinates"),
                    neighborhood=validation_result.get("neighborhood"),
                    city=validation_result.get("city"),
                    state=validation_result.get("state"),
                    zip_code=validation_result.get("zip_code"),
                    delivery_fee=validation_result.get("delivery_fee", 0),
                    is_deliverable=validation_result.get("is_deliverable", False),
                    validated_at=datetime.utcnow(),
                    google_place_id=validation_result.get("place_id")
                )

                self.db.add(cache_entry)

                logger.info(f"Cache saved: {address[:50]}")

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            self.db.rollback()
            return False

    async def _fuzzy_match(
        self,
        address: str,
        tenant_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Try to find similar addresses using fuzzy matching
        """

        # Extract key components (street number, neighborhood)
        import re

        # Extract street number
        numbers = re.findall(r'\b\d+\b', address)

        if not numbers:
            return None

        street_number = numbers[0]

        # Find addresses with same street number
        similar = self.db.query(AddressCache).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.address_text.like(f'%{street_number}%'),
                AddressCache.validated_at >= datetime.utcnow() - timedelta(days=self.cache_days)
            )
        ).all()

        if not similar:
            return None

        # Calculate similarity score
        best_match = None
        best_score = 0

        for candidate in similar:
            score = self._calculate_similarity(address, candidate.address_text)

            if score > best_score and score >= 0.8:  # 80% similarity threshold
                best_score = score
                best_match = candidate

        if best_match:
            age = datetime.utcnow() - best_match.validated_at

            return {
                "normalized_address": best_match.normalized_address,
                "coordinates": best_match.coordinates,
                "neighborhood": best_match.neighborhood,
                "city": best_match.city,
                "state": best_match.state,
                "zip_code": best_match.zip_code,
                "delivery_fee": float(best_match.delivery_fee or 0),
                "is_deliverable": best_match.is_deliverable,
                "cached_at": best_match.validated_at,
                "age_days": age.days,
                "similarity_score": best_score
            }

        return None

    def _normalize_address(self, address: str) -> str:
        """
        Normalize address for consistent caching

        - Lowercase
        - Remove extra spaces
        - Remove special characters
        - Standardize abbreviations
        """

        import re

        normalized = address.lower().strip()

        # Remove special characters except space, comma, numbers
        normalized = re.sub(r'[^\w\s,]', '', normalized)

        # Standardize abbreviations
        replacements = {
            r'\br\b': 'rua',
            r'\bav\b': 'avenida',
            r'\bal\b': 'alameda',
            r'\btr\b': 'travessa',
            r'\bn°\b': '',
            r'\bnº\b': '',
            r'\bno\b': '',
        }

        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)

        # Remove extra spaces
        normalized = ' '.join(normalized.split())

        return normalized

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings (0-1)
        Using simple character-based similarity
        """

        from difflib import SequenceMatcher

        return SequenceMatcher(None, str1, str2).ratio()

    async def get_cache_statistics(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cache statistics for tenant
        """

        from sqlalchemy import func

        since_date = datetime.utcnow() - timedelta(days=days)

        # Total cached addresses
        total_cached = self.db.query(func.count(AddressCache.id)).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.validated_at >= since_date
            )
        ).scalar()

        # Deliverable vs non-deliverable
        deliverable = self.db.query(func.count(AddressCache.id)).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.is_deliverable == True,
                AddressCache.validated_at >= since_date
            )
        ).scalar()

        # Most common neighborhoods
        top_neighborhoods = self.db.query(
            AddressCache.neighborhood,
            func.count(AddressCache.id).label('count')
        ).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.is_deliverable == True,
                AddressCache.validated_at >= since_date
            )
        ).group_by(
            AddressCache.neighborhood
        ).order_by(
            func.count(AddressCache.id).desc()
        ).limit(10).all()

        return {
            "total_cached": total_cached,
            "deliverable": deliverable,
            "non_deliverable": total_cached - deliverable,
            "top_neighborhoods": [
                {"neighborhood": n[0], "count": n[1]}
                for n in top_neighborhoods
            ],
            "cache_period_days": days,
            "estimated_api_calls_saved": total_cached  # Assumes 1 cache = 1 API call saved
        }

    async def cleanup_expired_cache(self, tenant_id: Optional[UUID] = None):
        """
        Remove expired cache entries
        """

        cutoff_date = datetime.utcnow() - timedelta(days=self.cache_days)

        query = self.db.query(AddressCache).filter(
            AddressCache.validated_at < cutoff_date
        )

        if tenant_id:
            query = query.filter(AddressCache.tenant_id == tenant_id)

        deleted_count = query.delete()
        self.db.commit()

        logger.info(f"Cleaned up {deleted_count} expired cache entries")

        return deleted_count

    async def invalidate_address(
        self,
        address: str,
        tenant_id: UUID
    ) -> bool:
        """
        Manually invalidate a cached address
        """

        normalized_input = self._normalize_address(address)

        deleted = self.db.query(AddressCache).filter(
            and_(
                AddressCache.tenant_id == tenant_id,
                AddressCache.address_text == normalized_input
            )
        ).delete()

        self.db.commit()

        return deleted > 0
