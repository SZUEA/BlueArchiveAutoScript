from core.utils import img_crop, kmp
import uiautomator2 as u2
import time

from gui.util import log


def implement(self):
    region_name = ["沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区"]

    lo = [[300, 267], [645, 267], [985, 267],
          [300, 413], [645, 413], [985, 413],
          [300, 531], [645, 531], [985, 531]]
    region_schedule_total_count = [7, 7, 8, 8, 8]
    cur_num = self.schedule_pri[0]
    left_change_page_x = 32
    right_change_page_x = 1247
    change_page_y = 360
    for i in range(0, len(self.schedule_pri)):
        tar_num = self.schedule_pri[i]
        log.d("begin schedule in [" + region_name[tar_num - 1] + "]", level=1, logger_box=self.loggerBox)
        while cur_num != tar_num:
            if cur_num > tar_num:
                self.connection.click(left_change_page_x, change_page_y)
                self.set_click_time()
                log.d("Click :(" + str(left_change_page_x) + " " + str(
                    change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                      logger_box=self.loggerBox)
            else:
                self.connection.click(right_change_page_x, change_page_y)
                self.set_click_time()
                log.d("Click :(" + str(right_change_page_x) + " " + str(
                    change_page_y) + ")" + " click_time = " + str(self.click_time), level=1,
                      logger_box=self.loggerBox)
            cur_lo = self.pd_pos()
            if cur_lo[0:8] != "schedule":
                log.d("unexpected page :" + cur_lo, level=3, logger_box=self.loggerBox)
                return False
            cur_num = int(cur_lo[8:])
            log.d("now in page " + cur_lo, level=1, logger_box=self.loggerBox)
        x = 1160
        y = 664
        self.click(x, y)
        if not self.common_positional_bug_detect_method("all_schedule", x, y, 2):
            log.d("not in page all schedule , return", level=3, logger_box=self.loggerBox)
            return False
        self.latest_img_array = self.get_screen_shot_array()
        img_cro = img_crop(self.latest_img_array, 126, 1167, 98, 719)
        res = self.img_ocr(img_cro)
        count = kmp("需要评级", res)
        start = region_schedule_total_count[self.schedule_pri[0] - 1] - count
        for j in range(0, start):
            x = lo[start - j - 1][0]
            y = lo[start - j - 1][1]
            self.connection.click(x, y)
            log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
                  logger_box=self.loggerBox)
            time.sleep(0.8)
            x = 640
            y = 556
            self.connection.click(640, 556)
            log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(self.click_time), level=1,
                  logger_box=self.loggerBox)
            self.set_click_time()
            if self.pd_pos() == "notice":
                self.main_activity[7][1] = 1
                log.d("task schedule finished", level=1, logger_box=self.loggerBox)
                return True
            time.sleep(3)
            self.set_click_time()
            if not self.common_positional_bug_detect_method("all_schedule", 962, 116, times=4, anywhere=True):
                return False
        self.click(680, 680)