from src.Party import Party
from src.Logger import log_info, log_init

if __name__ == "__main__":
    log_init()

    party = Party()
    log_info("Work started")
    party.run()