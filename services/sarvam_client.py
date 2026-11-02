from sarvamai import SarvamAI
from config import SARVAM_API_KEY

_client = None

def get_sarvam_client() -> SarvamAI:
    global _client
    if _client is None:
        _client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
    return _client
