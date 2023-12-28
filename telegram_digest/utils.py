import logging

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
