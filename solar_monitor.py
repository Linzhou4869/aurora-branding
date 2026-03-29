#!/usr/bin/env python3
"""
Solar Farm Power Output Monitor

Logs flagged timestamps where solar output falls below threshold.
Implements file locking for concurrent write safety.
Uses environment variables for configurable thresholds.

Author: OpenClaw Agent
Deploy: Ready for production use
"""

import os
import sys
import json
import fcntl
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# =============================================================================
# Configuration via Environment Variables
# =============================================================================

# Power output threshold (kW) - flag if solar output below this
LOW_OUTPUT_THRESHOLD = float(os.environ.get('LOW_OUTPUT_THRESHOLD', '100.0'))

# Irradiance threshold (W/m²) - flag if irradiance below this
LOW_IRRADIANCE_THRESHOLD = float(os.environ.get('LOW_IRRADIANCE_THRESHOLD', '200.0'))

# Solar farm capacity (kW peak)
SOLAR_CAPACITY_KW = float(os.environ.get('SOLAR_CAPACITY_KW', '500.0'))

# Base load (kW)
BASE_LOAD_KW = float(os.environ.get('BASE_LOAD_KW', '150.0'))

# Battery State of Charge (0.0 - 1.0)
BATTERY_SOC = float(os.environ.get('BATTERY_SOC', '0.85'))

# Battery degradation rate per cycle
DEGRADATION_RATE = float(os.environ.get('DEGRADATION_RATE', '0.012'))

# STC Irradiance (W/m²)
STC_IRRADIANCE = float(os.environ.get('STC_IRRADIANCE', '1000.0'))

# File paths
STATUS_FILE = os.environ.get('STATUS_FILE', 'solar_status.json')
LOG_FILE = os.environ.get('LOG_FILE', 'solar_monitor.log')
LOCK_FILE = os.environ.get('LOCK_FILE', 'solar_monitor.lock')

# Open-Meteo API endpoint
API_URL = os.environ.get(
    'OPEN_METEO_URL',
    'https://api.open-meteo.com/v1/forecast'
)

# Site coordinates
LATITUDE = float(os.environ.get('SITE_LATITUDE', '57.7826'))
LONGITUDE = float(os.environ.get('SITE_LONGITUDE', '14.1618'))

# Forecast days
FORECAST_DAYS = int(os.environ.get('FORECAST_DAYS', '3'))

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# File Locking Context Manager
# =============================================================================

@contextmanager
def file_lock(lock_path: str):
    """
    Acquire an exclusive file lock to prevent race conditions.
    
    Uses fcntl.flock() for POSIX-compliant locking.
    Automatically releases lock when context exits.
    
    Args:
        lock_path: Path to the lock file
        
    Yields:
        Lock file handle
    """
    lock_fd = None
    try:
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        logger.debug(f"Acquired lock: {lock_path}")
        yield lock_fd
    finally:
        if lock_fd:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            logger.debug(f"Released lock: {lock_path}")


# =============================================================================
# Data Fetching
# =============================================================================

def fetch_solar_forecast(
    latitude: float,
    longitude: float,
    days: int = 3
) -> Optional[dict]:
    """
    Fetch solar radiation forecast from Open-Meteo API.
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        days: Number of forecast days
        
    Returns:
        API response dict or None on failure
    """
    try:
        import urllib.request
        import urllib.error
        
        params = (
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&hourly=direct_radiation,diffuse_radiation,shortwave_radiation"
            f"&timezone=Europe/Stockholm"
            f"&forecast_days={days}"
        )
        
        url = f"{API_URL}{params}"
        logger.info(f"Fetching forecast from: {url}")
        
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            logger.info(f"Forecast fetched successfully")
            return data
            
    except urllib.error.URLError as e:
        logger.error(f"API request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching forecast: {e}")
        return None


# =============================================================================
# Power Calculation
# =============================================================================

