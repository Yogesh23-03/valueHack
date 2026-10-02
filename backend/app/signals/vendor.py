def check_vendor(name: str):
    if "New Distributor" in name:
        return {"score": 32, "badge": "red", "reasons": ["Registered 4 months ago", "Two cheque-bounce cases", "Missing GST filings", "Adverse media found"]}
    return {"score": 85, "badge": "green", "reasons": ["Registered 5 years ago", "Clean legal history", "Regular GST filings"]}
