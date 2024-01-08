import concurrent.futures
import subprocess
import time
import os
import psutil
from programs_list import programs_to_run
import traceback

def get_process_id(process_name):
    return subprocess.run(args=['powershell', '-Command', f'Get-Process {process_name} | Select-Object -ExpandProperty Id'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip().split("\r\n")

def run_powershell(command, infinite_pids):
    print(f"Running command: {command}")
    try:
        infinite = False
        if isinstance(command, list):
            if isinstance(command[-1], bool) and command[-1]:
                infinite = True
                command = command[:-1]
            command = "; ".join(command)

        if infinite:
            print("INFINITE PROGRAM")
            pids = get_process_id("python")
            print(f"Ids: {pids}")
            process = subprocess.Popen(['powershell', '-Command', command], close_fds=True)
            process_pid = [x for x in get_process_id('python') if x not in pids]
            infinite_pids.extend(process_pid)
            print(f"Started infinite program with PID {process_pid}")
            print(f"Command: {command}")
            print("===================")
            return None  # No result for infinite programs

        print("NON-INFINITE PROGRAM")
        print(f"Command: {command}")
        result = subprocess.run(['powershell', '-Command', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except Exception as e:
        print(f"The execution of the program {command} has failed: {e}")
        print("-------------------")
        print(traceback.format_exc())
        print("-------------------")
        return None

if __name__ == "__main__":
    actual_time = time.time()
    infinite_pids = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_powershell, program, infinite_pids) for program in programs_to_run]

        non_infinite_futures = [future for future, program in zip(futures, programs_to_run) if not (isinstance(program, list) and isinstance(program[-1], bool) and program[-1])]
        print(f"Non-infinite programs: {len(non_infinite_futures)}")
        print(f"Infinite programs: {len(futures) - len(non_infinite_futures)}")

        concurrent.futures.wait(non_infinite_futures)

        results = [future.result() for future in non_infinite_futures]

        for n, result in enumerate(results):
            print()
            print(f"The result of program {n} is:")
            print(f">>> {result}")
            print("===================")
           
    print(f"All non-infinite programs have finished in {round(time.time() - actual_time)} seconds")
    print()
    if infinite_pids:
        print("The infinite programs are:")
        print(" ".join(f">>> {pid}" for pid in infinite_pids))
