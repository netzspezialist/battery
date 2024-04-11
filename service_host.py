import asyncio
import sys
import logging

from logging.handlers import TimedRotatingFileHandler
from battery_service import BatteryService

if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    fileHandler = TimedRotatingFileHandler('/home/hildinger/energy/battery/log/battery.log', when='midnight', backupCount=7)
    fileHandler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)8s | %(message)s'))
    logger.addHandler(fileHandler)

    #stdout_handler = logging.StreamHandler()
    #stdout_handler.setLevel(logging.DEBUG)
    #stdout_handler.setFormatter(logging.Formatter('%(levelname)8s | %(message)s'))
    #logger.addHandler(stdout_handler)

    bmsService = BatteryService(logger)
    #inverterService = InverterService(logger)

    loop = asyncio.new_event_loop()
    try:
        loop.create_task(bmsService.start())   
        loop.run_forever()
    except (KeyboardInterrupt) as e:
        bmsService.logger.info('SystemExit caught. Stop services ...')
        bmsService.stop()

        pending = asyncio.all_tasks()
        logger.info(f'Cancelling pending tasks [{len(pending)}]')
        loop.run_until_complete(pending)
    finally:
        logger.info('Exit ...')
        loop.close()
        sys.exit(0)
