import time


class Timer():

    def human_readable_time(self):
        diff = self.diff
        unit_fine = "ns"
        diff_fine = diff
        if diff/(1.e3) < 1:
            unit = " ns"
        elif (diff/1.e6 < 1):
            unit = "µs"
            diff /= 1000 # type: ignore
        elif (diff/1.e9 < 1.):
            unit = "ms"
            diff /= 1000_000 # type: ignore
            unit_fine = "µs"
            diff_fine /= 1000 # type: ignore
        elif (diff/(1.e9*60.) < 1.):
            unit = "s"
            diff /= 1000_000_000 # type: ignore
            unit_fine = "ms"
            diff_fine /= 1000_000 # type: ignore
        elif (diff/(1.e9*3600.) < 1.):
            unit = "m"
            diff /= 60_000_000_000 # type: ignore
            unit_fine = "s"
            diff_fine /= 1000_000_000 # type: ignore
        else:
            unit = "h"
            diff /= 3600_000_000_000 # type: ignore
            unit_fine = "m"
            diff_fine /= 60_000_000 # type: ignore

        hrt = f"{diff} {unit} ({diff_fine} {unit_fine})"

        return f"[{self.context}] elapsed time: {hrt}."

    def __init__(self, context: str):
        self.start = time.time_ns()
        self.context = context

    def stop(self):
        self.now = time.time_ns()
        self.diff = self.now - self.start
