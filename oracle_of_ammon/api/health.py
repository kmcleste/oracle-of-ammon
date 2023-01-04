import os
import pathlib
import pynvml
import psutil
import sys
from typing import List

import haystack

from models import CPUUsage, MemoryUsage, GPUUsage, GPUInfo

sys.path.append(
    str(
        pathlib.Path(
            pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent, "common"
        )
    )
)
from logger import logger


def get_health_status():
    """
    This endpoint allows external systems to monitor the health of the Haystack REST API.
    """

    gpus: List[GPUInfo] = []

    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        for i in range(gpu_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_mem_total = float(info.total) / 1024 / 1024
            gpu_mem_used = None
            for proc in pynvml.nvmlDeviceGetComputeRunningProcesses(handle):
                if proc.pid == os.getpid():
                    gpu_mem_used = float(proc.usedGpuMemory) / 1024 / 1024
                    break
            gpu_info = GPUInfo(
                index=i,
                usage=GPUUsage(
                    memory_total=round(gpu_mem_total),
                    kernel_usage=pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
                    memory_used=round(gpu_mem_used)
                    if gpu_mem_used is not None
                    else None,
                ),
            )

            gpus.append(gpu_info)
    except pynvml.NVMLError:
        logger.warning("No NVIDIA GPU found.")

    p_cpu_usage = 0
    p_memory_usage = 0
    cpu_count = os.cpu_count() or 1
    p = psutil.Process()
    p_cpu_usage = p.cpu_percent() / cpu_count
    p_memory_usage = p.memory_percent()

    cpu_usage = CPUUsage(used=p_cpu_usage)
    memory_usage = MemoryUsage(used=p_memory_usage)

    return {
        "version": haystack.__version__,
        "cpu": cpu_usage,
        "memory": memory_usage,
        "gpus": gpus,
    }
