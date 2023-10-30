import re
def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""
def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result

if __name__=="__main__":
    print(extract_session_id("projects/kool-chatbot-kkdm/agent/sessions/434e25ca-1e48-ab85-62f3-82eece95b18e/contexts/ongoing-order"))