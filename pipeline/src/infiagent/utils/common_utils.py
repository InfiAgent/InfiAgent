import time
from functools import wraps

from .logger import get_logger

logger = get_logger()

def retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    一个重试装饰器.
    
    :param max_retries: 最大重试次数
    :param delay: 重试之间的延迟（以秒为单位）
    :param backoff: 延迟的倍数增长因子
    :param exceptions: 要捕获的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                logger.info(f"Retry func {func} for {retries} times")
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.error("retry failed due to {}".format(e), exc_info=True)
                    retries += 1
                    if retries >= max_retries:
                        raise e
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

