"""HTML Filter for logging."""

import logging
import re

class NoHTMLFilter(logging.Filter):
    """Filter out HTML and related content from logs."""
    
    def __init__(self):
        super().__init__()
        self.patterns = [
            r'<[^>]+>',  # HTML tags
            r'<script.*?</script>',  # Script tags and content
            r'<style.*?</style>',  # Style tags and content
            r'data-content-len',
            r'data-sjs',
            r'__bbox',
            r'{"require"',
            r'{"html"',
            r'instagram\.com\/rsrc\.php',
            r'static\.cdninstagram\.com',
            r'style="',
            r'class="',
        ]
        self.combined_pattern = '|'.join(self.patterns)

    def filter(self, record):
        if not hasattr(record, 'msg'):
            return True
            
        msg = str(record.msg).lower()
        
        # Skip if message matches any pattern
        if re.search(self.combined_pattern, str(record.msg), re.IGNORECASE | re.DOTALL):
            return False
            
        # Skip if message is too long (likely HTML)
        if len(str(record.msg)) > 500:
            return False
            
        return True 