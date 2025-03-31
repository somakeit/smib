from smib.common.config import config

HOW_FRESH_SMIBHID_HOST: str | None = config('HOW_FRESH_SMIBHID_HOST', default=None)
HOW_FRESH_SMIBHID_PORT: int = config('HOW_FRESH_SMIBHID_PORT', default=80, cast=int)

HOW_FRESH_SMIBHID_BASE_URL: str = f'http://{HOW_FRESH_SMIBHID_HOST}:{HOW_FRESH_SMIBHID_PORT}/api'