# student3.py
import sys
import logging
from student_common import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | STUDENT | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("student3")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logger.error("Usage: python student3.py <HOST> <PORT>")
        sys.exit(1)
    main("3", sys.argv[1], int(sys.argv[2]))
