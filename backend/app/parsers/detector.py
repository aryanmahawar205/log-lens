from typing import Dict, Tuple, Optional
from app.parsers.registry import ParserRegistry

class FormatDetector:
    """
    Automatic log format detection.
    Inspects sample lines to identify the correct parser and provides confidence scores.
    """

    @classmethod
    def detect_format(cls, sample_lines: list[str]) -> Tuple[Optional[str], float]:
        """
        Detects format from sample lines.
        Returns a tuple of (parser_name, confidence_score).
        Confidence is between 0.0 and 1.0 based on percentage of successfully parsed lines.
        """
        if not sample_lines:
            return None, 0.0

        best_parser_name = None
        best_confidence = 0.0

        parsers = ParserRegistry.get_all_parsers()

        for name, parser in parsers.items():
            # Skip the fallback inference parser during detection to see if a strict match works
            if name == "UNKNOWN_FORMAT":
                continue

            successful_parses = 0
            for line in sample_lines:
                try:
                    # Ignore parsing errors for detection
                    entry = parser.parse_line(line.strip())
                    if entry is not None:
                        successful_parses += 1
                except Exception:
                    pass

            confidence = successful_parses / len(sample_lines)

            if confidence > best_confidence:
                best_confidence = confidence
                best_parser_name = name

        # We return the best matched parser only if we have some minimal confidence.
        if best_confidence > 0.0:
            return best_parser_name, best_confidence

        return "UNKNOWN_FORMAT", 0.0
