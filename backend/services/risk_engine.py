def analyze_target(target: str):
    score = 0
    findings = []

    if not target:
        findings.append("Invalid target")
        score += 50

    if "http://" in target:
        findings.append("Target does not use HTTPS")
        score += 20

    if "localhost" in target or "127.0.0.1" in target:
        findings.append("Local development target detected")
        score += 5

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_score": min(score, 100),
        "threat_level": level,
        "findings": findings
    }