from typing import Dict, Any, List

def merge_goaccess_reports(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not reports:
        return {}
    if len(reports) == 1:
        return reports[0]

    merged = {
        "general": {
            "total_requests": 0,
            "valid_requests": 0,
            "unique_visitors": 0,
            "bandwidth": 0
        },
        "visitors": {"data": []},
        "hours": {"data": []},
        "requests": {"data": []},
        "hosts": {"data": []},
        "status_codes": {"data": []},
        "browsers": {"data": []},
        "os": {"data": []}
    }

    agg = {
        "visitors": {},
        "hours": {},
        "requests": {},
        "hosts": {},
        "status_codes": {},
        "browsers": {},
        "os": {}
    }

    for r in reports:
        if not r: continue
        gen = r.get("general", {})
        merged["general"]["total_requests"] += gen.get("total_requests", 0)
        merged["general"]["valid_requests"] += gen.get("valid_requests", 0)
        merged["general"]["unique_visitors"] += gen.get("unique_visitors", 0)
        merged["general"]["bandwidth"] += gen.get("bandwidth", 0)

        for key in agg.keys():
            for item in r.get(key, {}).get("data", []):
                k = item.get("data")
                if not k:
                    continue
                if k not in agg[key]:
                    agg[key][k] = {"data": k, "hits": {"count": 0}, "visitors": {"count": 0}, "bw": {"count": 0}}

                if "hits" in item:
                    agg[key][k]["hits"]["count"] += item["hits"].get("count", 0)
                if "visitors" in item:
                    agg[key][k]["visitors"]["count"] += item["visitors"].get("count", 0)
                if "bw" in item:
                    agg[key][k]["bw"]["count"] += item["bw"].get("count", 0)

    for key in agg.keys():
        sorted_data = sorted(agg[key].values(), key=lambda x: x["hits"]["count"], reverse=True)
        merged[key]["data"] = sorted_data

    return merged
