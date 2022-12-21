import logging
import logging.config

logging.config.fileConfig("src/kohlrahbi/logging.conf")
logger = logging.getLogger("kohlrahbi")
