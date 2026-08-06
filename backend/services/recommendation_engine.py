def get_recommendation(finding: str):
    finding = finding.lower()

    if "https" in finding:
        return "Enable HTTPS and redirect HTTP traffic to HTTPS."

    if "local development" in finding:
        return "Review the target environment before production deployment."

    if "invalid target" in finding:
        return "Provide a valid security scan target."

    return "Review the finding and apply appropriate security controls."