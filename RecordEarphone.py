"""用于记录新耳机煲机时长"""
import os
import time
import json
import threading
import re
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox as mBox


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 程序所在位置
record_path = os.path.join(BASE_DIR, "record.txt")  # 煲机记录文件路径


def remake_time_human(temp_time):
    """用于将时间从秒数转化为可读性强的 x天x小时x分钟x秒
    :param temp_time: 时间（秒数）
    """
    time_msg = "%.2f秒" % temp_time
    if temp_time > 60:  # 计算分钟
        cal_time_min = int(temp_time // 60)
        cal_time_sec = temp_time - cal_time_min * 60  # 计算秒数
        time_msg = "%s分钟%.2f秒" % (cal_time_min, cal_time_sec)
        if cal_time_min > 60:  # 计算小时
            cal_time_hour = int(cal_time_min // 60)
            cal_time_min = cal_time_min - cal_time_hour * 60  # 重新计算小时
            time_msg = "%s小时%s分钟%.2f秒" % (cal_time_hour, cal_time_min, cal_time_sec)
            if cal_time_hour > 24:  # 计算天数
                cal_time_day = int(cal_time_hour // 24)
                cal_time_hour = cal_time_hour - cal_time_day * 24  # 重新计算小时
                time_msg = "%s天%s小时%s分钟%.2f秒" % (cal_time_day, cal_time_hour, cal_time_min, cal_time_sec)
    return time_msg

def remake_time_human2(temp_time):
    """用于将时间从秒数转化为可读性强的 x天x小时x分钟x秒,本方法最多显示到小时数
    :param temp_time: 时间（秒数）
    """
    time_msg = "%.2f秒" % temp_time
    if temp_time > 60:  # 计算分钟
        cal_time_min = int(temp_time // 60)
        cal_time_sec = temp_time - cal_time_min * 60  # 计算秒数
        time_msg = "%s分钟%.2f秒" % (cal_time_min, cal_time_sec)
        if cal_time_min > 60:  # 计算小时
            cal_time_hour = int(cal_time_min // 60)
            cal_time_min = cal_time_min - cal_time_hour * 60  # 重新计算小时
            time_msg = "%s小时%s分钟%.2f秒" % (cal_time_hour, cal_time_min, cal_time_sec)
    return time_msg


def remake_time_sec(temp_time):
    """用于将时间从 x天x小时x分钟x秒 转化为秒数
    :param temp_time: 时间（秒数）
    """
    time_msg = 0  # 结果
    temp_time = temp_time.replace(' ', '')  # 去除空格
    time_sec = re.search(r'([0-9\.]+)秒', temp_time)
    time_min = re.search(r'([0-9]+)分钟', temp_time)
    time_hour = re.search(r'([0-9]+)小时', temp_time)
    time_day = re.search(r'([0-9]+)天', temp_time)  # 匹配天

    if time_day:
        print(time_day)
        time_msg = time_msg + float(time_day.group(1)) * 24 * 60 * 60
    if time_hour:
        time_msg = time_msg + float(time_hour.group(1)) * 60 * 60
    if time_min:
        time_msg = time_msg + float(time_min.group(1)) * 60
    if time_sec:
        time_msg = time_msg + float(time_sec.group(1))
    return time_msg


class MainPage(object):
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("耳机煲机记录程序")
        self.record = {}  # 用于记录煲机记录信息
        self.time_start = 0  # 开始计时时间
        self.time_ago = 0  # 过去计时时间
        self.timer_flag = False  # 计时器运行标志 True运行
        self.createPage()
        self.win.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.win.mainloop()

    def createPage(self):
        # 设置窗口大小
        winWidth = 600
        winHeight = 450
        # 获取屏幕分辨率
        screenWidth = self.win.winfo_screenwidth()
        screenHeight = self.win.winfo_screenheight()

        x = int((screenWidth - winWidth) / 2)
        y = int((screenHeight - winHeight) / 2)

        # 设置窗口初始位置在屏幕居中
        self.win.geometry("%sx%s+%s+%s" % (winWidth, winHeight, x, y))
        self.root = ttk.Frame(self.win)  # 主页Frame
        self.root.pack()
        f_top = ttk.Frame(self.root)  # 显示标题
        f_top.pack()
        f_option = ttk.Frame(self.root)  # 显示操作区
        f_option.pack()
        f_content = ttk.Frame(self.root)  # 记录显示区
        f_content.pack()
        ttk.Label(f_top, text="耳机煲机记录程序").pack(pady=10)
        ttk.Label(f_option, text="操作:", width=30).grid(row=0, column=0, padx=10)
        self.button_start = ttk.Button(f_option, text="开始", command=self.runNewJob)
        self.button_start.grid(row=0, column=1, padx=5)
        self.button_stop = ttk.Button(f_option, text="结束", command=self.runStopJob, state="disabled")
        self.button_stop.grid(row=0, column=2, padx=5)
        ttk.Label(f_content, text="耳机总煲机时长：").grid(row=0, column=0)
        self.label_total_msg = ttk.Label(f_content)  # 总信息
        self.label_total_msg.grid(row=0, column=1)
        ttk.Label(f_content, text="耳机本次煲机时长：").grid(row=1, column=0)
        self.label_current_msg = ttk.Label(f_content)  # 本次信息
        self.label_current_msg.grid(row=1, column=1)
        ttk.Label(f_content, text="历史记录：").grid(row=2, column=0)
        self.txt_msgList = ScrolledText(f_content, height=22, wrap=tk.WORD)  # 消息列表分区中创建文本控件
        self.txt_msgList.tag_config("green", foreground="green")  # 消息列表分区中创建标签
        self.txt_msgList.grid(row=3, column=0, columnspan=4)

        print("欢迎使用本程序，我将为您记录新耳机煲机时长以及煲机记录!")
        print("煲机记录文件位于：%s" % record_path)
        self.show_record()

    def closeWindow(self):
        """关闭窗口前自动保存进行中的计时记录"""
        self.stopJob()
        self.win.destroy()

    def show_record(self):
        """用于读取记录并输出"""
        # 读取记录
        if not os.path.exists(record_path):
            return
        with open(record_path, 'r', encoding='utf-8') as f:
            self.record = json.load(f)
        # 更新记录
        self.txt_msgList.config(state=tk.NORMAL)
        self.txt_msgList.delete("0.0", tk.END)  # 清空原内容
        try:
            self.time_ago = self.record["time_ago"]
            for item in self.record:
                if item == "time_ago":
                    self.txt_msgList.insert(tk.INSERT, "%s  :  %s\n" % ("历史记录煲机总时长", remake_time_human2(self.record[item])), 'green')
                    continue
                self.txt_msgList.insert(tk.INSERT, "%s  :  %s\n" % (item, remake_time_human2(self.record[item])))
            self.txt_msgList.see(tk.END)
            self.txt_msgList.config(state=tk.DISABLED)  # 将消息区设置为只读
        except Exception as e:
            print("记录文件似乎出问题了！请检查，异常：%s" % e)
            mBox.showerror("文件数据出错", "记录文件似乎出问题了！请检查，异常：%s" % e)

    def newJob(self):
        """用于开始新的煲机过程"""
        # print(self.record)
        self.button_stop.config(state=tk.NORMAL)
        self.button_start.config(state=tk.DISABLED)
        self.time_start = time.time()  # 开始时间
        self.timer_flag = True  # 将计时器标志位修改位True，开始计时器工作
        while self.timer_flag is True:
            cal_time = (time.time() - self.time_start)  # 计算时间差
            time_current = remake_time_human2(cal_time)  # 本次煲机时长
            time_total = remake_time_human2(cal_time + self.time_ago)
            self.label_current_msg.config(text=time_current)
            self.label_total_msg.config(text=time_total)
            time.sleep(1)

    def runNewJob(self):
        """创建子线程执行实际函数"""
        t = threading.Thread(target=self.newJob)
        t.daemon = True
        t.start()

    def stopJob(self):
        """结束本次耳机煲机"""
        # print(self.record)
        # 关闭计时器
        self.timer_flag = False  # 设置计时器标志位，关闭计时器工作
        # 操作按钮控件关闭
        self.button_stop.config(state=tk.DISABLED)
        self.button_start.config(state=tk.NORMAL)
        # 避免重复点击stop造成数据出错
        if self.time_start == 0:
            return
        # 写出记录
        time_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.time_start))
        # print(time_start)
        time_current = time.time() - self.time_start  # 本次煲机时长
        self.record["time_ago"] = self.time_ago + time_current  # 更新已煲机总时长
        self.record[time_start] = time_current  # 记录煲机记录 格式为 “2021-2-2 2:01:00”: xxxxx 本次煲机秒数
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(self.record, f, ensure_ascii=False)
        # 更新显示区信息
        self.show_record()
        # 计时器状态置零
        self.time_start = 0  # 将计时器计时时间还原

    def runStopJob(self):
        t = threading.Thread(target=self.stopJob)
        t.daemon = True
        t.start()


if __name__ == '__main__':
    MainPage()

