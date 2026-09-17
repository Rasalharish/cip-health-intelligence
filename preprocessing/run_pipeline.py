import os
import subprocess
import sys

def run_script(script_path):
    print(f"Running {script_path}...")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_path}:")
        print(result.stderr)
        sys.exit(1)
    print(result.stdout)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    scripts_to_run = [
        os.path.join(base_dir, 'preprocessing', 'filter_cip.py'),
        os.path.join(base_dir, 'preprocessing', 'clean_data.py'),
        os.path.join(base_dir, 'preprocessing', 'segment_steps.py'),
        os.path.join(base_dir, 'preprocessing', 'features.py'),
        os.path.join(base_dir, 'model2', 'baseline.py')
    ]
    
    print("Starting Model 2 Pipeline...")
    
    for script in scripts_to_run:
        if os.path.exists(script):
            run_script(script)
        else:
            print(f"Warning: Script {script} not found, skipping...")
            
    print("Pipeline completed successfully.")
