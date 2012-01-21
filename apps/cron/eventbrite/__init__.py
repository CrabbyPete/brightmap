import logging

from eventbrite.client import EventbriteClient
from eventbrite.client import EventbriteWidgets

__version__ = '0.30'

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

eventbrite_root_logger = logging.getLogger('eventbrite')
eventbrite_root_logger.addHandler(NullHandler())
