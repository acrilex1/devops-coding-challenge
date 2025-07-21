"""
Unit tests for PricingService

Tests the AWS S3 pricing functionality including:
- API unavailable scenarios (e.g., LocalStack environment)
- AWS Pricing API success and failure scenarios
- Caching behavior
- Simplified single-API-call design
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.pricing_service import PricingService


class TestPricingService:
    """Test cases for PricingService class."""
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"DEFAULT_S3_PRICE_PER_GB": "0.023"})
    @pytest.mark.parametrize("scenario,side_effect", [
        ("API unavailable", Exception("AWS API not available")),
        ("API failure", Exception("API Error")),
        ("Empty response", {"PriceList": []}),
    ])
    async def test_get_s3_pricing_fallback_scenarios(self, scenario, side_effect):
        """Test pricing fallback for various failure scenarios."""
        # Arrange
        pricing_service = PricingService()
        
        with patch("boto3.client") as mock_client:
            mock_pricing_client = MagicMock()
            if isinstance(side_effect, Exception):
                mock_pricing_client.get_products.side_effect = side_effect
            else:
                mock_pricing_client.get_products.return_value = side_effect
            mock_client.return_value = mock_pricing_client
            
            # Act
            price_standard = await pricing_service.get_s3_pricing("STANDARD")
            price_ia = await pricing_service.get_s3_pricing("STANDARD_IA")
            
            # Assert
            assert price_standard == 0.023, f"Failed for scenario: {scenario}"
            assert price_ia == 0.023, f"Failed for scenario: {scenario}"
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"DEFAULT_S3_PRICE_PER_GB": "0.025"})
    async def test_get_s3_pricing_aws_success_and_caching(self):
        """Test pricing from AWS Pricing API and that results are cached (API called only once)."""
        # Arrange
        pricing_service = PricingService()
        
        # Mock the full API response with multiple storage classes
        mock_response = {
            "PriceList": [
                '{"product":{"attributes":{"storageClass":"General Purpose"}},"terms":{"OnDemand":{"test":{"priceDimensions":{"test":{"pricePerUnit":{"USD":"0.030"}}}}}}}',
                '{"product":{"attributes":{"storageClass":"Standard - Infrequent Access"}},"terms":{"OnDemand":{"test":{"priceDimensions":{"test":{"pricePerUnit":{"USD":"0.0125"}}}}}}}',
            ]
        }
        
        with patch("boto3.client") as mock_client:
            mock_pricing_client = MagicMock()
            mock_pricing_client.get_products.return_value = mock_response
            mock_client.return_value = mock_pricing_client
            
            # Act - Multiple calls to test both success and caching
            price1 = await pricing_service.get_s3_pricing("STANDARD")
            price2 = await pricing_service.get_s3_pricing("STANDARD")  # Should use cache
            price_ia = await pricing_service.get_s3_pricing("STANDARD___INFREQUENT_ACCESS")  # Should use cache
            price_unknown = await pricing_service.get_s3_pricing("UNKNOWN_CLASS")  # Should use default
            
            # Assert - Verify correct pricing and caching behavior
            assert price1 == 0.030  # From API response
            assert price2 == 0.030  # From cache (same value)
            assert price_ia == 0.0125  # From cache (Standard IA price)
            assert price_unknown == 0.025  # Default price for unknown class
            
            # Verify API was called only once despite multiple pricing requests
            mock_pricing_client.get_products.assert_called_once()
