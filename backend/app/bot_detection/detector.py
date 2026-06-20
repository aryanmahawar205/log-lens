import re

class BotDetector:
    """
    Classifies visitors based on User-Agent string.
    Categories: human, search_engine_bot, monitoring_bot, crawler, unknown.
    """

    SEARCH_ENGINE_BOTS = [
        r'googlebot',
        r'bingbot',
        r'yandex',
        r'baiduspider',
        r'duckduckbot',
        r'slurp' # Yahoo
    ]

    CRAWLERS = [
        r'ahrefs',
        r'semrush',
        r'mj12bot',
        r'dotbot',
        r'rogerbot',
        r'bot', r'spider', r'crawler', r'scraper' # generic matchers
    ]

    MONITORING_BOTS = [
        r'pingdom',
        r'uptimerobot',
        r'statuscake',
        r'datadog',
        r'newrelic'
    ]

    HUMAN_BROWSERS = [
        r'mozilla',
        r'chrome',
        r'safari',
        r'edge',
        r'opera',
        r'firefox'
    ]

    @classmethod
    def classify(cls, user_agent: str) -> str:
        """
        Classifies a given user-agent string.
        """
        if not user_agent or user_agent == '-':
            return 'unknown'

        ua_lower = user_agent.lower()

        # Check Search Engines first (they usually contain 'bot' too)
        for pattern in cls.SEARCH_ENGINE_BOTS:
            if re.search(pattern, ua_lower):
                return 'search_engine_bot'

        # Check Monitoring tools
        for pattern in cls.MONITORING_BOTS:
            if re.search(pattern, ua_lower):
                return 'monitoring_bot'

        # Check Generic Crawlers
        for pattern in cls.CRAWLERS:
            if re.search(pattern, ua_lower):
                return 'crawler'

        # Check if it looks like a human browser
        # Be careful as many bots spoof 'Mozilla'. We rely on bots being caught by previous checks.
        for pattern in cls.HUMAN_BROWSERS:
            if re.search(pattern, ua_lower):
                return 'human'

        return 'unknown'
