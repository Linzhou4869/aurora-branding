#!/usr/bin/env python3
"""
Line 4 Batch Compliance Checker
ISO 9001:2015 Clause 8.7 - Control of Nonconforming Outputs

Identifies batches where:
- Rejections exceed 5 units, OR
- Rejection rate surpasses 2.5%

Usage:
    python line4_batch_compliance_checker.py [--input DATA.json] [--output REPORT.md]
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Any

# Compliance thresholds
MAX_REJECTIONS = 5
MAX_REJECTION_RATE = 2.5  # percentage


def load_batch_data(data: Any) -> List[Dict]:
    """Load batch data from JSON string, dict, or list."""
    if isinstance(data, str):
        return json.loads(data)
    elif isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'batches' in data:
        return data['batches']
    else:
        return [data]


def check_compliance(batch: Dict) -> Dict[str, Any]:
    """
    Check a single batch against compliance thresholds.
    
    Returns:
        Dict with batch_id, compliance status, and violation details
    """
    batch_id = batch.get('batch_id', 'UNKNOWN')
    rejections = batch.get('rejections', 0)
    rate = batch.get('rate', 0.0)
    
    # Check violations
    rejection_violation = rejections > MAX_REJECTIONS
    rate_violation = rate > MAX_REJECTION_RATE
    is_compliant = not (rejection_violation or rate_violation)
    
    violations = []
    if rejection_violation:
        violations.append({
            'type': 'rejection_count',
            'threshold': MAX_REJECTIONS,
            'actual': rejections,
            'excess': rejections - MAX_REJECTIONS
        })
    if rate_violation:
        violations.append({
            'type': 'rejection_rate',
            'threshold': MAX_REJECTION_RATE,
            'actual': rate,
            'excess': round(rate - MAX_REJECTION_RATE, 2)
        })
    
    return {
        'batch_id': batch_id,
        'rejections': rejections,
        'rate': rate,
        'is_compliant': is_compliant,
        'violations': violations,
        'violation_count': len(violations)
    }


def analyze_batches(batch_data: Any) -> Dict[str, Any]:
    """
    Analyze all batches and generate compliance report.
    
    Args:
        batch_data: JSON string, list, or dict containing batch data
        
    Returns:
        Analysis results with compliant and non-compliant batches
    """
    batches = load_batch_data(batch_data)
    results = [check_compliance(batch) for batch in batches]
    
    compliant = [r for r in results if r['is_compliant']]
    non_compliant = [r for r in results if not r['is_compliant']]
    
    return {
        'timestamp': datetime.now().isoformat(),
        'total_batches': len(results),
        'compliant_count': len(compliant),
        'non_compliant_count': len(non_compliant),
        'compliance_rate': round(len(compliant) / len(results) * 100, 1) if results else 0,
        'compliant_batches': compliant,
        'non_compliant_batches': sorted(non_compliant, key=lambda x: x['violation_count'], reverse=True),
        'all_results': results
    }


def generate_markdown_report(analysis: Dict[str, Any]) -> str:
    """Generate a markdown compliance report."""
    lines = []
    lines.append("# Line 4 Batch Compliance Assessment Report")
    lines.append("")
    lines.append(f"**Generated:** {analysis['timestamp']}")
    lines.append(f"**Standard:** ISO 9001:2015 Clause 8.7")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Batches | {analysis['total_batches']} |")
    lines.append(f"| Compliant | {analysis['compliant_count']} ({analysis['compliance_rate']}%) |")
    lines.append(f"| Non-Compliant | {analysis['non_compliant_count']} |")
    lines.append("")
    lines.append("## Thresholds")
    lines.append("")
    lines.append(f"- Maximum Rejections: {MAX_REJECTIONS} units")
    lines.append(f"- Maximum Rejection Rate: {MAX_REJECTION_RATE}%")
    lines.append("")
    
    # Non-compliant batches (flagged first)
    if analysis['non_compliant_batches']:
        lines.append("---")
        lines.append("")
        lines.append("## 🔴 NON-COMPLIANT BATCHES (Action Required)")
        lines.append("")
        
        for batch in analysis['non_compliant_batches']:
            lines.append(f"### Batch {batch['batch_id']}")
            lines.append("")
            lines.append(f"| Metric | Value | Threshold | Status |")
            lines.append(f"|--------|-------|-----------|--------|")
            
            rej_status = "❌ FAIL" if batch['rejections'] > MAX_REJECTIONS else "✅ PASS"
            rate_status = "❌ FAIL" if batch['rate'] > MAX_REJECTION_RATE else "✅ PASS"
            
            lines.append(f"| Rejections | {batch['rejections']} | ≤ {MAX_REJECTIONS} | {rej_status} |")
            lines.append(f"| Rejection Rate | {batch['rate']}% | ≤ {MAX_REJECTION_RATE}% | {rate_status} |")
            lines.append("")
            lines.append(f"**Violations:** {batch['violation_count']}")
            lines.append("")
            
            for v in batch['violations']:
                lines.append(f"- {v['type'].replace('_', ' ').title()}: {v['actual']} (threshold: {v['threshold']}, excess: {v['excess']})")
            lines.append("")
            lines.append("**Required Actions (ISO 9001:2015 Clause 8.7):**")
            lines.append("- [ ] Quarantine batch inventory")
            lines.append("- [ ] Document nonconformity")
            lines.append("- [ ] Determine disposition (rework/scrap/concession)")
            lines.append("- [ ] Record authorization decision")
            lines.append("")
    
    # Compliant batches
    if analysis['compliant_batches']:
        lines.append("---")
        lines.append("")
        lines.append("## ✅ Compliant Batches")
        lines.append("")
        
        for batch in analysis['compliant_batches']:
            lines.append(f"- **{batch['batch_id']}**: {batch['rejections']} rejections ({batch['rate']}%) — No action required")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## ISO 9001:2015 Clause 8.7 Reference")
    lines.append("")
    lines.append("### 8.7 Control of Nonconforming Outputs")
    lines.append("")
    lines.append("**8.7.1** The organization shall ensure that outputs that do not conform to their requirements are identified and controlled to prevent their unintended use or delivery.")
    lines.append("")
    lines.append("The organization shall deal with nonconforming outputs by one or more of the following:")
    lines.append("- Correction (e.g., rework, repair)")
    lines.append("- Segregation, containment, return, or suspension of provision")
    lines.append("- Informing the customer")
    lines.append("- Obtaining authorization for acceptance under concession")
    lines.append("")
    lines.append("**8.7.2** The organization shall retain documented information that:")
    lines.append("- Describes the nonconformity")
    lines.append("- Describes the actions taken")
    lines.append("- Describes any concessions obtained")
    lines.append("- Identifies who authorized the decision")
    lines.append("")
    lines.append("*Generated by OpenClaw Compliance Analysis System*")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    # Default test data (Line 4 batches)
    default_data = [
        {"batch_id": "A101", "rejections": 4, "rate": 1.5},
        {"batch_id": "B202", "rejections": 8, "rate": 3.2},
        {"batch_id": "C303", "rejections": 2, "rate": 0.8}
    ]
    
    # Parse command line args
    input_data = default_data
    output_file = "line4_compliance_report.md"
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            sys.exit(0)
        # Try to load from file
        try:
            with open(sys.argv[1], 'r') as f:
                input_data = json.load(f)
        except FileNotFoundError:
            print(f"File not found: {sys.argv[1]}, using default data")
        except json.JSONDecodeError:
            print(f"Invalid JSON in {sys.argv[1]}, using default data")
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    # Run analysis
    print("Analyzing batch data...")
    analysis = analyze_batches(input_data)
    
    # Generate report
    report = generate_markdown_report(analysis)
    
    # Save report
    with open(output_file, 'w') as f:
        f.write(report)
    
    # Print summary
    print(f"\n{'='*50}")
    print("COMPLIANCE ANALYSIS COMPLETE")
    print(f"{'='*50}")
    print(f"Total Batches:      {analysis['total_batches']}")
    print(f"Compliant:          {analysis['compliant_count']} ({analysis['compliance_rate']}%)")
    print(f"Non-Compliant:      {analysis['non_compliant_count']}")
    
    if analysis['non_compliant_batches']:
        print(f"\n🔴 FLAGGED BATCHES:")
        for batch in analysis['non_compliant_batches']:
            print(f"   - {batch['batch_id']}: {len(batch['violations'])} violation(s)")
            for v in batch['violations']:
                print(f"     • {v['type']}: {v['actual']} (threshold: {v['threshold']})")
    
    print(f"\n📄 Report saved to: {output_file}")
    
    # Return exit code based on compliance
    sys.exit(0 if analysis['non_compliant_count'] == 0 else 1)


if __name__ == "__main__":
    main()
