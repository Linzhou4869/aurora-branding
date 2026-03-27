#!/usr/bin/env python3
"""
Guest Satisfaction Score Analyzer
Calculates mean satisfaction score and flags critical alerts (scores < 7)
"""

def analyze_scores(scores):
    """Analyze satisfaction scores and return metrics with alerts."""
    
    # Calculate mean
    mean_score = sum(scores) / len(scores)
    
    # Find critical alerts (scores below 7)
    critical_alerts = [score for score in scores if score < 7]
    critical_indices = [i for i, score in enumerate(scores) if score < 7]
    
    # Build results
    results = {
        'scores': scores,
        'count': len(scores),
        'mean': round(mean_score, 2),
        'min': min(scores),
        'max': max(scores),
        'critical_alerts': critical_alerts,
        'critical_indices': critical_indices
    }
    
    return results

def print_report(results):
    """Print formatted analysis report."""
    print("=" * 60)
    print("GUEST SATISFACTION SCORE ANALYSIS")
    print("=" * 60)
    print(f"\nScores Analyzed: {results['scores']}")
    print(f"Total Reviews: {results['count']}")
    print(f"\n--- METRICS ---")
    print(f"Mean Satisfaction: {results['mean']}")
    print(f"Minimum Score: {results['min']}")
    print(f"Maximum Score: {results['max']}")
    
    print(f"\n--- CRITICAL ALERTS ---")
    if results['critical_alerts']:
        print(f"⚠️  WARNING: {len(results['critical_alerts'])} score(s) below threshold (< 7)")
        for idx, score in zip(results['critical_indices'], results['critical_alerts']):
            print(f"   • Review #{idx + 1}: Score = {score} [CRITICAL]")
    else:
        print("✓ No critical alerts - all scores at or above threshold")
    
    print("\n" + "=" * 60)
    return results

if __name__ == "__main__":
    # Satisfaction scores from flagship beachfront resort
    scores = [8, 9, 7, 10, 6]
    
    results = analyze_scores(scores)
    print_report(results)
    
    # Save results to file
    with open('satisfaction_metrics.txt', 'w') as f:
        f.write("GUEST SATISFACTION SCORE ANALYSIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Scores Analyzed: {results['scores']}\n")
        f.write(f"Total Reviews: {results['count']}\n\n")
        f.write("--- METRICS ---\n")
        f.write(f"Mean Satisfaction: {results['mean']}\n")
        f.write(f"Minimum Score: {results['min']}\n")
        f.write(f"Maximum Score: {results['max']}\n\n")
        f.write("--- CRITICAL ALERTS ---\n")
        if results['critical_alerts']:
            f.write(f"WARNING: {len(results['critical_alerts'])} score(s) below threshold (< 7)\n")
            for idx, score in zip(results['critical_indices'], results['critical_alerts']):
                f.write(f"   Review #{idx + 1}: Score = {score} [CRITICAL]\n")
        else:
            f.write("No critical alerts - all scores at or above threshold\n")
    
    print("\n✓ Results saved to: satisfaction_metrics.txt")
