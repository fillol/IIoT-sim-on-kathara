import pandas as pd
import re
import os

STATS_FILE = 'stats.csv'

def parse_mem_usage(mem_str):
    """Converts a memory string from docker stats (e.g., '55.1MiB') to megabytes."""
    try:
        # Extract numeric value and unit
        match = re.match(r"(\d+\.?\d*)\s*([a-zA-Z]+)", mem_str)
        if not match:
            return 0.0
        
        value, unit = float(match.group(1)), match.group(2).upper()
        
        # Convert to MiB
        if unit == 'KIB':
            return value / 1024
        elif unit == 'MIB':
            return value
        elif unit == 'GIB':
            return value * 1024
        else:
            return 0.0
    except Exception:
        return 0.0

def main():
    """Reads the stats CSV and calculates peak and average RAM usage per service."""
    if not os.path.exists(STATS_FILE):
        print(f"Error: Statistics file '{STATS_FILE}' not found.")
        print("Please run the './run_and_monitor.sh' script first.")
        return

    # Read the CSV data into a pandas DataFrame
    df = pd.read_csv(STATS_FILE, names=['Name', 'MemUsage'])
    
    # Clean the service names (docker compose adds prefixes)
    df['Name'] = df['Name'].apply(lambda x: x.split('-1')[0].replace('src-', ''))
    
    # Convert the memory usage string to a numeric value in MiB
    df['MemUsageMiB'] = df['MemUsage'].apply(parse_mem_usage)
    
    # Group by service name and calculate statistics
    results = df.groupby('Name')['MemUsageMiB'].agg(['max', 'mean']).reset_index()
    results.rename(columns={'max': 'PeakRAM_MiB', 'mean': 'AvgRAM_MiB'}, inplace=True)
    
    print("\n" + "="*60)
    print(" " * 15 + "RAM USAGE ANALYSIS DURING BENCHMARK")
    print("="*60)
    print(results.to_string(index=False))
    print("="*60)
    print("\nPeakRAM_MiB: The maximum memory used by the service during the test.")
    print("AvgRAM_MiB: The average memory used by the service during the test.")

if __name__ == "__main__":
    main()