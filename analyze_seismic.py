#!/usr/bin/env python3
"""
Seismic Load Compliance Analysis - BNBC 0.3g Threshold
Analyzes structure/floor combinations for PGA compliance
"""

import csv
import json
from datetime import datetime
from pathlib import Path

# Configuration
BNBC_PGA_THRESHOLD = 0.30  # 0.3g threshold
INPUT_FILE = Path(__file__).parent / "seismic_load_data.csv"
OUTPUT_DIR = Path(__file__).parent / "seismic_analysis"

def analyze_seismic_data():
    """Analyze seismic load data against BNBC threshold."""
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Read input data
    structures = []
    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            structures.append({
                'Structure_ID': row['Structure_ID'],
                'Floor_Level': row['Floor_Level'],
                'Calculated_PGA': float(row['Calculated_PGA(g)']),
                'Zone_Safety_Factor': float(row['Zone_Safety_Factor'])
            })
    
    # Analyze compliance
    compliant = []
    non_compliant = []
    
    for struct in structures:
        pga = struct['Calculated_PGA']
        if pga > BNBC_PGA_THRESHOLD:
            struct['Violation'] = pga - BNBC_PGA_THRESHOLD
            struct['Violation_Percent'] = ((pga - BNBC_PGA_THRESHOLD) / BNBC_PGA_THRESHOLD) * 100
            non_compliant.append(struct)
        else:
            struct['Margin'] = BNBC_PGA_THRESHOLD - pga
            compliant.append(struct)
    
    # Sort non-compliant by severity (highest PGA first)
    non_compliant.sort(key=lambda x: x['Calculated_PGA'], reverse=True)
    
    # Generate analysis log
    log_data = {
        'analysis_timestamp': datetime.now().isoformat(),
        'threshold_g': BNBC_PGA_THRESHOLD,
        'total_structures': len(structures),
        'compliant_count': len(compliant),
        'non_compliant_count': len(non_compliant),
        'compliance_rate': f"{(len(compliant)/len(structures))*100:.1f}%",
        'non_compliant_details': non_compliant,
        'compliant_details': compliant
    }
    
    # Write analysis log
    log_file = OUTPUT_DIR / "analysis_log.json"
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    # Generate summary report
    report = generate_report(log_data, non_compliant, compliant)
    report_file = OUTPUT_DIR / "compliance_summary_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Write CSV of non-compliant structures
    if non_compliant:
        nc_file = OUTPUT_DIR / "non_compliant_structures.csv"
        with open(nc_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Structure_ID', 'Floor_Level', 'Calculated_PGA(g)', 'Zone_Safety_Factor', 'Violation_g', 'Violation_%'])
            for nc in non_compliant:
                writer.writerow({
                    'Structure_ID': nc['Structure_ID'],
                    'Floor_Level': nc['Floor_Level'],
                    'Calculated_PGA(g)': nc['Calculated_PGA'],
                    'Zone_Safety_Factor': nc['Zone_Safety_Factor'],
                    'Violation_g': f"{nc['Violation']:.4f}",
                    'Violation_%': f"{nc['Violation_Percent']:.1f}"
                })
    
    return log_data, report

def generate_report(log_data, non_compliant, compliant):
    """Generate markdown summary report."""
    
    report = f"""# Seismic Load Compliance Analysis Report

**Analysis Date:** {log_data['analysis_timestamp'][:19].replace('T', ' ')}
**Standard:** BNBC (Bangladesh National Building Code)
**PGA Threshold:** {log_data['threshold_g']}g

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Structures Analyzed | {log_data['total_structures']} |
| Compliant | {log_data['compliant_count']} |
| **Non-Compliant** | **{log_data['non_compliant_count']}** |
| Compliance Rate | {log_data['compliance_rate']} |

---

## ⚠️ Non-Compliant Structures (Immediate Action Required)

The following structure/floor combinations exceed the BNBC 0.3g PGA threshold:

| Structure ID | Floor Level | Calculated PGA | Zone Safety Factor | Violation (g) | Violation (%) |
|--------------|-------------|----------------|--------------------|---------------|---------------|
"""
    
    for nc in non_compliant:
        report += f"| {nc['Structure_ID']} | {nc['Floor_Level']} | **{nc['Calculated_PGA']:.2f}g** | {nc['Zone_Safety_Factor']:.2f} | +{nc['Violation']:.4f}g | +{nc['Violation_Percent']:.1f}% |\n"
    
    report += f"""
---

## ✅ Compliant Structures

| Structure ID | Floor Level | Calculated PGA | Zone Safety Factor | Margin (g) |
|--------------|-------------|----------------|--------------------|------------|
"""
    
    for c in compliant:
        report += f"| {c['Structure_ID']} | {c['Floor_Level']} | {c['Calculated_PGA']:.2f}g | {c['Zone_Safety_Factor']:.2f} | {c['Margin']:.4f}g |\n"
    
    report += f"""
---

## Recommendations

1. **Immediate structural assessment** required for {log_data['non_compliant_count']} non-compliant structure/floor combinations
2. **Evacuation consideration** for floors exceeding threshold by >10%
3. **Retrofitting analysis** to determine remediation options
4. **Re-analysis** after any structural modifications

---

*Report generated by Seismic Load Compliance Analyzer*
*BNBC 0.3g Threshold Compliance Check*
"""
    
    return report

if __name__ == "__main__":
    log_data, report = analyze_seismic_data()
    print(f"Analysis complete: {log_data['non_compliant_count']} non-compliant structures identified")
    print(f"Output directory: {OUTPUT_DIR}")
