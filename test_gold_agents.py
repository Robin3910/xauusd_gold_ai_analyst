"""Test script for gold agents."""
from src.gold_agents.workflow import run_gold_analysis
from src.gold_agents.config import get_gold_analysts_list

print("Available Gold Analysts:")
print("=" * 60)
for a in get_gold_analysts_list():
    print(f"\n- {a['key']}")
    print(f"  Name: {a['display_name']}")
    print(f"  Focus: {a['focus']}")

print("\n" + "=" * 60)
print("Running test analysis...")

result = run_gold_analysis(
    symbol="XAUUSD",
    show_reasoning=False,
)

print(f"\nRecommendation: {result.get('recommendation', {}).get('action', 'N/A')}")
print(f"Confidence: {result.get('recommendation', {}).get('confidence', 0):.0f}%")
print(f"Risk Level: {result.get('risk_assessment', {}).get('risk_level', 'N/A')}")
print("\nTest completed successfully!")
