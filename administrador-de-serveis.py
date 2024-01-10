import concurrent.futures
import subprocess
import time
import os
import psutil
import traceback
import argparse
import json

class ProgramRunner:
    def __init__(self, programs_to_run):
        self.programs_to_run = programs_to_run
        self.infinite_pids = []

    def get_process_id(self, process_name):
        return subprocess.run(args=['powershell', '-Command', f'Get-Process {process_name} | Select-Object -ExpandProperty Id'], stdout=subprocess.PIPE).stdout.decode('utf-8').strip().split("\r\n")

    def run_powershell(self, command):
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
                pids = self.get_process_id("python")
                print(f"Ids: {pids}")
                process = subprocess.Popen(['powershell', '-Command', command], close_fds=True)
                process_pid = [x for x in self.get_process_id('python') if x not in pids]
                self.infinite_pids.extend(process_pid)
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

    def run_programs(self):
        actual_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run_powershell, program) for program in self.programs_to_run]

            non_infinite_futures = [future for future, program in zip(futures, self.programs_to_run) if not (isinstance(program, list) and isinstance(program[-1], bool) and program[-1])]
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
        if self.infinite_pids:
            print("The infinite programs are:")
            print(" ".join(f">>> {pid}" for pid in self.infinite_pids))
            

def stop_infinite_programs(infinite_pids):
    # Implement logic to stop infinite programs based on their PIDs
    pass

def load_from_json(json_file):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
            programs_to_run = data.get('programs_to_run', [])
            infinite_pids = data.get('infinite_pids', [])
            return programs_to_run, infinite_pids
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
        return [], []

def save_to_json(json_file, programs_to_run, infinite_pids):
    data = {'programs_to_run': programs_to_run, 'infinite_pids': infinite_pids}
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Run and manage programs.")
    parser.add_argument("-r", "--run", action="store_true", help="Run the programs")
    parser.add_argument("-s", "--stop", action="store_true", help="Stop programs with infinite loops")
    parser.add_argument("-f", "--file", type=str, help="JSON file containing commands and PIDs")

    args = parser.parse_args()

    if args.run and args.stop:
        print("Error: Cannot run and stop programs at the same time.")
        return

    if args.file:
        programs_to_run, infinite_pids = load_from_json(args.file)
        print(f"Loaded {len(programs_to_run)} programs from {args.file}")
        print(f"Loaded {len(infinite_pids)} infinite pids from {args.file}")
    else:
        print("Error: No file specified.")
        return

    if args.run:
        program_runner = ProgramRunner(programs_to_run)
        program_runner.run_programs()
        infinite_pids.extend(program_runner.infinite_pids)
        save_to_json(args.file, programs_to_run, infinite_pids)

    if args.stop:
        stop_infinite_programs(infinite_pids)

if __name__ == "__main__":
    main()