def calculate_power_output(forecast_data: dict) -> list:
    """
    Calculate solar power output from forecast data.
    
    Args:
        forecast_data: Open-Meteo API response
        
    Returns:
        List of hourly results with power calculations
    """
    hourly = forecast_data.get('hourly', {})
    times = hourly.get('time', [])
    global_rad = hourly.get('shortwave_radiation', [])
    
    results = []
    
    for i in range(len(times)):
        irradiance = global_rad[i] if i < len(global_rad) else 0.0
        
        # Power output scales linearly with irradiance
        solar_output = (irradiance / STC_IRRADIANCE) * SOLAR_CAPACITY_KW
        
        # Net power after base load
        net_power = solar_output - BASE_LOAD_KW
        
        # Determine battery action
        if net_power < 0:
            battery_discharge = abs(net_power)
            battery_action = 'DISCHARGE'
        else:
            battery_discharge = 0.0
            battery_action = 'CHARGE/EXPORT'
        
        # Flag conditions
        is_low_output = solar_output < LOW_OUTPUT_THRESHOLD
        is_low_irradiance = irradiance < LOW_IRRADIANCE_THRESHOLD
        
        results.append({
            'timestamp': times[i],
            'irradiance_w_m2': irradiance,
            'solar_output_kw': round(solar_output, 2),
            'net_power_kw': round(net_power, 2),
            'battery_action': battery_action,
            'battery_discharge_kwh': round(battery_discharge, 2),
            'is_low_output': is_low_output,
            'is_low_irradiance': is_low_irradiance,
            'flagged': is_low_output  # Primary flag condition
        })
    
    return results


# =============================================================================
# Status File Management
# =============================================================================

def load_existing_status(status_path: str) -> dict:
    """Load existing status file or return empty structure."""
    try:
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load existing status: {e}")
    
    return {
        'metadata': {
            'site': {
                'latitude': LATITUDE,
                'longitude': LONGITUDE
            },
            'thresholds': {
                'low_output_kw': LOW_OUTPUT_THRESHOLD,
                'low_irradiance_w_m2': LOW_IRRADIANCE_THRESHOLD
            },
            'last_updated': None,
            'run_count': 0
        },
        'flagged_timestamps': [],
        'summary': {}
    }


def write_status_file(status_path: str, status_data: dict) -> bool:
    """
    Write status data to file with exclusive locking.
    
    Args:
        status_path: Path to status JSON file
        status_data: Data to write
        
    Returns:
        True on success, False on failure
    """
    try:
        with file_lock(LOCK_FILE):
            # Load existing to preserve history
            existing = load_existing_status(status_path)
            
            # Merge new flagged timestamps (avoid duplicates)
            existing_timestamps = set(
                f['timestamp'] for f in existing.get('flagged_timestamps', [])
            )
            
            new_flags = [
                f for f in status_data.get('flagged_timestamps', [])
                if f['timestamp'] not in existing_timestamps
            ]
            
            existing['flagged_timestamps'].extend(new_flags)
            existing['flagged_timestamps'].sort(key=lambda x: x['timestamp'])
            
            # Update metadata
            existing['metadata']['last_updated'] = datetime.utcnow().isoformat()
            existing['metadata']['run_count'] = existing['metadata'].get('run_count', 0) + 1
            existing['summary'] = status_data.get('summary', {})
            
            # Write atomically
            temp_path = f"{status_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(existing, f, indent=2)
            
            os.replace(temp_path, status_path)
            logger.info(f"Status file updated: {status_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")
        return False


# =============================================================================
# Analysis & Reporting
# =============================================================================

def generate_summary(results: list) -> dict:
    """Generate analysis summary from results."""
    flagged = [r for r in results if r['flagged']]
    low_irr = [r for r in results if r['is_low_irradiance']]
    
    # Find consecutive low irradiance periods (>4 hours)
    consecutive_periods = []
    current_streak = []
    
    for r in results:
        if r['is_low_irradiance']:
            current_streak.append(r)
        else:
            if len(current_streak) > 4:
                consecutive_periods.append({
                    'start': current_streak[0]['timestamp'],
                    'end': current_streak[-1]['timestamp'],
                    'hours': len(current_streak),
                    'avg_irradiance': sum(
                        x['irradiance_w_m2'] for x in current_streak
                    ) / len(current_streak)
                })
            current_streak = []
    
    if len(current_streak) > 4:
        consecutive_periods.append({
            'start': current_streak[0]['timestamp'],
            'end': current_streak[-1]['timestamp'],
            'hours': len(current_streak),
            'avg_irradiance': sum(
                x['irradiance_w_m2'] for x in current_streak
            ) / len(current_streak)
        })
    
    solar_outputs = [r['solar_output_kw'] for r in results]
    total_discharge = sum(r['battery_discharge_kwh'] for r in results)
    
    return {
        'total_hours_analyzed': len(results),
        'flagged_count': len(flagged),
        'flagged_percentage': round(len(flagged) / len(results) * 100, 1),
        'low_irradiance_hours': len(low_irr),
        'consecutive_low_periods': consecutive_periods,
        'power_stats': {
            'max_output_kw': max(solar_outputs),
            'min_output_kw': min(solar_outputs),
            'avg_output_kw': round(sum(solar_outputs) / len(solar_outputs), 1),
            'hours_meeting_base_load': len([
                r for r in results if r['solar_output_kw'] >= BASE_LOAD_KW
            ])
        },
        'battery_impact': {
            'total_discharge_kwh': round(total_discharge, 1),
            'estimated_cycles': round(
                total_discharge / (SOLAR_CAPACITY_KW * 0.5), 2
            ),
            'degradation_impact_pct': round(
                (total_discharge / (SOLAR_CAPACITY_KW * 0.5)) * DEGRADATION_RATE * 100, 1
            )
        },
        'generated_at': datetime.utcnow().isoformat()
    }


