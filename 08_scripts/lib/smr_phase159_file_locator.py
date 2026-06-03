def locate_owner_input_file():
    import os
    paths = [os.path.join(os.getcwd(),"owner_decision_input.json"),os.path.join(os.path.dirname(__file__),"..","..","..","owner_decision_input.json")]
    for p in paths:
        if os.path.exists(p):
            return {"phase159_file_locator":{"owner_input_present":True,"input_path":p,"file_found":True}}
    return {"phase159_file_locator":{"owner_input_present":False,"input_path":None,"file_found":False,"missing_input_allowed":True,"note":"No owner_decision_input.json found. All candidates remain pending_owner_review."}}
