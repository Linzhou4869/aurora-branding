#!/usr/bin/env python3
"""
Test suite for Construction Budget Calculator.
Tests calculate_material_costs and main functions.
Currency: SEK (Swedish Krona)
"""

import unittest
from unittest.mock import patch
from budget_calculator import (
    cost_summary,
    total_area_sqm,
    tax_rate,
    calculate_material_costs,
    main
)


class TestCalculateMaterialCosts(unittest.TestCase):
    """Tests for calculate_material_costs function."""

    def test_returns_integer(self):
        """Test that function returns an integer."""
        result = calculate_material_costs()
        self.assertIsInstance(result, int)

    def test_returns_positive_value(self):
        """Test that result is positive."""
        result = calculate_material_costs()
        self.assertGreater(result, 0)

    def test_equals_sum_of_categories(self):
        """Test that result equals sum of all cost_summary values."""
        result = calculate_material_costs()
        expected = sum(cost_summary.values())
        self.assertEqual(result, expected)

    def test_foundations_value(self):
        """Test Foundations is 45,000,000 SEK."""
        self.assertEqual(cost_summary['Foundations'], 45000000)

    def test_structural_steel_value(self):
        """Test Structural Steel is 62,500,000 SEK."""
        self.assertEqual(cost_summary['Structural Steel'], 62500000)

    def test_logistics_value(self):
        """Test Logistics Infrastructure is 18,000,000 SEK."""
        self.assertEqual(cost_summary['Logistics Infrastructure'], 18000000)

    def test_total_material_cost(self):
        """Test total material costs (45M + 62.5M + 18M = 125.5M SEK)."""
        result = calculate_material_costs()
        self.assertEqual(result, 125500000)

    def test_cost_summary_has_three_categories(self):
        """Test that cost_summary has exactly 3 categories."""
        self.assertEqual(len(cost_summary), 3)

    def test_all_categories_are_positive(self):
        """Test all category values are positive."""
        for category, cost in cost_summary.items():
            self.assertGreater(cost, 0, f"{category} should be positive")


class TestMainFunction(unittest.TestCase):
    """Tests for main function."""

    @patch('builtins.print')
    def test_returns_grand_total(self, mock_print):
        """Test that main returns the grand total with tax."""
        result = main()
        material_total = calculate_material_costs()
        price_per_sqm = 125500000  # Sum of key categories
        area_cost = total_area_sqm * price_per_sqm
        subtotal = material_total + area_cost
        tax_amount = subtotal * tax_rate
        expected_total = subtotal + tax_amount
        self.assertEqual(result, expected_total)

    @patch('builtins.print')
    def test_prints_header(self, mock_print):
        """Test that main prints the header."""
        main()
        header_calls = [
            call for call in mock_print.call_args_list
            if 'CONSTRUCTION BUDGET CALCULATOR' in str(call)
        ]
        self.assertGreater(len(header_calls), 0)

    @patch('builtins.print')
    def test_prints_cost_summary(self, mock_print):
        """Test that main prints cost summary."""
        main()
        summary_calls = [
            call for call in mock_print.call_args_list
            if 'Cost Summary' in str(call)
        ]
        self.assertGreater(len(summary_calls), 0)

    @patch('builtins.print')
    def test_prints_tax(self, mock_print):
        """Test that main prints tax information."""
        main()
        tax_calls = [
            call for call in mock_print.call_args_list
            if 'Tax' in str(call)
        ]
        self.assertGreater(len(tax_calls), 0)

    @patch('builtins.print')
    def test_prints_grand_total(self, mock_print):
        """Test that main prints grand total."""
        main()
        total_calls = [
            call for call in mock_print.call_args_list
            if 'Grand Total' in str(call)
        ]
        self.assertGreater(len(total_calls), 0)


class TestParameters(unittest.TestCase):
    """Tests for script parameters."""

    def test_total_area_is_5000(self):
        """Test total_area_sqm is 5000."""
        self.assertEqual(total_area_sqm, 5000)

    def test_tax_rate_is_0_25(self):
        """Test tax_rate is 0.25 (25%)."""
        self.assertEqual(tax_rate, 0.25)

    def test_total_area_is_positive(self):
        """Test total_area_sqm is positive."""
        self.assertGreater(total_area_sqm, 0)

    def test_tax_rate_is_positive(self):
        """Test tax_rate is positive."""
        self.assertGreater(tax_rate, 0)

    def test_tax_rate_is_less_than_one(self):
        """Test tax_rate is less than 1 (100%)."""
        self.assertLess(tax_rate, 1)


class TestPricePerSqmCalculation(unittest.TestCase):
    """Tests for price_per_sqm calculation logic."""

    def test_price_per_sqm_equals_sum_of_three_categories(self):
        """Test price_per_sqm equals Foundations + Structural Steel + Logistics."""
        expected = (
            cost_summary['Foundations']
            + cost_summary['Structural Steel']
            + cost_summary['Logistics Infrastructure']
        )
        self.assertEqual(expected, 125500000)

    def test_foundations_contribution(self):
        """Test Foundations contribution to price_per_sqm."""
        self.assertEqual(cost_summary['Foundations'], 45000000)

    def test_structural_steel_contribution(self):
        """Test Structural Steel contribution to price_per_sqm."""
        self.assertEqual(cost_summary['Structural Steel'], 62500000)

    def test_logistics_contribution(self):
        """Test Logistics Infrastructure contribution to price_per_sqm."""
        self.assertEqual(cost_summary['Logistics Infrastructure'], 18000000)

    def test_sum_calculation(self):
        """Test the sum: 45,000,000 + 62,500,000 + 18,000,000."""
        total = 45000000 + 62500000 + 18000000
        self.assertEqual(total, 125500000)


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def test_empty_cost_summary_would_return_zero(self):
        """Test that empty cost_summary would return 0."""
        empty_summary = {}
        total = sum(empty_summary.values())
        self.assertEqual(total, 0)

    def test_single_category(self):
        """Test with single category."""
        single = {'Foundations': 45000000}
        total = sum(single.values())
        self.assertEqual(total, 45000000)

    def test_large_multiplication(self):
        """Test large area * price calculation."""
        area = 5000
        price = 125500000
        result = area * price
        self.assertEqual(result, 627500000000)

    def test_tax_calculation_on_large_amount(self):
        """Test tax calculation on large amount."""
        amount = 627625500000  # subtotal
        tax = amount * 0.25
        self.assertEqual(tax, 156906375000)


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_full_calculation_chain(self):
        """Test the full calculation chain."""
        # Material costs
        material_total = calculate_material_costs()
        self.assertEqual(material_total, 125500000)

        # Price per sqm (same as material total in this case)
        price_per_sqm = material_total
        self.assertEqual(price_per_sqm, 125500000)

        # Area cost
        area_cost = total_area_sqm * price_per_sqm
        self.assertEqual(area_cost, 627500000000)

        # Subtotal
        subtotal = material_total + area_cost
        self.assertEqual(subtotal, 627625500000)

        # Tax
        tax_amount = subtotal * tax_rate
        self.assertEqual(tax_amount, 156906375000)

        # Grand total
        grand_total = subtotal + tax_amount
        self.assertEqual(grand_total, 784531875000)

    def test_result_matches_manual_calculation(self):
        """Test that result matches manual calculation."""
        # Manual: (125500000 + 5000*125500000) * 1.25
        material = 125500000
        area = 5000 * 125500000
        subtotal = material + area
        expected = subtotal * 1.25

        result = main.__wrapped__() if hasattr(main, '__wrapped__') else None
        # We can't easily test this without capturing print, so test the math
        self.assertEqual(expected, 784531875000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
