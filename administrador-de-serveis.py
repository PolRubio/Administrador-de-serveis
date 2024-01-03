import concurrent.futures
import subprocess
import time
import os
from programs_list import programs_to_run

def run_powershell(command, infinite_pids):
    infinite = False
    if isinstance(command, list):
        if isinstance(command[-1], bool) and command[-1]:
            infinite = True
            command = command[:-1]
        command = "; ".join(command)

        if infinite:
            process = subprocess.Popen(['powershell', '-Command', command], close_fds=True)
            infinite_pids.append(process.pid)
            return None  # No result for infinite programs

        result = subprocess.run(['powershell', '-Command', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()

if __name__ == "__main__":
    actual_time = time.time()
    infinite_pids = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_powershell, program, infinite_pids) for program in programs_to_run]

        non_infinite_futures = [future for future, program in zip(futures, programs_to_run) if not (isinstance(program, list) and isinstance(program[-1], bool) and program[-1])]
        print(f"Non-infinite programs: {len(non_infinite_futures)}")

        concurrent.futures.wait(non_infinite_futures)

        results = [future.result() for future in non_infinite_futures]

        for n, result in enumerate(results):
            print()
            print(f"The result of program {n} is:")
            print(f">>> {result}")
            print("===================")
           
    print(f"All non-infinite programs have finished in {time.time() - actual_time} seconds")
    print()
    print("The infinite programs are:")
    print(f">>> {pid}" for pid in infinite_pids)
