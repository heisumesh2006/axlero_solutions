def predict_risk(target: str, scan_type: str):
    score = 0

    if scan_type.upper() == "WEB":
        score += 20

    if "http://" in target.lower():
        score += 20

    if "https://" in target.lower():
        score += 5

    return min(score, 100)