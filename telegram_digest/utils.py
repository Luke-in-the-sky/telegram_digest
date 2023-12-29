import logging
import emoji
import re

class MyLogger():
  def __init__(self, logger_name: str):
    self.logger_name = logger_name
    self.logger = logging.getLogger(logger_name)
    self._setup_logger()

  def _setup_logger(self):
    # Remove all existing handlers
    self.logger.handlers = []

    # Create a handler (for example, logging to a file)
    handler = logging.FileHandler(f'{self.logger_name}.log', mode='w')
    formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    self.logger.addHandler(handler)
    self.logger.setLevel(logging.INFO)


# string parsing and cleaning

def clean_string(s: str) -> str:
    # Remove emojis (it's just extra tokens for the LLM that are not helpful for our usecase)
    s = emoji.replace_emoji(s, replace="")

    # Replace newlines with a single space
    s = re.sub(r"\n+", " ", s)

    # Replace multiple spaces with a single space
    s = re.sub(r"\s+", " ", s)

    return s.strip()
        
def replace_urls_with_placeholder(text: str, placeholder="<URL>") -> str:
    # Regular expression for matching URLs
    url_pattern = r'https?://\S+|www\.\S+'
    return re.sub(url_pattern, placeholder, text)