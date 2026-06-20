import pytest
from app.bot_detection.detector import BotDetector

def test_bot_detector_search_engine():
    assert BotDetector.classify("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)") == "search_engine_bot"
    assert BotDetector.classify("Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)") == "search_engine_bot"

def test_bot_detector_crawlers():
    assert BotDetector.classify("AhrefsBot/7.0") == "crawler"
    assert BotDetector.classify("SemrushBot/7~bl") == "crawler"
    assert BotDetector.classify("random scraper") == "crawler"

def test_bot_detector_monitoring():
    assert BotDetector.classify("Pingdom.com_bot_version_1.4_(http://www.pingdom.com/)") == "monitoring_bot"

def test_bot_detector_human():
    assert BotDetector.classify("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") == "human"

def test_bot_detector_unknown():
    assert BotDetector.classify("curl/7.68.0") == "unknown"
