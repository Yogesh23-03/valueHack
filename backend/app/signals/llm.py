import re
def parse_scenario(text: str):
    match = re.search(r'(\d+)\s*days?', text)
    days = int(match.group(1)) if match else 14
    return {"type": "supplier_delay", "target": "A", "days": days}
