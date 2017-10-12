#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/ADHome")

from runserver import app as application
application.secret_key = "9\x14\x8c\xbcHY\xebC'E\xe4\x98E\x04\x08\xeb\xe8\xbe`wg\x89<\xa6"
