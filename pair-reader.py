import os
import json
from datetime import datetime, timezone, timedelta

def read_pairs_by_date(date, chain_name="ETH", days=1):
    """
    Reads the pair log file for a given UTC date (or range of dates) and returns a JSON array.
    
    :param date: Date string in format YYYY-MM-DD (e.g., "2025-02-16").
    :param days: Number of days to look back (default = 1). If >1, fetches logs from `date` to `date - (days-1)`.
    :return: JSON array containing liquidity pair data from the given range.
    """
    
    chain_name = chain_name.upper()
    log_dir = os.path.join("pair_logs", chain_name)
    pairs = []

    #Convert input date to a datetime object
    start_date = datetime.strptime(date, "%Y-%m-%d")

    for i in range(days):
        target_date = start_date - timedelta(days=i) #Get past date

        file_path = os.path.join(log_dir, f"{target_date.strftime('%Y-%m-%d')}_pairs.txt")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        pairs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        print(f"Skipping malformed JSON in {file_path}: {line.strip()}")
        else:
            print(f"No log file found for {target_date.strftime('%Y-%m-%d')} in {chain_name}.")
    
    return pairs


today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

pairs_data = read_pairs_by_date(today_date)

if pairs_data:
    print(json.dumps(pairs_data, indent=4))
else:
    print("No pairs found in the given date range.")
