import csv
import time
import subprocess
import os
from datetime import datetime
from threading import Thread

class ResourceMonitor:
    def __init__(self, container_name):
        # 수정된 경로 설정
        self.output_dir = "../resources"
        os.makedirs(self.output_dir, exist_ok=True)  # 디렉토리 생성

        self.container = container_name
        self.csv_file = os.path.join(self.output_dir, f"{self.container}_resource_usage.csv")
        self.fieldnames = [
            "timestamp (UTC)", "container",
            "cpu_percent (%)", "mem_usage (MiB)", "mem_percent (%)",
            "net_input (B)", "net_output (B)",
            "gpu_mem_usage (MiB)", "gpu_utilization (%)"
        ]
        self.monitoring = False
        self.thread = Thread(target=self.monitor_container)
        self.init_csv()

    def init_csv(self):
        """Initialize CSV file."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def start(self):
        """Start monitoring in a separate thread."""
        if not self.monitoring:
            self.monitoring = True
            self.thread.start()

    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        self.thread.join()

    def monitor_container(self):
        while self.monitoring:
            start_time = time.time()
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            docker_stats = subprocess.run(
                f"docker stats --no-stream --format "
                f"'{{{{.CPUPerc}}}},{{{{.MemUsage}}}},{{{{.MemPerc}}}},{{{{.NetIO}}}}' {self.container}",
                shell=True, capture_output=True, text=True
            ).stdout.strip().split(",")

            if len(docker_stats) < 4:
                time.sleep(1)
                continue

            gpu_ids_raw = subprocess.run(
                f"docker inspect --format='{{{{index .HostConfig.DeviceRequests 0 \"DeviceIDs\"}}}}' {self.container}",
                shell=True, capture_output=True, text=True
            ).stdout.strip()
            gpu_ids = gpu_ids_raw.strip("[]").split() or ["0"]

            gpu_stats_raw = subprocess.run(
                f"nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits",
                shell=True, capture_output=True, text=True
            ).stdout.strip()
            gpu_stats = [line.strip() for line in gpu_stats_raw.split('\n') if line.strip()]

            cpu_percent = float(docker_stats[0].strip('%')) if docker_stats[0] else 0.0
            mem_usage_str = docker_stats[1].split('/')[0].strip()
            if 'KiB' in mem_usage_str:
                mem_usage = float(mem_usage_str.replace('KiB', '')) / 1024
            elif 'MiB' in mem_usage_str:
                mem_usage = float(mem_usage_str.replace('MiB', ''))
            elif 'GiB' in mem_usage_str:
                mem_usage = float(mem_usage_str.replace('GiB', '')) * 1024
            else:
                mem_usage = 0.0

            mem_percent = float(docker_stats[2].strip('%')) if docker_stats[2] else 0.0

            try:
                net_input, net_output = map(
                    lambda x: float(x.strip().replace('k', 'e3').replace('M', 'e6').replace('G', 'e9').replace('B', '')),
                    docker_stats[3].split('/')
                )
            except ValueError:
                net_input, net_output = 0.0, 0.0

            for gpu_stat in gpu_stats:
                gpu_fields = gpu_stat.split(',')
                gpu_index = gpu_fields[0].strip()
                if gpu_index not in gpu_ids:
                    continue

                gpu_mem_usage = float(gpu_fields[1].strip()) if len(gpu_fields) > 1 else 0.0
                gpu_utilization = float(gpu_fields[2].strip()) if len(gpu_fields) > 2 else 0.0

                with open(self.csv_file, mode='a', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                    writer.writerow({
                        "timestamp (UTC)": current_time,
                        "container": f"{self.container}-GPU{gpu_index}",
                        "cpu_percent (%)": cpu_percent,
                        "mem_usage (MiB)": mem_usage,
                        "mem_percent (%)": mem_percent,
                        "net_input (B)": net_input,
                        "net_output (B)": net_output,
                        "gpu_mem_usage (MiB)": gpu_mem_usage,
                        "gpu_utilization (%)": gpu_utilization
                    })

            elapsed_time = time.time() - start_time
            if elapsed_time < 1:
                time.sleep(1 - elapsed_time)