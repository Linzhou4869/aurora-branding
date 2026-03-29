#!/usr/bin/env python3
"""
Firmware Telemetry Analysis Script
Validates autonomous irrigation controller performance metrics
"""

import json
from datetime import datetime
from statistics import mean, stdev

# Telemetry data
latencies_ms = [150, 160, 210, 155, 300]
packet_losses_pct = [0.1, 0.2, 0.05, 0.1, 0.5]

# Thresholds
LATENCY_CRITICAL_THRESHOLD_MS = 200
PACKET_LOSS_CRITICAL_THRESHOLD_PCT = 0.3

def analyze_telemetry():
    """Process telemetry data and identify anomalies"""
    
    # Calculate statistics
    mean_latency = mean(latencies_ms)
    std_latency = stdev(latencies_ms) if len(latencies_ms) > 1 else 0
    min_latency = min(latencies_ms)
    max_latency = max(latencies_ms)
    
    mean_packet_loss = mean(packet_losses_pct)
    
    # Identify critical anomalies
    latency_anomalies = []
    for i, latency in enumerate(latencies_ms):
        if latency > LATENCY_CRITICAL_THRESHOLD_MS:
            latency_anomalies.append({
                "index": i,
                "latency_ms": latency,
                "severity": "CRITICAL" if latency > 250 else "WARNING"
            })
    
    packet_loss_anomalies = []
    for i, loss in enumerate(packet_losses_pct):
        if loss > PACKET_LOSS_CRITICAL_THRESHOLD_PCT:
            packet_loss_anomalies.append({
                "index": i,
                "packet_loss_pct": loss,
                "severity": "CRITICAL"
            })
    
    # Identify CORRELATED failures (latency > 200ms AND packet_loss > 0.4% simultaneously)
    CORRELATED_PACKET_LOSS_THRESHOLD_PCT = 0.4
    correlated_failures = []
    for i in range(len(latencies_ms)):
        if latencies_ms[i] > LATENCY_CRITICAL_THRESHOLD_MS and packet_losses_pct[i] > CORRELATED_PACKET_LOSS_THRESHOLD_PCT:
            correlated_failures.append({
                "index": i,
                "latency_ms": latencies_ms[i],
                "packet_loss_pct": packet_losses_pct[i],
                "severity": "CRITICAL"
            })
    
    # Determine overall health status
    health_status = "HEALTHY"
    if latency_anomalies or packet_loss_anomalies:
        if any(a["severity"] == "CRITICAL" for a in latency_anomalies + packet_loss_anomalies):
            health_status = "DEGRADED"
        else:
            health_status = "WARNING"
    
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "firmware_validation": {
            "target": "Autonomous Irrigation Controller",
            "sample_count": len(latencies_ms)
        },
        "latency_metrics": {
            "mean_ms": round(mean_latency, 2),
            "std_dev_ms": round(std_latency, 2),
            "min_ms": min_latency,
            "max_ms": max_latency,
            "threshold_ms": LATENCY_CRITICAL_THRESHOLD_MS
        },
        "packet_loss_metrics": {
            "mean_pct": round(mean_packet_loss, 3),
            "values_pct": packet_losses_pct,
            "threshold_pct": PACKET_LOSS_CRITICAL_THRESHOLD_PCT
        },
        "anomalies": {
            "latency": latency_anomalies,
            "packet_loss": packet_loss_anomalies,
            "correlated_failures": correlated_failures,
            "total_critical": len([a for a in latency_anomalies + packet_loss_anomalies if a["severity"] == "CRITICAL"]),
            "total_correlated": len(correlated_failures)
        },
        "health_status": health_status,
        "recommendation": "Firmware requires attention" if health_status != "HEALTHY" else "Firmware validated successfully"
    }
    
    return results

def main():
    results = analyze_telemetry()
    
    # Output JSON results
    print(json.dumps(results, indent=2))
    
    # Save to file
    with open("telemetry_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis complete. Results saved to telemetry_results.json")
    print(f"  Mean Latency: {results['latency_metrics']['mean_ms']} ms")
    print(f"  Critical Anomalies: {results['anomalies']['total_critical']}")
    print(f"  Health Status: {results['health_status']}")

if __name__ == "__main__":
    main()
