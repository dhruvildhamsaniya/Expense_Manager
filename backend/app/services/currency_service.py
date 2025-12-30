import httpx
from typing import Dict, Optional
from datetime import datetime, timedelta
from app.db import db
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        self.api_url = settings.EXCHANGE_RATE_API_URL
        self.cache_hours = settings.CACHE_EXCHANGE_RATES_HOURS
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate from from_currency to to_currency.
        Uses cache if available and fresh, otherwise fetches from API.
        """
        if from_currency == to_currency:
            return 1.0
        
        # Check cache first
        cached_rate = await self._get_cached_rate(from_currency, to_currency)
        if cached_rate:
            return cached_rate
        
        # Fetch from API
        rate = await self._fetch_rate_from_api(from_currency, to_currency)
        
        if rate:
            # Cache the rate
            await self._cache_rate(from_currency, to_currency, rate)
        
        return rate
    
    async def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get rate from cache if fresh."""
        try:
            result = await db.fetch_one(
                """
                SELECT rate, fetched_at
                FROM exchange_rates
                WHERE base_currency = $1 AND target_currency = $2
                """,
                from_currency, to_currency
            )
            
            if result:
                fetched_at = result['fetched_at']
                age = datetime.now(fetched_at.tzinfo) - fetched_at
                
                if age < timedelta(hours=self.cache_hours):
                    logger.info(f"Using cached rate: {from_currency} -> {to_currency} = {result['rate']}")
                    return float(result['rate'])
            
            return None
        
        except Exception as e:
            logger.error(f"Error fetching cached rate: {e}")
            return None
    
    async def _fetch_rate_from_api(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Fetch exchange rate from API."""
        try:
            url = f"{self.api_url}/{from_currency}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get('rates', {})
                    
                    if to_currency in rates:
                        rate = float(rates[to_currency])
                        logger.info(f"Fetched rate from API: {from_currency} -> {to_currency} = {rate}")
                        return rate
            
            logger.warning(f"Could not fetch rate for {from_currency} -> {to_currency}")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching rate from API: {e}")
            return None
    
    async def _cache_rate(self, from_currency: str, to_currency: str, rate: float):
        """Cache exchange rate in database."""
        try:
            await db.execute(
                """
                INSERT INTO exchange_rates (base_currency, target_currency, rate, fetched_at)
                VALUES ($1, $2, $3, now())
                ON CONFLICT (base_currency, target_currency)
                DO UPDATE SET rate = $3, fetched_at = now()
                """,
                from_currency, to_currency, rate
            )
            logger.info(f"Cached rate: {from_currency} -> {to_currency} = {rate}")
        
        except Exception as e:
            logger.error(f"Error caching rate: {e}")
    
    async def convert_amount(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> Dict[str, float]:
        """
        Convert amount from one currency to another.
        Returns dict with 'converted_amount' and 'rate'.
        """
        rate = await self.get_exchange_rate(from_currency, to_currency)
        
        if rate is None:
            logger.warning(f"Could not convert {from_currency} to {to_currency}, using 1:1")
            rate = 1.0
        
        converted = amount * rate
        
        return {
            'converted_amount': round(converted, 2),
            'rate': rate
        }

currency_service = CurrencyService()