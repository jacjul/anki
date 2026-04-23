import logging

logging.basicConfig(level=logging.DEBUG,
                    filename="app.log",
                    format= "%(asctime)s - %(levelname)s - %(message)s"
                    )

logger = logging.getLogger("app")