#!/usr/bin/env python3

import sys
import time
import threading
import shutil


class MultiProgressBar:
    def __init__(self):
        self.tasks = []
        self.print_lock = threading.Lock()
        self.threads =[]

    def add_task(self, name, clssobj, tb, tf, pb, pf, cp):
        """
        - name: str, name of the task
        - total_getter: function that returns total units
        - progress_getter: function that returns current progress
        - unit: string suffix like 'files', 'MB', etc.
        """
        self.tasks.append({
            'name': name,
            'obj': clssobj,
            'total_bytes': tb,
            'total_files': tf,
            'bytes_progress': pb,
            'files_progress': pf,
            'current_process': cp
        })

    def are_threads_alive(self):
        alive_threads = [t for t in self.threads if t.is_alive()]
        if not alive_threads:
            return False
        else:
            return True

    def print_progress(self, name, fract, filecount=None, process=None):
        bar_length = 30
        filled = int(bar_length * fract)
        bar = '█' * filled + '-' * (bar_length - filled)

        with self.print_lock:
            width = shutil.get_terminal_size().columns
            line = f"\033[1;34m{name:<20}\033[0m|{bar}| {(fract * 100):.2f}%    {filecount or '':<14} {process or '':<10}"
            print(line[:width])

    def clear_lines(self, n):
        for _ in range(n):
            sys.stdout.write('\x1b[1A')  # Move cursor up one line
            sys.stdout.write('\x1b[2K')  # Clear entire line
        sys.stdout.flush()

    def render(self, stop_event):
        allprog = [0] * len(self.tasks)

        for x in allprog:
            print()

        while any(v < 1 for v in allprog) and not stop_event.is_set():
            time.sleep(0.05)
            self.clear_lines(len(self.tasks))

            allprog.clear()
            for task in self.tasks:
                bp = task['bytes_progress']
                bprog = getattr(task['obj'], bp)

                bt = task['total_bytes']
                btotal = getattr(task['obj'], bt)

                fp = task['files_progress']
                fprog = getattr(task['obj'], fp)
                ft = task['total_files']
                ftotal = getattr(task['obj'], ft)
                fcount = f"file {fprog} of {ftotal}"

                cp = task['current_process']
                cproc = getattr(task['obj'], cp)

                fract = 0
                if btotal != 0:
                    fract = bprog/btotal

                allprog.append(fract)
                if fract == 1:
                    self.print_progress(task['name'], fract, fcount)
                else:
                    self.print_progress(task['name'], fract, fcount, cproc)
