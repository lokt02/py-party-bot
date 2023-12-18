import logging

def log_init():
    logging.basicConfig(filename='log.txt',
                        filemode='a',
                        format='[%(asctime)s,%(msecs)d] | %(name)s | [%(levelname)s] %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

    log_info("Basic config.ini set")

def log_info(message):
    print('[INFO] ' + message)
    logging.info(message)

def log_error(message):
    print('[ERROR] ' + message)
    logging.error(message)

def log_debug(message):
    print('[DEBUG] ' + message)
    logging.debug(message)
