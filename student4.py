# student4.py
import sys
import logging
from student_common import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | STUDENT | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("student4")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error("Usage: python student4.py <HOST> <PORT>")
        sys.exit(1)
    main("4", sys.argv[1], int(sys.argv[2]))
