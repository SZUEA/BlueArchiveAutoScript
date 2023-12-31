import sys
import threading
import time

import numpy as np
import uiautomator2 as u2
from qfluentwidgets import qconfig

import module
from core.scheduler import Scheduler
from core.setup import Setup
from core.utils import kmp, get_x_y
from debug.debugger import start_debugger
from gui.components.logger_box import LoggerBox
from gui.util import log
from gui.util.config import conf
sys.stderr = open('error.log', 'w+', encoding='utf-8')

from debug.debugger import start_debugger

class Main(Setup):

    def __init__(self, logger_box: LoggerBox = None):
        super().__init__()
        self.unknown_ui_page_count = None
        self.io_err_solved_count = 0
        self.io_err_count = 0
        self.io_err_rate = 10
        self.loggerBox = logger_box
        self.flag_run = False
        self.click_interval = 0.5
        self._server_record = ''
        self._first_started = True
        self.connection = None
        self.activity_name_list = self.main_activity.copy()
        for i in range(0, len(self.main_activity)):
            self.main_activity[i] = [self.main_activity[i], 0]
        self.common_task_count = [(10, 2, 10),(11, 3, 10)]  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(普通)打k次
        self.hard_task_count = [(1, 3, 3), (3, 3, 3)]  # **可设置参数 每个元组表示(i,j,k)表示 第i任务第j关(困难)打k次
        self.common_task_status = np.full(len(self.common_task_count), False, dtype=bool)
        self.hard_task_status = np.full(len(self.hard_task_count), False, dtype=bool)
        self.scheduler = Scheduler()
        start_debugger()

    def _init_emulator(self) -> bool:
        # noinspection PyBroadException
        try:
            server = qconfig.get(conf.server)
            self.package_name = 'com.RoamingStar.BlueArchive' \
                if server == '官服' else 'com.RoamingStar.BlueArchive.bilibili'
            if not self._first_started and self._server_record == server:
                return True
            # url = "com.RoamingStar.BlueArchive/com.yostar.sdk.bridge.YoStarUnityPlayerActivity"
            # emulator_path = qconfig.get(conf.emulatorPath)
            # if emulator_path:
            #     log.d("Emulator path: " + emulator_path, level=1, logger_box=self.loggerBox)
            #     log.d("Emulator is starting...", level=1, logger_box=self.loggerBox)
            #     subprocess.run(['start', emulator_path, '-avd', 'Pixel_2_API_29', '-port', '7555'])
            #     # time.sleep(10)
            #     log.d("Emulator has been started.", level=1, logger_box=self.loggerBox)

            self.unknown_ui_page_count = 0
            self.connection = u2.connect()
            self.connection.app_start(self.package_name)
            t = self.connection.window_size()
            log.d("Screen Size  " + str(t), level=1, logger_box=self.loggerBox)
            if (t[0] == 1280 and t[1] == 720) or (t[1] == 1280 and t[0] == 720):
                log.d("Screen Size Fitted", level=1, logger_box=self.loggerBox)
            else:
                log.d("Screen Size unfitted", level=4, logger_box=self.loggerBox)
                self.flag_run = False
                return False
            self._first_started = False
            self._server_record = server
            return True
        except Exception as e:
            log.d(e, level=3, logger_box=self.loggerBox)
            self.flag_run = False
            return False

    def send(self, msg):
        # try:
        if msg == "start":
            self.start_instance()
        elif msg == "stop":
            self.flag_run = False

    #         except Exception as e:

    #             log.d(e, level=3, logger_box=self.loggerBox)
    #             self.flag_run = False

    def click(self, x, y):  # 点击屏幕（x，y）处
        self.connection.click(x, y)
        self.set_click_time()
        log.d("Click :(" + str(x) + " " + str(y) + ")" + " click_time = " + str(round(self.click_time, 3)), level=1,
              logger_box=self.loggerBox)

    def change_acc_auto(self):  # 战斗时自动开启3倍速和auto
        img1 = self.get_screen_shot_array()
        acc_r_ave = img1[625][1196][0] // 3 + img1[625][1215][0] // 3 + img1[625][1230][0] // 3
        print(acc_r_ave)
        if 250 <= acc_r_ave <= 260:
            log.d("CHANGE acceleration phase from 2 to 3", level=1, logger_box=self.loggerBox)
            self.click(1215, 625)
        elif 0 <= acc_r_ave <= 60:
            log.d("ACCELERATION phase 3", level=1, logger_box=self.loggerBox)
        elif 140 <= acc_r_ave <= 180:
            log.d("CHANGE acceleration phase from 1 to 3", level=1, logger_box=self.loggerBox)
            self.click(1215, 625)
            self.click(1215, 625)
        else:
            log.d("CAN'T DETECT acceleration BUTTON", level=2, logger_box=self.loggerBox)

        auto_r_ave = img1[677][1171][0] // 2 + img1[677][1246][0] // 2
        if 190 <= auto_r_ave <= 230:
            log.d("CHANGE MANUAL to auto", level=1, logger_box=self.loggerBox)
            self.click(1216, 678)
        elif 0 <= auto_r_ave <= 60:
            log.d("AUTO", level=1, logger_box=self.loggerBox)
        else:
            log.d("can't identify auto button", level=2, logger_box=self.loggerBox)
        print(auto_r_ave)

    def common_fight_practice(self):
        self.flag_run = False
        time.sleep(1)
        self.change_acc_auto()
        while 1:
            self.latest_img_array = self.get_screen_shot_array()
            path1 = "src/common_button/check_blue.png"
            path3 = "src/common_button/fail_check.png"
            return_data1 = get_x_y(self.latest_img_array, path1)
            return_data2 = get_x_y(self.latest_img_array, path3)
            if return_data1[1][0] < 1e-03 or return_data2[1][0] < 1e-03:
                if return_data1[1][0] < 1e-03:
                    log.d("fight succeeded", level=1, logger_box=self.loggerBox)
                    success = True
                    self.click(return_data1[0][0], return_data1[0][1])
                else:
                    log.d("fight failed", level=1, logger_box=self.loggerBox)
                    success = False
                    self.click(return_data2[0][0], return_data2[0][1])
                break
            else:
                self.click(767, 500)
                log.d("fighting", level=1, logger_box=self.loggerBox)
            time.sleep(2)

        threading.Thread(target=self.run, daemon=True).start()

        if not success:
            while 1:
                time.sleep(1)
                self.latest_img_array = self.get_screen_shot_array()
                path2 = "src/common_button/fail_back.png"
                return_data1 = get_x_y(self.latest_img_array, path2)
                if return_data1[1][0] < 1e-03:
                    log.d("Fail Back", level=1, logger_box=self.loggerBox)
                    self.click(return_data1[0][0], return_data1[0][1])
                    break
        else:
            self.common_positional_bug_detect_method("fight_success", 1171, 60)
            self.click(772, 657)

        time.sleep(4)
        return success

    def special_task_common_operation(self, a, b, f=True):
        special_task_lox = 1120
        special_task_loy = [180, 286, 386, 489, 564, 432, 530, 628]
        fail_cnt = 0
        difficulty_name = ["A", "B", "C", "D", "E", "F", "G", "H"]
        img_shot = self.get_screen_shot_array()
        ocr_res = self.img_ocr(img_shot)

        highest_level = 8

        for i in range(0, 3):
            if kmp(difficulty_name[i], ocr_res):
                highest_level = i + 1
                break

        if a >= highest_level:  # 肯定未通关
            log.d("UNLOCKED", level=2, logger_box=self.loggerBox)
            return True

        log.d("-------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("try to swipe to TOP page", level=1, logger_box=self.loggerBox)
        while fail_cnt <= 3:
            log.d("swipe", level=1, logger_box=self.loggerBox)
            self.connection.swipe(916, 200, 916, 460, 0.1)
            time.sleep(1)
            img_shot = self.get_screen_shot_array()
            ocr_res = self.img_ocr(img_shot)
            if kmp("A", ocr_res) == 0:
                fail_cnt += 1
                if fail_cnt <= 3:
                    log.d("TRY AGAIN", 1, logger_box=self.loggerBox)
                else:
                    log.d("FAIL to swipe to TOP page", level=2, logger_box=self.loggerBox)
                    log.d("-------------------------------------------------------------------------------", 1,
                          logger_box=self.loggerBox)
                    return False
            else:
                log.d("SUCCESSFULLY swipe to TOP page", level=1, logger_box=self.loggerBox)
                log.d("-------------------------------------------------------------------------------", 1,
                      logger_box=self.loggerBox)
                break

        if a >= 6:
            fail_cnt = 0
            log.d("-------------------------------------------------------------------------------", 1,
                  logger_box=self.loggerBox)
            log.d("try to swipe to LOWEST page", level=1, logger_box=self.loggerBox)
            while fail_cnt <= 3:
                log.d("swipe", level=1, logger_box=self.loggerBox)
                self.connection.swipe(916, 460, 916, 200, 0.1)
                time.sleep(1)
                img_shot = self.get_screen_shot_array()
                ocr_res = self.img_ocr(img_shot)
                if kmp("D", ocr_res) == 0 or kmp("A", ocr_res) != 0:
                    fail_cnt += 1
                    if fail_cnt <= 3:
                        log.d("TRY AGAIN", 1, logger_box=self.loggerBox)
                    else:
                        log.d("FAIL to swipe to LOWEST page", level=2, logger_box=self.loggerBox)
                        log.d("-------------------------------------------------------------------------------", 1,
                              logger_box=self.loggerBox)
                        return False
                else:
                    log.d("SUCCESSFULLY swipe to LOWEST page", level=1, logger_box=self.loggerBox)
                    log.d("-------------------------------------------------------------------------------", 1,
                          logger_box=self.loggerBox)
                    break

        self.click(special_task_lox, special_task_loy[a - 1])

        if self.pd_pos() == "notice":
            log.d("UNLOCKED", level=2, logger_box=self.loggerBox)
        else:
            for i in range(0, b - 1):
                self.click(1033, 297)
                if f:
                    time.sleep(0.6)
                else:
                    time.sleep(0.2)
            self.click(937, 404)
            lo = self.pd_pos()
            if lo == "charge_power":
                log.d("inadequate power , exit task", level=3, logger_box=self.loggerBox)
            elif lo == "charge_notice":
                log.d("inadequate ticket , exit task", level=3, logger_box=self.loggerBox)
            elif lo == "notice":
                self.click(767, 501)
                time.sleep(2)
            else:
                log.d("AUTO FIGHT UNLOCKED , exit task", level=3, logger_box=self.loggerBox)
        return True

    def main_to_page(self, index, path=None, name=None, any=False):

        self.to_page[7] = [[217, 940], [659, self.schedule_lo_y[self.schedule_pri[0] - 1]],
                           ["schedule", "schedule" + str(self.schedule_pri[0])]]
        procedure = self.to_page[index]
        step = 0
        if len(procedure) != 0:
            step = len(procedure[0])
        if step:
            log.d("begin main to page " + str(procedure[2][step - 1]), level=1, logger_box=self.loggerBox)
        i = 0
        times = 0
        while i != step:
            x = procedure[0][i]
            y = procedure[1][i]
            page = procedure[2][i]
            self.click(x, y)
            if self.pd_pos(path=path, name=name, anywhere=any) != page:
                if times <= 1:
                    times += 1
                    log.d("not in page " + str(page) + " , count = " + str(times), level=2, logger_box=self.loggerBox)
                elif times == 2:
                    log.d("not in page " + str(page) + " , return to main page", level=2, logger_box=self.loggerBox)
                    self.to_main_page(anywhere=any)
                    times = 0
                    i = 0
            else:
                times = 0
                i += 1

    def start_instance(self):
        if self._init_emulator():
            self.thread_starter()

    def get_screen_shot_array(self):
        try:
            screenshot = self.connection.screenshot()
            numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
            if abs(int(self.click_interval * 100) - 50) > 1e-05:
                if self.io_err_solved_count == self.io_err_rate:
                    log.d("The IOError cease to happen.", level=1, logger_box=self.loggerBox)
                    log.d("Trying reducing the screenshot interval by 0.1s.", level=1, logger_box=self.loggerBox)
                    self.click_interval -= 0.1
                    self.io_err_solved_count = 0
                    self.io_err_count = max(self.io_err_count - 1, 0)
                else:
                    self.io_err_solved_count += 1
            return numpy_array
        except Exception as e:
            log.d("The IOError happened! Trying add the screenshot interval by 0.1s.",
                  level=3, logger_box=self.loggerBox)
            if self.io_err_count >= self.io_err_rate:
                self.click_interval += 0.1
                self.io_err_count = 0
            self.io_err_count += 1
            log.d(f'{e}! Trying screenshot again...', level=3, logger_box=self.loggerBox)
            time.sleep(1 + int(self.click_interval))
            return None

    def worker(self):

        shot_time = time.time() - self.base_time
        print(shot_time)
        self.latest_img_array = self.get_screen_shot_array()
        ct = time.time()
        
        self.get_keyword_appear_time(self.img_ocr(self.latest_img_array))
        print("shot time", shot_time,"click time",self.click_time)

        locate_res = self.return_location()
        if shot_time > self.click_time:
            self.pos.insert(0, [locate_res, shot_time])
        if len(self.pos) > 2:
            print("exceed len 2", shot_time)
            self.pos.pop()

    def common_positional_bug_detect_method(self, pos, x, y, times=3, anywhere=False, path=None, name=None):
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        log.d("BEGIN DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
        cnt = 1
        t = self.pd_pos(path=path, name=name, anywhere=anywhere)
        while cnt <= times:
            if t == pos:
                log.d("SUCCESSFULLY DETECT POSITION " + pos.upper(), 1, logger_box=self.loggerBox)
                log.d("------------------------------------------------------------------------------------------------", 1,
                      logger_box=self.loggerBox)
                return True
            log.d("FAIL TIME : " + str(cnt), 2, logger_box=self.loggerBox)
            cnt += 1
            self.click(x, y)
            t = self.pd_pos(path=path, name=name, anywhere=anywhere)

        log.d("CAN'T DETECT POSITION " + pos.upper(), 3, logger_box=self.loggerBox)
        log.d("------------------------------------------------------------------------------------------------", 1,
              logger_box=self.loggerBox)
        return False



    def run(self):
        self.flag_run = True
        log.d("start getting screenshot", 1, self.loggerBox)
        while self.flag_run:
            threading.Thread(target=self.worker, daemon=True).start()
            # self.worker()
            time.sleep(self.click_interval)
            # print(f'{self.flag_run}')
            # 可设置参数 time.sleep(i) 截屏速度为i秒/次，越快程序作出反映的时间便越快，
            # 同时对电脑的性能要求也会提高，目前推荐设置为1，后续优化后可以设置更低的值
        log.d("stop getting screenshot", 1, self.loggerBox)
        print("run stop")

    def thread_starter(self):  # 不要每次点击启动都跑这个
        thread_run = threading.Thread(target=self.run, daemon=True)
        thread_run.start()
        lo = self.pd_pos(anywhere=True)
        while lo != "main_page" and lo != "notice" and lo != "main_notice":
            path = "src/skip_plot/skip_plot_button.png"
            return_data = get_x_y(self.latest_img_array, path)
            if return_data[1][0] <= 1e-03:
                log.d("AT PLOT PAGE skip plot", 1, logger_box=self.loggerBox)
                self.click(return_data[0][0], return_data[0][1])
                lo = "plot"
                break
            self.click(1236, 39)
            self.click(108, 368)
            lo = self.pd_pos(anywhere=True)
        if lo == "main_notice":
            self.click(1138, 101)
        elif lo == "notice":
            self.click(763, 500)
        log.line(self.loggerBox)
        log.d("start activities", level=1, logger_box=self.loggerBox)
        while self.flag_run:
            next_func_name = self.scheduler.heartbeat()
            if next_func_name:
                log.d(f'{next_func_name} start', level=1, logger_box=self.loggerBox)
                i = self.activity_name_list.index(next_func_name)
                if i != 14:
                    self.to_main_page()
                    self.main_to_page(i)
                if self.solve(next_func_name):
                    log.d(f'{next_func_name} finished', level=1, logger_box=self.loggerBox)
                    self.scheduler.systole(next_func_name)
                else:
                    log.d(f'{next_func_name} failed', level=3, logger_box=self.loggerBox)
                    self.flag_run = False
                self.to_main_page()
            else:
                time.sleep(2)
        print("thread_starter stop")

        # for i in range(0, len(self.main_activity)):
        #     print(self.main_activity[i][0], self.main_activity[i][1])
        #     if self.main_activity[i][1] == 0:
        #         log.line(self.loggerBox)
        #         print(self.main_activity[i][0])
        #         log.d("begin " + self.main_activity[i][0] + " task", level=1, logger_box=self.loggerBox)
        #         if i != 8 and i != 14:
        #             self.to_main_page()
        #             self.main_to_page(i)
        #         self.solve(self.main_activity[i][0])
        #         print(self.main_activity[i][0], self.main_activity[i][1])
        # count = 0
        # for i in range(0, len(self.main_activity)):
        #     if self.main_activity[i][1] == 1:
        #         count += 1
        # if count == 13:
        #     self.flag_run = False

    def pd_pos(self, path=None, name=None, anywhere=False):
        if path:
            self.latest_img_array = self.get_screen_shot_array()
            return_data = get_x_y(self.latest_img_array, path)
            print(return_data)
            if return_data[1][0] <= 1e-03:
                log.d("current_location : " + name, 1, logger_box=self.loggerBox)
                return name

        while len(self.pos) > 0 and self.pos[len(self.pos) - 1][1] < self.click_time:
            self.pos.pop()

        while 1:
            if not self.flag_run:
                return
            if len(self.pos) == 2 and self.pos[0][0] == self.pos[1][0]:
                lo = self.pos[0][0]
                self.pos.clear()
                if lo == "UNKNOWN UI PAGE":
                    if anywhere:
                        log.d("anywhere accepted", 1, logger_box=self.loggerBox)
                        return "click_anywhere"
                    elif self.unknown_ui_page_count < 20:
                        self.unknown_ui_page_count += 1
                        log.d("UNKNOWN UI PAGE COUNT:" + str(self.unknown_ui_page_count), 2,
                              logger_box=self.loggerBox)
                    elif self.unknown_ui_page_count == 20:
                        log.d("Unknown ui page", 3, logger_box=self.loggerBox)
                        self.flag_run = False
                else:
                    self.unknown_ui_page_count = 0
                    log.d("current_location : " + lo, 1, logger_box=self.loggerBox)
                    return lo
            time.sleep(1)

    def solve(self, activity) -> bool:
        try:
            return module.__dict__[activity].implement(self)
        except Exception as e:
            log.d(e, level=3, logger_box=self.loggerBox)
            self.flag_run = False
            return False

    def to_main_page(self, anywhere=False):
        self.common_positional_bug_detect_method("main_page", 1236, 39, times=7, anywhere=anywhere)


if __name__ == "__main__":
    t = Main()
    t._init_emulator()
    a = t.get_screen_shot_array()
    print(t.img_ocr(a))
#     t.get_keyword_appear_time(t.img_ocr(a))
#     print(t.return_location())


if __name__ == '__main__':
    print(time.time())
    t = Main()
    t._init_emulator()
    t.latest_img_array = t.get_screen_shot_array()
    path2 = "src/momo_talk/momo_talk2.png"
    return_data1 = get_x_y(t.latest_img_array, path2)
    print(return_data1)
    ocr_res = t.img_ocr(t.get_screen_shot_array())
    print(ocr_res)
    t.get_keyword_appear_time(ocr_res)
    print(t.return_location())
