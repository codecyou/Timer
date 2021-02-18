"""计时器应用模块"""


import os
import time
import json
import threading
import re
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox as mBox

mutex = threading.Lock()  # 创建锁用于保障修改和写出数据安全
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 程序所在位置
record_path = os.path.join(BASE_DIR, "record_timer.txt")  # 煲机记录文件路径
# 数据格式{"current_id":$current_id, $id:{"time_start":$time_start, "cal_time":$cal_time,"title":$title,"remark":$remark},}


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
                if cal_time_day > 365:  # 计算天数
                    cal_time_year = int(cal_time_day // 365)
                    cal_time_day = cal_time_day - cal_time_year * 365  # 重新计算天数
                    time_msg = "%s年%s天%s小时%s分钟%.2f秒" % (cal_time_year, cal_time_day, cal_time_hour, cal_time_min, cal_time_sec)
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
        self.win.title("计时器")
        self.record = {}  # 用于记录煲机记录信息
        self.new_title = tk.StringVar()  # 新建计时器标题
        self.new_remark = tk.StringVar()  # 新建计时器备注
        self.timer_row = 2  # 用于布局显示label的行起始位置
        self.timer_id = None  # 计时器目前编号
        self.timer_active = []  # 用于记录当前正在计时的计时器，配合停止button使用
        self.search_key = tk.StringVar()  # 用于在计时器记录界面搜索计时器，要搜索的计时器的关键字
        self.search_mode = tk.StringVar()  # 用于在计时器记录界面搜索计时器，要搜索的计时器的模式  “title”  内容  "time"  时间
        self.search_mode.set("title")
        # 获取编号
        # 1.读取记录
        self.read_record()
        # 2.计算当前新编号
        if "current_id" not in self.record:
            self.record["current_id"] = 0
        self.timer_id = self.record["current_id"]
        self.createPage()
        self.win.protocol('WM_DELETE_WINDOW', self.closeWindow)  # 绑定窗口关闭事件，防止计时器正在工作导致数据丢失
        # self.win.iconbitmap(r'C:\Users\Pro\Desktop\fm.ico')
        self.win.mainloop()

    def closeWindow(self):
        """用来处理关闭窗口按钮在退出系统前的询问"""
        active_num = len(self.timer_active)  # 当前正在进行的计时器数
        # print(active_num)
        if active_num:
            ans = mBox.askyesno(title="Warning", message="当前还有 %s 个计时器正在工作，数据尚未保存，是否退出？" % active_num)
            if not ans:
                # 选择否/no 不退出
                return
        # 退出程序
        self.win.destroy()

    def createPage(self):
        # 设置窗口大小
        winWidth = 700
        winHeight = 550
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
        self.f_content = ttk.Frame(self.root)  # 记录显示区
        self.f_content.pack()
        ttk.Label(f_top, text="计时器").pack(pady=10)

        ttk.Label(f_option, text="编号").grid(row=0, column=0)
        ttk.Label(f_option, text="事项").grid(row=0, column=1)
        ttk.Label(f_option, text="备注").grid(row=0, column=2)
        self.label_id = ttk.Label(f_option, text=self.timer_id)
        self.label_id.grid(row=1, column=0)
        ttk.Entry(f_option, textvariable=self.new_title, width=30).grid(row=1, column=1, padx=2)
        ttk.Entry(f_option, textvariable=self.new_remark, width=30).grid(row=1, column=2, padx=2)
        self.button_start = ttk.Button(f_option, text="创建", command=self.runNewJob)
        self.button_start.grid(row=1, column=3, padx=5)

        self.label_active = ttk.Label(self.f_content, text="当前共有 %s 个计时器任务！" % len(self.timer_active))  # 展示当前计时任务个数
        self.label_active.grid(row=0, column=0, columnspan=5, pady=5)
        ttk.Button(self.f_content, text="查看历史记录", command=self.show_record).grid(row=0, column=5, pady=5)
        ttk.Label(self.f_content, text="编号").grid(row=1, column=0, padx=5)
        ttk.Label(self.f_content, text="事项").grid(row=1, column=1, padx=5)
        ttk.Label(self.f_content, text="备注").grid(row=1, column=2, padx=5)
        ttk.Label(self.f_content, text="开始时间").grid(row=1, column=3, padx=5)
        ttk.Label(self.f_content, text="已计时长").grid(row=1, column=4, padx=5)

        print("欢迎使用本程序，我将为您记录计时器事件记录!")
        print("记录文件位于：%s" % record_path)

    def read_record(self):
        """用于读取记录"""
        # 读取记录
        if not os.path.exists(record_path):
            return
        with open(record_path, 'r', encoding='utf-8') as f:
            self.record = json.load(f)

    def backPrePage(self):
        """从记录查询页面返回计时器操作页面"""
        self.root_new.pack_forget()
        self.root.pack()

    def show_record(self):
        """用于查看历史记录"""
        self.root_new = ttk.Frame(self.win)  # 记录查看页面Frame
        self.root_new.pack()
        self.root.pack_forget()  # 隐藏原root页面

        ttk.Label(self.root_new, text="计时器记录查看").grid(row=0, column=0, columnspan=3, pady=5)
        ttk.Button(self.root_new, text="返回上一页", command=self.backPrePage).grid(row=0, column=2)
        self.content = ScrolledText(self.root_new, height=35, width=95, wrap=tk.WORD)  # 创建记录展示区
        self.content.tag_config("green", foreground="green")  # 消息列表分区中创建标签
        self.content.grid(row=1, columnspan=3)
        ttk.Label(self.root_new, text="查找模式:").grid(row=2, column=0)
        ttk.Radiobutton(self.root_new, text="根据内容", value="title", variable=self.search_mode).grid(row=2, column=1)
        ttk.Radiobutton(self.root_new, text="根据时间", value="time", variable=self.search_mode).grid(row=2, column=2)

        ttk.Entry(self.root_new, textvariable=self.search_key, width=50).grid(row=3, column=0)
        ttk.Button(self.root_new, text="搜索", command=self.searchRecord).grid(row=3, column=1)
        ttk.Button(self.root_new, text="查看所有便签", command=self.showAll).grid(row=3, column=2, sticky=tk.EW)
        self.showAll()  # 显示所有信息

    def searchRecord(self):
        """用于搜索计时器记录"""
        # print(self.search_mode.get())
        # print(self.search_key.get())
        # 清空数据区
        self.content.delete("0.0", tk.END)
        # 读取记录
        self.read_record()
        record = self.record
        # 搜索匹配条件的记录
        search_key = self.search_key.get()
        result_list = []  # 用于记录搜索到的计时信息，存储计时时长
        for item_id in record:
            if item_id == "current_id":
                continue
            time_start = record[item_id]["time_start"]
            cal_time = record[item_id]["cal_time"]
            cal_time_h = remake_time_human(cal_time)
            title = record[item_id]["title"]
            remark = record[item_id]["remark"]
            msg = "编号:%s, 开始时间:%s, 计时时长:%s, 事项:%s, 备注:%s\n" % (
            item_id, time_start, cal_time_h, title, remark)
            if self.search_mode.get() == "title":
                if re.search(r"%s" % search_key, title) or re.search(r"%s" % search_key, remark):
                    result_list.append(cal_time)  # 将匹配到的符合条件的计时时长信息添加到result_list中
                    self.content.insert(tk.INSERT, msg)
            else:
                if re.search(r"%s" % search_key, time_start):
                    result_list.append(cal_time)  # 将匹配到的符合条件的计时时长信息添加到result_list中
                    self.content.insert(tk.INSERT, msg)
        # 显示搜索统计信息
        if len(result_list):
            sum_msg = sum(result_list)
            avg_msg = sum_msg / len(result_list)
            msg = "共找到 %s 条符合条件的计时任务信息，SUM: %s  ,MAX: %s  ,AVG: %s  ,MIN: %s  " % (len(result_list), remake_time_human(sum_msg), remake_time_human(max(result_list)), remake_time_human(avg_msg), remake_time_human(min(result_list)))
            self.content.insert(tk.INSERT, msg, "green")
        else:
            self.content.insert(tk.INSERT, "未找到符合条件的计时任务信息！", "green")

    def showAll(self):
        """用于显示所有计时器信息"""
        # 读取记录
        self.read_record()
        record = self.record
        # 输出信息
        self.content.delete("0.0", tk.END)
        self.content.insert(tk.INSERT, "共有 %s 个计时器历史记录！\n" % (len(record)-1), "green")  # len() - current_id 占用那一位
        for item_id in record:
            if item_id == "current_id":
                continue
            item = record[item_id]
            msg = "编号:%s, 开始时间:%s, 计时时长:%s, 事项:%s, 备注:%s\n" % (item_id, item["time_start"], remake_time_human(item["cal_time"]), item["title"], item["remark"])
            self.content.insert(tk.INSERT, msg)

    def newJob(self):
        """用于开始计时器"""
        timer_id = self.timer_id
        new_title = self.new_title.get()
        # 判断是否有输入内容,无内容输入则不创建计时器
        if (not new_title) or (not new_title.strip()):
            return
        new_remark = self.new_remark.get()
        # timer_flag = True  # 将计时器标志位修改位True，开始计时器工作
        self.timer_active.append(timer_id)  # 将当前计时器的id添加到self.timer_active列表中
        # 计时器相关信息+1
        self.timer_row += 1  # 计时器布局行号+1
        self.timer_id += 1  # 计时器编号+1
        self.label_id.config(text=self.timer_id)
        self.label_active.config(text="当前共有 %s 个计时器任务正在计时！" % len(self.timer_active))
        time_start = time.time()  # 开始时间，时间戳
        time_start_write = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_start))  # 开始时间，格式化
        cal_time = 0  # 已计时长

        # 设计布局
        label_id = ttk.Label(self.f_content, text=timer_id)
        label_id.grid(row=self.timer_row, column=0, padx=5)
        label_title = ttk.Label(self.f_content, text=new_title)
        label_title.grid(row=self.timer_row, column=1, padx=5)
        label_remark = ttk.Label(self.f_content, text=new_remark)
        label_remark.grid(row=self.timer_row, column=2, padx=5)
        label_time_start = ttk.Label(self.f_content, text=time_start_write)
        label_time_start.grid(row=self.timer_row, column=3, padx=5)
        label_cal_time = ttk.Label(self.f_content, text=cal_time)
        label_cal_time.grid(row=self.timer_row, column=4, padx=5)
        # stopJob = (lambda flag: flag = False)  # 设置计时器标志位，关闭计时器工作
        button_stop = ttk.Button(self.f_content, text="停止", command=lambda: self.stopJob(timer_id))
        button_stop.grid(row=self.timer_row, column=5, padx=5)

        # 循环计时
        # while timer_flag is True:
        while timer_id in self.timer_active:
            cal_time = (time.time() - time_start)  # 计算时间差
            cal_time_msg = remake_time_human(cal_time)  # 本次煲机时长
            label_cal_time.config(text=cal_time_msg)
            time.sleep(1)

        # 将”停止“按钮置为不可点击
        button_stop.config(state=tk.DISABLED, text="已结束")

        # 将计时记录写出到记录文件
        # 数据格式{$id:{"time_start":$time_start, "cal_time":$cal_time,"title":$title,"remark":$remark},}
        mutex.acquire()
        self.record["current_id"] = self.timer_id
        self.record[timer_id] = {"time_start": time_start_write, "cal_time": cal_time, "title": new_title, "remark": new_remark}
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(self.record, f, ensure_ascii=False)
        mutex.release()

    def runNewJob(self):
        """创建子线程执行实际函数"""
        t = threading.Thread(target=self.newJob)
        t.daemon = True
        t.start()

    def stopJob(self, timer_id):
        """用于停止计时器"""
        if timer_id in self.timer_active:
            # 将该计时器id从timer_active列表中删除
            self.timer_active.remove(timer_id)
            print("计时器id：%s 结束计时！" % timer_id)
            # 刷新label_active
            self.label_active.config(text="当前共有 %s 个计时器任务正在计时！" % len(self.timer_active))


if __name__ == '__main__':
    MainPage()
