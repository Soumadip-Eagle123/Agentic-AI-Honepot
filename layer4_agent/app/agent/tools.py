def stalling_excuse(context: str = "") -> str:
    return "OBSERVATION: Margaret is taking a long time to read her screen. The app is freezing."

def reveal_fake_bank_details(context: str = "") -> str:
    return "OBSERVATION: Fake Bank Details exposed: Acct: 994821034, Routing: 021000021."

known_actions = {
    "stalling_excuse": stalling_excuse,
    "reveal_fake_bank_details": reveal_fake_bank_details
}