def print_report(results: list, summary: dict):
    """Print formatted analysis report to stdout."""
    print("\n" + "=" * 80)
    print("SOLAR FARM MONITORING REPORT")
    print("=" * 80)
    print(f"Site: {LATITUDE}°N, {LONGITUDE}°E")
    print(f"Generated: {summary['generated_at']}")
    print(f"Thresholds: Output < {LOW_OUTPUT_THRESHOLD} kW | Irradiance < {LOW_IRRADIANCE_THRESHOLD} W/m²")
    print("=" * 80)
    
    print(f"\n📊 OVERVIEW")
    print(f"  Hours analyzed: {summary['total_hours_analyzed']}")
    print(f"  Flagged slots: {summary['flagged_count']} ({summary['flagged_percentage']}%)")
    print(f"  Low irradiance hours: {summary['low_irradiance_hours']}")
    
    print(f"\n⚠️  CONSECUTIVE LOW IRRADIANCE PERIODS (>4 hours)")
    if summary['consecutive_low_periods']:
        for i, period in enumerate(summary['consecutive_low_periods'], 1):
            print(f"  Period {i}: {period['start']} to {period['end']}")
            print(f"           Duration: {period['hours']}h, Avg irradiance: {period['avg_irradiance']:.1f} W/m²")
    else:
        print("  None detected")
    
    print(f"\n📈 POWER STATISTICS")
    stats = summary['power_stats']
    print(f"  Max output: {stats['max_output_kw']} kW")
    print(f"  Min output: {stats['min_output_kw']} kW")
    print(f"  Avg output: {stats['avg_output_kw']} kW")
    print(f"  Hours meeting base load ({BASE_LOAD_KW} kW): {stats['hours_meeting_base_load']}")
    
    print(f"\n🔋 BATTERY IMPACT")
    batt = summary['battery_impact']
    print(f"  Total discharge: {batt['total_discharge_kwh']} kWh")
    print(f"  Estimated cycles: {batt['estimated_cycles']}")
    print(f"  Degradation impact: {batt['degradation_impact_pct']}%")
    
    print(f"\n📋 FLAGGED TIMESTAMPS (Output < {LOW_OUTPUT_THRESHOLD} kW)")
    flagged = [r for r in results if r['flagged']]
    for r in flagged[:20]:
        print(f"  • {r['timestamp']}: {r['solar_output_kw']} kW")
    if len(flagged) > 20:
        print(f"  ... and {len(flagged) - 20} more")
    
    print("\n" + "=" * 80)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main execution function."""
    logger.info("Solar Monitor starting...")
    logger.info(f"Configuration: LOW_OUTPUT_THRESHOLD={LOW_OUTPUT_THRESHOLD} kW, "
                f"LOW_IRRADIANCE_THRESHOLD={LOW_IRRADIANCE_THRESHOLD} W/m²")
    
    # Fetch forecast
    forecast = fetch_solar_forecast(LATITUDE, LONGITUDE, FORECAST_DAYS)
    if not forecast:
        logger.error("Failed to fetch forecast. Exiting.")
        sys.exit(1)
    
    # Calculate power output
    results = calculate_power_output(forecast)
    logger.info(f"Calculated power output for {len(results)} hours")
    
    # Generate summary
    summary = generate_summary(results)
    
    # Prepare status data
    status_data = {
        'flagged_timestamps': [
            {
                'timestamp': r['timestamp'],
                'solar_output_kw': r['solar_output_kw'],
                'irradiance_w_m2': r['irradiance_w_m2'],
                'net_power_kw': r['net_power_kw'],
                'battery_discharge_kwh': r['battery_discharge_kwh']
            }
            for r in results if r['flagged']
        ],
        'summary': summary,
        'all_results': results  # Full dataset for reference
    }
    
    # Write to status file
    status_path = Path(STATUS_FILE).resolve()
    if write_status_file(str(status_path), status_data):
        logger.info(f"Status written to: {status_path}")
    else:
        logger.error("Failed to write status file")
        sys.exit(1)
    
    # Print report
    print_report(results, summary)
    
    logger.info("Solar Monitor completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
