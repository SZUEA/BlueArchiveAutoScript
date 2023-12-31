import time

from core.utils import get_x_y
from gui.util import log


def implement(self, activity="collect_daily_power"):
    while 1:
        path1 = self.get_screen_shot_array()
        path2 = "../src/daily_task/daily_task_collect_all_bright.png"
        path3 = "../src/daily_task/daily_task_collect_all_grey.png"
        return_data1 = get_x_y(path1, path2)
        return_data2 = get_x_y(path1, path3)
        print(return_data1)
        print(return_data2)
        if return_data2[1][0] <= 1e-03:
            log.d("work reward has been collected", level=1, logger_box=self.loggerBox)
            break
        elif return_data1[1][0] <= 1e-03:
            log.d("collect work task reward", level=1, logger_box=self.loggerBox)
            self.click(return_data1[0][0], return_data1[0][1])
            time.sleep(2)
            self.click(217, 63)
            time.sleep(0.5)
            if not self.common_positional_bug_detect_method("work_task", 217, 63):
                return False
        else:
            log.d("Can't detect button", level=2, logger_box=self.loggerBox)
            return False

    if activity == "collect_daily_power":
        self.main_activity[3][1] = 1
        log.d("collect daily power task finished", level=1, logger_box=self.loggerBox)
    else:
        self.main_activity[13][1] = 1
        log.d("collect reward task finished", level=1, logger_box=self.loggerBox)
    return True
