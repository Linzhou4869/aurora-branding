#!/usr/bin/env python3
"""Simple budget calculator for construction materials."""

# Cost summary (SEK)
cost_summary = {
    'Foundations': 45000000,
    'Structural Steel': 62500000,
    'Logistics Infrastructure': 18000000
}

# Project parameters
total_area_sqm = 5000
price_per_sqm = 35000
tax_rate = 0.25


def calculate_material_costs():
    """Calculate total material costs from cost summary."""
    total = 0
    for category, cost in cost_summary.items():
        total += cost
    return total


def main():
    """Main function to calculate and display budget."""
    print("=" * 60)
    print("CONSTRUCTION BUDGET CALCULATOR")
    print("=" * 60)

    # Calculate material costs
    material_total = calculate_material_costs()

    # Calculate price_per_sqm from key categories
    price_per_sqm = (
        cost_summary['Foundations']
        + cost_summary['Structural Steel']
        + cost_summary['Logistics Infrastructure']
    )

    # Calculate area-based cost
    area_cost = total_area_sqm * price_per_sqm

    # Calculate subtotal and tax
    subtotal = material_total + area_cost
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount

    # Display results
    print("\nCost Summary:")
    for category, cost in cost_summary.items():
        print(f"  {category}: {cost:,.0f} SEK")

    print(f"\n  price_per_sqm (sum of key categories): {price_per_sqm:,.0f} SEK")
    print(f"  Area ({total_area_sqm} sqm) cost: {area_cost:,.0f} SEK")
    print(f"  Material Total: {material_total:,.0f} SEK")
    print(f"  Subtotal: {subtotal:,.0f} SEK")
    print(f"  Tax ({tax_rate * 100:.0f}%): {tax_amount:,.0f} SEK")
    print(f"  Grand Total: {grand_total:,.0f} SEK")
    print("=" * 60)

    return grand_total


if __name__ == "__main__":
    result = main()
    print(f"\nFinal Result: {result:,.0f} SEK")
