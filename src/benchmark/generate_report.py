import os
import numpy as np
import re

RESULTS_DIR = '/app/results'

def parse_main_report(file_path):
    """Parses the main ab report to get human-readable metrics."""
    metrics = {}
    with open(file_path, 'r') as f:
        content = f.read()
        rps_match = re.search(r"Requests per second:\s+([\d\.]+)", content)
        tpr_match = re.search(r"Time per request:\s+([\d\.]+)\s+\(mean\)", content)
        
        if rps_match:
            metrics['Requests per Second'] = float(rps_match.group(1))
        if tpr_match:
            metrics['Time per Request (ms)'] = float(tpr_match.group(1))
            
    return metrics

def analyze_tsv_data(file_path):
    """Analyzes the gnuplot-friendly TSV file for statistical calculations."""
    try:
        data = np.loadtxt(file_path, skiprows=1, usecols=3, delimiter='\t')
        
        mean_time = np.mean(data)
        std_dev = np.std(data)
        variance = np.var(data)
        percentile_95 = np.percentile(data, 95)
        
        return {
            "Mean Processing Time (ms)": mean_time,
            "Std Deviation (ms)": std_dev,
            "Variance (ms^2)": variance,
            "95th Percentile (ms)": percentile_95
        }
    except Exception as e:
        print(f"Could not analyze TSV file {file_path}: {e}")
        return {}

def main():
    """Main function to generate and print the report."""
    print("\n" + "="*50)
    print(" " * 15 + "BENCHMARK SUMMARY")
    print("="*50)

    test_cases = {
        "Standard Payload": ("standard_report.txt", "standard_data.tsv"),
        "Secure Payload": ("secure_report.txt", "secure_data.tsv")
    }

    for name, (report_file, tsv_file) in test_cases.items():
        report_path = os.path.join(RESULTS_DIR, report_file)
        tsv_path = os.path.join(RESULTS_DIR, tsv_file)
        
        print(f"\n--- Results for: {name} ---")
        
        if os.path.exists(report_path) and os.path.exists(tsv_path):
            main_metrics = parse_main_report(report_path)
            stats = analyze_tsv_data(tsv_path)
            
            for key, value in main_metrics.items():
                print(f"{key:<25}: {value:.2f}")
            
            print("-" * 20)
            
            for key, value in stats.items():
                print(f"{key:<25}: {value:.2f}")
        else:
            print(f"Result files for '{name}' not found.")
            
    print("\n" + "="*50)


if __name__ == "__main__":
    main()