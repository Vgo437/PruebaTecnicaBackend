import sys
import logging
from pythonjsonlogger import jsonlogger


def configurar_logging():
    """Configura logging estructurado en formato JSON para toda la aplicacion."""


    logger = logging.getLogger("api")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "service"},
    )

    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


logger = configurar_logging()