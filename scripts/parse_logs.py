#!/usr/bin/env python3
"""
Simple parser for MPC benchmark logs that outputs plain text tables.
Usage: python parse_logs.py <log_directory> --prefix <prefix> [--output table.txt]
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Configuration for different benchmark types
CONFIGS = {
    "poseidon2_chains": {
        "pattern": r'poseidon2_chains-(\d+)',
        "grouping": "ℓ",
    },
    "leansig": {
        "pattern": r'leansig-(\d+)-(\d+)-(\d+)',
        "grouping": "(v, w, T)",
    },
    "leansig_prec": {
        "pattern": r'leansig_prec-(\d+)-(\d+)-(\d+)',
        "grouping": "n_σ",
    }
}

PROTOCOL_MAP = {
    "atlas": "ATLAS",
    "mascot": "MASCOT",
    "mama": "MAMA",
    "mama-party": "MAMA",
    "mal-shamir": "Mal. Shamir",
    "malicious-shamir": "Mal. Shamir",
}

DELAY_TO_D = {"1ms": 1, "10ms": 10, "100ms": 100}

@dataclass
class Result:
    protocol: str
    params: Tuple
    d: int
    prec: int
    off_time: float
    off_data: float
    com_rounds: int
    on_time: float
    on_data: float

def parse_log(filepath: Path, prefix: str) -> Optional[Result]:
    """Parse a single log file."""
    config = CONFIGS.get(prefix)
    if not config:
        return None
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract parameters from filename
    match = re.search(config["pattern"], filepath.name)
    if not match:
        return None
    params = tuple(int(g) for g in match.groups())
    
    # Extract protocol
    protocol = None
    for key, name in PROTOCOL_MAP.items():
        if key in filepath.name or f'{key}-party.x' in content:
            protocol = name
            break
    if not protocol:
        return None
    
    # Extract delay
    delay_match = re.search(r'_(1ms|10ms|100ms)_', filepath.name)
    if not delay_match:
        return None
    d = DELAY_TO_D[delay_match.group(1)]
    
    # Extract preprocessing cost (sum all operations)
    prec = 0
    prep_section = re.search(r'Actual preprocessing cost of program:(.*?)(?:Command line:|Coordination took|$)', 
                             content, re.DOTALL)
    if prep_section:
        for op in ['Triples', 'Squares', 'Bits', 'Inputs']:
            m = re.search(rf'(\d+)\s+{op}', prep_section.group(1))
            if m:
                prec += int(m.group(1))
    
    # Extract offline phase
    off_match = re.search(r'([\d.]+)\s+seconds\s+\(([\d.]+)\s+MB,\s+\d+\s+rounds\)\s+on the preprocessing/offline phase', 
                         content)
    off_time = float(off_match.group(1)) if off_match else 0.0
    off_data = float(off_match.group(2)) if off_match else 0.0
    
    # Extract online phase
    on_match = re.search(r'([\d.]+)\s+seconds\s+\(([\d.]+)\s+MB,\s+(\d+)\s+rounds\)\s+on the online phase', 
                        content)
    on_time = float(on_match.group(1)) if on_match else 0.0
    on_data = float(on_match.group(2)) if on_match else 0.0
    com_rounds = int(on_match.group(3)) if on_match else 0
    
    return Result(protocol, params, d, prec, off_time, off_data, com_rounds, on_time, on_data)

def format_num(val: float) -> str:
    """Format number for table display."""
    if val == 0:
        return "-"
    if val >= 1000:
        return str(int(val))
    elif val >= 10:
        return f"{val:.0f}"
    elif val >= 1:
        return f"{val:.2f}"
    else:
        return f"{val:.2f}"

def generate_table(results: List[Result], prefix: str) -> str:
    """Generate plain text table."""
    config = CONFIGS[prefix]
    
    # Group by params and protocol
    grouped = defaultdict(lambda: defaultdict(lambda: {}))
    for r in results:
        grouped[r.params][r.protocol][r.d] = r
    
    lines = []
    
    # Determine table type
    has_combined = (prefix == "leansig_prec")
    
    # Header
    if has_combined:
        lines.append(f"{config['grouping']:<15} Protocol      Prec.   Offline phase                         Online phase                          Combined")
        lines.append(f"{'':15} {'':13} {'':8} Time (s)                     Data(MB)  Com.rounds  Time (s)                     Data(MB)  Time (s)                     Data(MB)")
        lines.append(f"{'':15} {'':13} {'':8} d=1      d=10     d=100                          d=1      d=10     d=100                d=1      d=10     d=100")
    else:
        lines.append(f"{config['grouping']:<15} Protocol      Prec.   Offline phase                         Online phase")
        lines.append(f"{'':15} {'':13} {'':8} Time (s)                     Data(MB)  Com.rounds  Time (s)                     Data(MB)")
        lines.append(f"{'':15} {'':13} {'':8} d=1      d=10     d=100                          d=1      d=10     d=100")
    
    lines.append("-" * 140)
    
    # Data rows
    for params in sorted(grouped.keys()):
        first_row = True
        for protocol in ['MAMA', 'MASCOT', 'ATLAS', 'Mal. Shamir']:
            if protocol not in grouped[params]:
                continue
            
            d_results = grouped[params][protocol]
            
            # Get data for each delay
            r1 = d_results.get(1)
            r10 = d_results.get(10)
            r100 = d_results.get(100)
            
            # Prec (same across all delays for this protocol)
            prec = max((r.prec for r in d_results.values()), default=0)
            
            # Offline times
            off_t1 = format_num(r1.off_time) if r1 else "-"
            off_t10 = format_num(r10.off_time) if r10 else "-"
            off_t100 = format_num(r100.off_time) if r100 else "-"
            
            # Offline data (typically same for all delays)
            off_data = format_num(r1.off_data if r1 else (r10.off_data if r10 else (r100.off_data if r100 else 0)))
            
            # Com rounds (typically same for all delays)
            com_rounds = r1.com_rounds if r1 else (r10.com_rounds if r10 else (r100.com_rounds if r100 else 0))
            
            # Online times
            on_t1 = format_num(r1.on_time) if r1 else "-"
            on_t10 = format_num(r10.on_time) if r10 else "-"
            on_t100 = format_num(r100.on_time) if r100 else "-"
            
            # Online data
            on_data = format_num(r1.on_data if r1 else (r10.on_data if r10 else (r100.on_data if r100 else 0)))
            
            # Format params column
            if prefix == "poseidon2_chains":
                param_str = str(params[0]) if first_row else ""
            elif prefix == "leansig_prec":
                param_str = str(params[2]) if first_row else ""  # Use 3rd param (n_σ)
            else:  # leansig
                param_str = f"({params[0]}, {params[1]}, {params[2]})" if first_row else ""
            
            if has_combined:
                # Combined times
                comb_t1 = format_num(r1.off_time + r1.on_time) if r1 else "-"
                comb_t10 = format_num(r10.off_time + r10.on_time) if r10 else "-"
                comb_t100 = format_num(r100.off_time + r100.on_time) if r100 else "-"
                
                # Combined data
                comb_data = format_num((r1.off_data + r1.on_data) if r1 else 
                                      ((r10.off_data + r10.on_data) if r10 else 
                                       ((r100.off_data + r100.on_data) if r100 else 0)))
                
                line = f"{param_str:<15} {protocol:<13} {prec:<7} {off_t1:<8} {off_t10:<8} {off_t100:<13} {off_data:<9} {com_rounds:<11} {on_t1:<8} {on_t10:<8} {on_t100:<13} {on_data:<9} {comb_t1:<8} {comb_t10:<8} {comb_t100:<13} {comb_data}"
            else:
                line = f"{param_str:<15} {protocol:<13} {prec:<7} {off_t1:<8} {off_t10:<8} {off_t100:<13} {off_data:<9} {com_rounds:<11} {on_t1:<8} {on_t10:<8} {on_t100:<13} {on_data}"
            
            lines.append(line)
            first_row = False
        
        lines.append("")  # Blank line between parameter sets
    
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_logs.py <log_directory> --prefix <prefix> [--output table.txt]")
        print("\nAvailable prefixes:")
        for p in CONFIGS.keys():
            print(f"  - {p}")
        print("\nExamples:")
        print("  python parse_logs.py ./results --prefix poseidon2_chains")
        print("  python parse_logs.py ./results --prefix leansig --output table3.txt")
        sys.exit(1)
    
    log_dir = Path(sys.argv[1])
    prefix = None
    output_file = None
    
    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == "--prefix" and i + 1 < len(sys.argv):
            prefix = sys.argv[i + 1]
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
    
    if not prefix or prefix not in CONFIGS:
        print(f"Error: Invalid prefix. Available: {list(CONFIGS.keys())}")
        sys.exit(1)
    
    # Find log files
    log_files = [f for f in log_dir.glob("*.log") if prefix in f.name]
    log_files += [f for f in log_dir.glob("*.txt") if prefix in f.name]
    
    if not log_files:
        print(f"No log files found with prefix '{prefix}'")
        sys.exit(1)
    
    print(f"Parsing {len(log_files)} log files...")
    
    results = []
    for log_file in log_files:
        r = parse_log(log_file, prefix)
        if r:
            results.append(r)
            print(f"✓ {log_file.name}: {r.protocol}, params={r.params}, d={r.d}")
    
    if not results:
        print("No valid results found")
        sys.exit(1)
    
    print(f"\nParsed {len(results)} results")
    
    # Generate table
    table = generate_table(results, prefix)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(table)
        print(f"\nTable written to {output_file}")
    else:
        print("\n" + "=" * 120)
        print(table)
        print("=" * 120)

if __name__ == "__main__":
    main()