import logging
 
class LoggerUtility:
    _instance = None
 
    def __new__(cls, name=__name__, log_level=logging.DEBUG):
        if cls._instance is None:
            cls._instance = super(LoggerUtility, cls).__new__(cls)
            cls._instance._initialize_logger(name, log_level)
        return cls._instance
 
    def _initialize_logger(self, name, log_level):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
       
        # Check if the logger already has handlers to avoid adding multiple
        if not self.logger.hasHandlers():
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
 
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
 
    def get_logger(self):
        return self.logger
   
    def close(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
 
        del self.logger