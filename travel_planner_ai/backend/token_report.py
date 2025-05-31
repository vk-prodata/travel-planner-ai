#!/usr/bin/env python3
"""
Token Usage Report Generator
Extracts token usage information from travel planner logs.

Usage:
    python token_report.py [log_file]
    python token_report.py  # Uses today's log file
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

def extract_token_usage_from_logs(log_file_path: str) -> Dict[str, Any]:
    """Extract token usage information from log files"""
    
    token_pattern = re.compile(r'🪙 TOKEN USAGE: (\d+) total \((\d+) prompt \+ (\d+) completion\)')
    success_pattern = re.compile(r'Final token cost: (\d+) tokens')
    retry_pattern = re.compile(r'RETRY.*Wasted (\d+) tokens')
    
    total_tokens = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    successful_requests = 0
    wasted_tokens = 0
    retry_count = 0
    
    requests: List[Dict] = []
    
    try:
        with open(log_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Extract detailed token usage
                token_match = token_pattern.search(line)
                if token_match:
                    tokens = int(token_match.group(1))
                    prompt_tokens = int(token_match.group(2))
                    completion_tokens = int(token_match.group(3))
                    
                    total_tokens += tokens
                    total_prompt_tokens += prompt_tokens
                    total_completion_tokens += completion_tokens
                    
                    requests.append({
                        'line': line_num,
                        'total': tokens,
                        'prompt': prompt_tokens,
                        'completion': completion_tokens,
                        'timestamp': line.split()[0] + ' ' + line.split()[1] if len(line.split()) >= 2 else 'Unknown'
                    })
                
                # Track successful completions
                success_match = success_pattern.search(line)
                if success_match:
                    successful_requests += 1
                
                # Track wasted tokens from retries
                retry_match = retry_pattern.search(line)
                if retry_match:
                    wasted = int(retry_match.group(1))
                    wasted_tokens += wasted
                    retry_count += 1
    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file_path}")
        return {}
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return {}
    
    return {
        'log_file': log_file_path,
        'total_requests': len(requests),
        'successful_requests': successful_requests,
        'retry_count': retry_count,
        'total_tokens': total_tokens,
        'prompt_tokens': total_prompt_tokens,
        'completion_tokens': total_completion_tokens,
        'wasted_tokens': wasted_tokens,
        'effective_tokens': total_tokens - wasted_tokens,
        'requests': requests
    }

def format_report(data: Dict[str, Any]) -> str:
    """Format token usage data into a readable report"""
    
    if not data:
        return "❌ No token usage data found"
    
    report = f"""
🪙 TOKEN USAGE REPORT
{'='*50}
📁 Log File: {data['log_file']}
📊 Summary:
   • Total AI Requests: {data['total_requests']}
   • Successful Requests: {data['successful_requests']}
   • Retry Attempts: {data['retry_count']}

💰 Token Costs:
   • Total Tokens Used: {data['total_tokens']:,}
   • Prompt Tokens: {data['prompt_tokens']:,}
   • Completion Tokens: {data['completion_tokens']:,}
   • Wasted Tokens (Retries): {data['wasted_tokens']:,}
   • Effective Tokens: {data['effective_tokens']:,}

📈 Efficiency:
   • Success Rate: {(data['successful_requests'] / max(data['total_requests'], 1) * 100):.1f}%
   • Token Efficiency: {(data['effective_tokens'] / max(data['total_tokens'], 1) * 100):.1f}%
   • Avg Tokens per Request: {(data['total_tokens'] / max(data['total_requests'], 1)):.0f}

"""
    
    if data['requests']:
        report += "📋 Individual Requests:\n"
        for i, req in enumerate(data['requests'][-5:], 1):  # Show last 5 requests
            report += f"   {i}. {req['timestamp']} - {req['total']:,} tokens ({req['prompt']:,} prompt + {req['completion']:,} completion)\n"
        
        if len(data['requests']) > 5:
            report += f"   ... and {len(data['requests']) - 5} more requests\n"
    
    return report

def main():
    """Main function to generate token usage report"""
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        # Use today's log file
        today = datetime.now().strftime('%Y%m%d')
        log_file = f"travel_planner_ai/logs/travel_planner_{today}.log"
    
    # Convert to absolute path if relative
    if not Path(log_file).is_absolute():
        # Assume we're in the backend directory
        log_file = Path.cwd().parent / log_file
    
    print(f"🔍 Analyzing token usage from: {log_file}")
    data = extract_token_usage_from_logs(str(log_file))
    
    report = format_report(data)
    print(report)
    
    # Optionally save report to file
    if data and input("\n💾 Save report to file? (y/n): ").lower() == 'y':
        report_file = f"token_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✅ Report saved to: {report_file}")

if __name__ == "__main__":
    main() 