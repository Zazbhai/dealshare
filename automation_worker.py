import subprocess
import sys
import os
import threading
import time
from queue import Queue
from datetime import datetime

# Force unbuffered output and UTF-8 encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except:
        # Fallback if reconfigure fails
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
else:
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
    sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, 'reconfigure') else None

# Logging setup
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)
latest_logs_file = os.path.join(logs_dir, 'latest_logs.txt')
log_lock = threading.Lock()

def write_to_log(message, worker_id=None):
    """Write message to worker log file and latest_logs.txt"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}\n"
    
    with log_lock:
        # Write to latest_logs.txt (combined)
        try:
            with open(latest_logs_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"[ERROR] Failed to write to latest_logs: {e}")
        
        # Write to worker-specific log file
        if worker_id:
            worker_log_file = os.path.join(logs_dir, f'worker_{worker_id}.log')
            try:
                with open(worker_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
            except Exception as e:
                print(f"[ERROR] Failed to write to worker log: {e}")

def run_single_order(order_num):
    """Run a single order automation"""
    print(f"[DEBUG] run_single_order called for order {order_num}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, 'main.py')
    
    print(f"[DEBUG] Base directory: {base_dir}")
    print(f"[DEBUG] Main script path: {main_script}")
    print(f"[DEBUG] Main script exists: {os.path.exists(main_script)}")
    
    env = os.environ.copy()  # This already contains API_KEY, API_URL, etc. from server.py
    env['ORDER_NUMBER'] = str(order_num)
    # Set UTF-8 encoding for Windows to handle emojis
    if sys.platform == 'win32':
        env['PYTHONIOENCODING'] = 'utf-8'
    
    # Debug: Verify API config is passed through
    print(f"[DEBUG] Environment check for order {order_num}: API_KEY={'SET' if env.get('API_KEY') else 'NOT SET'}, API_URL={env.get('API_URL', 'NOT SET')}")
    
    print(f"[DEBUG] Python executable: {sys.executable}")
    print(f"[DEBUG] Environment variables: ORDER_NUMBER={env.get('ORDER_NUMBER')}, AUTOMATION_NAME={env.get('AUTOMATION_NAME', 'NOT SET')}")
    
    try:
        print(f"[DEBUG] Creating subprocess for order {order_num}...")
        process = subprocess.Popen(
            [sys.executable, '-u', main_script],  # -u flag for unbuffered output
            cwd=base_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        print(f"[DEBUG] Subprocess created with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"[ERROR] Failed to create subprocess for order {order_num}: {e}")
        import traceback
        traceback.print_exc()
        raise

def read_process_output(process, order_num):
    """Read and print process output in real-time"""
    def read_stdout():
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    message = f"[ORDER {order_num} STDOUT] {line.rstrip()}"
                    print(message)
                    write_to_log(message, worker_id=order_num)
        except Exception as e:
            error_msg = f"[ERROR] Error reading stdout for order {order_num}: {e}"
            print(error_msg)
            write_to_log(error_msg, worker_id=order_num)
    
    def read_stderr():
        try:
            for line in iter(process.stderr.readline, ''):
                if line:
                    message = f"[ORDER {order_num} STDERR] {line.rstrip()}"
                    print(message)
                    write_to_log(message, worker_id=order_num)
        except Exception as e:
            error_msg = f"[ERROR] Error reading stderr for order {order_num}: {e}"
            print(error_msg)
            write_to_log(error_msg, worker_id=order_num)
    
    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    return stdout_thread, stderr_thread

def main():
    print("[DEBUG] ========== AUTOMATION WORKER STARTING ==========")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    print(f"[DEBUG] Script location: {__file__}")
    
    total_orders = int(os.environ.get('TOTAL_ORDERS', '1'))
    max_parallel = int(os.environ.get('MAX_PARALLEL_WINDOWS', '1'))
    
    print(f"[DEBUG] Environment variables:")
    print(f"[DEBUG]   TOTAL_ORDERS: {total_orders}")
    print(f"[DEBUG]   MAX_PARALLEL_WINDOWS: {max_parallel}")
    print(f"[DEBUG]   AUTOMATION_NAME: {os.environ.get('AUTOMATION_NAME', 'NOT SET')}")
    print(f"[DEBUG]   API_KEY: {'SET' if os.environ.get('API_KEY') else 'NOT SET'}")
    
    print(f"[INFO] Starting automation: {total_orders} orders, max {max_parallel} parallel windows")
    write_to_log(f"[INFO] Starting automation: {total_orders} orders, max {max_parallel} parallel windows")
    
    completed = 0
    success_count = 0
    failure_count = 0
    active_processes = []
    order_queue = Queue()
    output_threads = {}  # Store output reading threads
    session_start_delay = 8  # Delay in seconds between starting each session (increased for better resource management)
    sessions_started = 0  # Track how many sessions have been started
    
    # Status file for tracking
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'automation_status.json')
    import json
    from datetime import datetime
    
    # Initialize status file
    def update_status_file(is_running, success, failure, all_products_failed=False):
        try:
            status_data = {
                "is_running": is_running,
                "success": success,
                "failure": failure,
                "all_products_failed": all_products_failed,
                "start_time": datetime.now().isoformat() if is_running else None,
                "end_time": datetime.now().isoformat() if not is_running else None
            }
            # Atomic write
            temp_file = status_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, status_file)
        except Exception as e:
            print(f"[ERROR] Failed to update status file: {e}")
    
    # Initialize status
    update_status_file(True, 0, 0)
    
    # Add all orders to queue
    for i in range(1, total_orders + 1):
        order_queue.put(i)
    
    print(f"[DEBUG] Added {total_orders} orders to queue")
    
    should_stop_all = False  # Flag to stop all workers if all product URLs fail
    
    try:
        while completed < total_orders and not should_stop_all:
            print(f"[DEBUG] Loop iteration: completed={completed}/{total_orders}, active={len(active_processes)}, queue_size={order_queue.qsize()}")
            
            # Start new processes up to max_parallel
            while len(active_processes) < max_parallel and not order_queue.empty() and not should_stop_all:
                order_num = order_queue.get()
                
                # Add delay between starting sessions (except for the first one)
                if sessions_started > 0:
                    delay_seconds = session_start_delay
                    print(f"[INFO] Waiting {delay_seconds} seconds before starting order {order_num}/{total_orders}...")
                    write_to_log(f"[INFO] Waiting {delay_seconds} seconds before starting order {order_num}/{total_orders}...")
                    time.sleep(delay_seconds)
                
                print(f"[INFO] Starting order {order_num}/{total_orders}")
                print(f"[INFO] [ISOLATED] Worker {order_num} will be completely isolated - gets its own phone number and request_id")
                try:
                    process = run_single_order(order_num)
                    active_processes.append((order_num, process))
                    sessions_started += 1  # Increment session counter
                    # Start reading output
                    stdout_thread, stderr_thread = read_process_output(process, order_num)
                    output_threads[order_num] = (stdout_thread, stderr_thread)
                    print(f"[DEBUG] Order {order_num} process started, PID: {process.pid}")
                    print(f"[DEBUG] [ISOLATED] Worker {order_num} isolation: Each process has its own memory space and variables")
                except Exception as e:
                    print(f"[ERROR] Failed to start order {order_num}: {e}")
                    import traceback
                    traceback.print_exc()
                    completed += 1  # Count as failed
                    failure_count += 1
                    update_status_file(True, success_count, failure_count)
            
            # Check for completed processes
            for order_num, process in active_processes[:]:
                if should_stop_all:
                    break
                    
                return_code = process.poll()
                if return_code is not None:
                    # Process finished
                    completed += 1
                    status = "SUCCESS" if return_code == 0 else "FAILED"
                    if return_code == 0:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    print(f"[INFO] Order {order_num} completed ({status}, return_code={return_code}) - {completed}/{total_orders} total")
                    write_to_log(f"[INFO] Order {order_num} completed ({status}, return_code={return_code}) - {completed}/{total_orders} total", worker_id=order_num)
                    
                    # Update status file
                    update_status_file(True, success_count, failure_count)
                    
                    # Read any remaining output
                    try:
                        stdout, stderr = process.communicate(timeout=1)
                        if stdout:
                            message = f"[ORDER {order_num} FINAL STDOUT] {stdout}"
                            print(message)
                            write_to_log(message, worker_id=order_num)
                        if stderr:
                            message = f"[ORDER {order_num} FINAL STDERR] {stderr}"
                            print(message)
                            write_to_log(message, worker_id=order_num)
                    except:
                        pass
                    
                    active_processes.remove((order_num, process))
                    if order_num in output_threads:
                        del output_threads[order_num]
                    
                    # If process failed with exit code 1 (all product URLs failed), stop all workers immediately
                    if return_code == 5:
                        print(f"[CRITICAL] Order {order_num} failed - all product URLs failed. Stopping all workers immediately...")
                        write_to_log(f"[CRITICAL] Order {order_num} failed - all product URLs failed. Stopping all workers immediately...", worker_id=order_num)
                        should_stop_all = True
                        
                        # Terminate all remaining active processes
                        for remaining_order_num, remaining_process in active_processes[:]:
                            try:
                                print(f"[DEBUG] Terminating process for order {remaining_order_num}")
                                remaining_process.terminate()
                                try:
                                    remaining_process.wait(timeout=5)
                                except:
                                    remaining_process.kill()
                            except Exception as e:
                                print(f"[ERROR] Failed to terminate process for order {remaining_order_num}: {e}")
                        
                        # Mark remaining orders in queue and active processes as failed
                        remaining_in_queue = order_queue.qsize()
                        remaining_active = len(active_processes)
                        remaining_total = remaining_in_queue + remaining_active
                        
                        if remaining_total > 0:
                            failure_count += remaining_total
                            completed += remaining_total
                            print(f"[INFO] Marked {remaining_total} remaining orders as failed ({remaining_in_queue} in queue, {remaining_active} active)")
                            write_to_log(f"[INFO] Marked {remaining_total} remaining orders as failed", worker_id=None)
                        
                        # Clear the queue and active processes
                        while not order_queue.empty():
                            order_queue.get()
                        active_processes.clear()
                        # Mark as all products failed
                        update_status_file(False, success_count, failure_count, all_products_failed=True)
                        break  # Break out of the for loop
            
            time.sleep(0.5)  # Small delay to avoid busy waiting
    except KeyboardInterrupt:
        print("\n[WARNING] [INTERRUPTED] Interrupted! Stopping all active processes...")
        # Terminate all active processes
        for order_num, process in active_processes:
            try:
                print(f"[DEBUG] Terminating process for order {order_num}")
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        print("[INFO] All processes terminated.")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in main loop: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print(f"[INFO] All {total_orders} orders completed!")
    print(f"[INFO] Final stats: Success={success_count}, Failure={failure_count}")
    write_to_log(f"[INFO] All {total_orders} orders completed!")
    write_to_log(f"[INFO] Final stats: Success={success_count}, Failure={failure_count}")
    
    # Mark as completed in status file
    update_status_file(False, success_count, failure_count)
    
    print("[DEBUG] ========== AUTOMATION WORKER FINISHED ==========")
    write_to_log("[DEBUG] ========== AUTOMATION WORKER FINISHED ==========")

if __name__ == "__main__":
    main()

