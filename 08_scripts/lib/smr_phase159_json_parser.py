def parse_owner_decision_json(file_result):
    if not file_result.get("file_found"):
        return {"phase159_json_parser":{"parsed_ok":False,"entries":0,"decisions":[],"note":"No input file. Using default pending decisions.","mock_used":False,"fixture_used":False}}
    try:
        import json
        with open(file_result["input_path"],"r",encoding="utf-8") as fh:
            data = json.load(fh)
        return {"phase159_json_parser":{"parsed_ok":True,"entries":len(data) if isinstance(data,list) else 0,"decisions":data if isinstance(data,list) else [],"mock_used":False,"fixture_used":False}}
    except Exception as e:
        return {"phase159_json_parser":{"parsed_ok":False,"entries":0,"decisions":[],"error":str(e),"mock_used":False,"fixture_used":False}}
