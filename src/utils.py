import logging
import sys

class KeywordFilter(logging.Filter):
    private_token = "&&&DEBUG&&&"
    def filter(self, record):
        return self.private_token in record.getMessage()
class LoggingTool:
    """
    from utils import LoggingTool
    logger = LoggingTool.get_logger(__name__)
    logger.debug(f"messages")
    """
    @staticmethod
    def get_logger(name: str, setLevel=logging.INFO):
        logger = logging.getLogger(name)
        if not logger.handlers:  # 중복 핸들러 방지
            handler = logging.StreamHandler(sys.stderr)
            # stream_handler.addFilter(KeywordFilter()) # KeywordFilter.private_token을 message에 추가
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - [%(filename)s : %(funcName)s() : %(lineno)d] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(setLevel)
        return logger
    
    @staticmethod
    def set_root_logger(setLevel=logging.INFO):
        stream_handler = logging.StreamHandler(sys.stdout)
        # stream_handler.addFilter(KeywordFilter())

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        logging.basicConfig(
            level=setLevel,
            format='%(asctime)s - %(levelname)-8s - [%(filename)s : %(funcName)s() : %(lineno)d] - %(message)s',
            handlers=[stream_handler]
        )