import logging

logger = logging.getLogger("kostal-plenticore")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("/data/venus_kostal_plenticore/Energy.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.DEBUG)
