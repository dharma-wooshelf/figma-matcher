
def match_stub(figma, web):
    issues = []
    f = figma["elements"][0]
    w = web["elements"][0]

    if f["box"][2] != w["box"][2]:
        issues.append({
            "type": "width-mismatch",
            "figma": f["box"][2],
            "web": w["box"][2]
        })

    if f["style"]["background"] != w["style"]["background"]:
        issues.append({
            "type": "color-mismatch",
            "figma": f["style"]["background"],
            "web": w["style"]["background"]
        })

    return {
        "score": 80,
        "issues": issues
    }
