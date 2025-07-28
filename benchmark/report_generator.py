import os
import sys
import numpy as np
import pandas as pd
import re
import argparse

def parse_ab_report(file_path):
    """
    Parses an Apache Benchmark (ab) report file to extract key metrics.
    """
    metrics = {}
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            rps_match = re.search(r"Requests per second:\s+([\d\.]+)", content)
            tpr_match = re.search(r"Time per request:\s+([\d\.]+)\s+\(mean\)", content)

            if rps_match:
                metrics['Requests per Second'] = float(rps_match.group(1))
            if tpr_match:
                metrics['Time per Request (ms)'] = float(tpr_match.group(1))
    except FileNotFoundError:
        print(f"Warning: Report file not found at {file_path}", file=sys.stderr)
    return metrics

def analyze_ab_tsv(file_path):
    """
    Analyzes an 'ab' gnuplot-friendly TSV file for latency statistics.
    """
    try:
        # 'ttime' (total time) is the 5th column (index 4)
        data = np.loadtxt(file_path, skiprows=1, usecols=4, delimiter='\t')
        return {
            "Mean Latency (ms)": np.mean(data),
            "Std Dev (ms)": np.std(data),
            "95th Percentile (ms)": np.percentile(data, 95)
        }
    except Exception as e:
        print(f"Warning: Could not analyze TSV file {file_path}: {e}", file=sys.stderr)
        return {}

def parse_mem_usage(mem_str):
    """
    Converts a memory string from 'docker stats' (e.g., '55.1MiB') to float MiB.
    """
    try:
        match = re.match(r"(\d+\.?\d*)\s*([a-zA-Z]+)", mem_str)
        if not match: return 0.0
        
        value, unit = float(match.group(1)), match.group(2).upper()
        
        if 'KIB' in unit: return value / 1024
        if 'GIB' in unit: return value * 1024
        return value # Assumes MiB
    except (ValueError, AttributeError):
        return 0.0

def parse_cpu_usage(cpu_str):
    """
    Converts a CPU percentage string (e.g., '0.55%') to a float.
    """
    try:
        return float(cpu_str.replace('%', ''))
    except (ValueError, AttributeError):
        return 0.0

def analyze_resource_stats(stats_file, project_name):
    """
    Reads the stats.csv file and computes resource usage statistics.
    """
    if not os.path.exists(stats_file):
        print(f"Error: Statistics file '{stats_file}' not found.", file=sys.stderr)
        return None

    df = pd.read_csv(stats_file)
    
    # Clean service names (e.g., "src-dropper-1" -> "dropper")
    df['Name'] = df['Name'].apply(lambda x: x.replace(f"{project_name}-", "").split('-1')[0])
    
    df['MemUsageMiB'] = df['MemUsage'].apply(parse_mem_usage)
    df['CPUPerc'] = df['CPUPerc'].apply(parse_cpu_usage)
    
    resource_usage = df.groupby('Name').agg(
        AvgRAM_MiB=('MemUsageMiB', 'mean'),
        PeakRAM_MiB=('MemUsageMiB', 'max'),
        AvgCPU_Perc=('CPUPerc', 'mean'),
        PeakCPU_Perc=('CPUPerc', 'max')
    ).reset_index()
    
    return resource_usage

def main(args):
    """
    Main function to generate and print the consolidated report.
    """
    # --- 1. Performance Report ---
    print("\n" + "="*65)
    print(" " * 18 + "PERFORMANCE BENCHMARK SUMMARY")
    print("="*65)
    
    test_cases = {
        "Standard Payload": ("standard_report", "standard_data"),
        "Secure Payload": ("secure_report", "secure_data")
    }

    num_loops = len([f for f in os.listdir(args.results_dir) if f.startswith('standard_report')])
    if num_loops == 0:
        print("No performance report files found. Skipping performance analysis.", file=sys.stderr)
    else:
        for name, (report_prefix, tsv_prefix) in test_cases.items():
            all_main_metrics = [parse_ab_report(os.path.join(args.results_dir, f"{report_prefix}_{i}.txt")) for i in range(1, num_loops + 1)]
            all_stats = [analyze_ab_tsv(os.path.join(args.results_dir, f"{tsv_prefix}_{i}.tsv")) for i in range(1, num_loops + 1)]

            avg_main_metrics = {k: np.mean([d[k] for d in all_main_metrics if k in d]) for k in all_main_metrics[0]}
            avg_stats = {k: np.mean([d[k] for d in all_stats if k in d]) for k in all_stats[0]}

            print(f"\n--- Average Results for: {name} ({num_loops} runs) ---")
            for key, value in {**avg_main_metrics, **avg_stats}.items():
                print(f"{key:<25}: {value:.2f}")

    # --- 2. Resource Usage Report ---
    print("\n" + "="*65)
    print(" " * 20 + "RESOURCE USAGE ANALYSIS")
    print("="*65)

    resource_df = analyze_resource_stats(args.stats_file, args.project_name)
    
    if resource_df is not None:
        print(resource_df.to_string(index=False))
    else:
        print("Could not generate resource usage report.")
        
    print("="*65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a consolidated benchmark report.")
    parser.add_argument('--results-dir', type=str, required=True, help="Path to the directory with performance results.")
    parser.add_argument('--stats-file', type=str, required=True, help="Path to the resource stats CSV file.")
    parser.add_argument('--project-name', type=str, default='src', help="The project name used in docker-compose.")
    args = parser.parse_args()
    main(args)