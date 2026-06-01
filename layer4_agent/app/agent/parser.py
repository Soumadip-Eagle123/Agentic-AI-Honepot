import re

ACTION_REGEX = re.compile(r"Action\s*:\s*(\w+)\s*:\s*(.+)")

def parse_action(text: str):
    lines = text.split("\n")
    for line in lines:
        match = ACTION_REGEX.match(line)
        if match:
            return match.group(1), match.group(2)
    return None