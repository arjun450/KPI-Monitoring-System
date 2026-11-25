"""
One-click setup script.
Run this once to: generate data → run ETL → check alerts → open dashboard.
"""

import os
import sys
import subprocess
import webbrowser
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd=None):
    print(f"\n▶  {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd or BASE_DIR, shell=isinstance(cmd, str))
    if result.returncode != 0:
        print(f"❌  Command failed with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    print("=" * 60)
    print("  KPI Monitoring System — Setup & Launch")
    print("=" * 60)

    # Step 1: Generate synthetic data
    print("\n[1/4] Generating synthetic dataset...")
    run([sys.executable, os.path.join(BASE_DIR, "data", "generate_data.py")])

    # Step 2: Run ETL pipeline
    print("\n[2/4] Running ETL pipeline (extract → validate → transform → load)...")
    etl_script = os.path.join(BASE_DIR, "etl", "load.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(BASE_DIR, "etl")
    subprocess.run([sys.executable, etl_script], env=env, cwd=BASE_DIR)

    # Step 3: Run alert check
    print("\n[3/4] Running KPI alert engine...")
    env["PYTHONPATH"] = os.path.join(BASE_DIR, "etl") + os.pathsep + os.path.join(BASE_DIR, "automation")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "automation", "alert_engine.py")],
                   env=env, cwd=BASE_DIR)

    # Step 4: Generate report
    print("\n[4/4] Generating daily report...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "automation", "generate_report.py")],
                   env=env, cwd=BASE_DIR)

    print("\n" + "=" * 60)
    print("✅  Setup complete!")
    print("\nTo launch the interactive dashboard, run:")
    print(f"  streamlit run {os.path.join(BASE_DIR, 'dashboard', 'app.py')}")
    print("=" * 60)

    # Ask user if they want to launch dashboard now
    launch = input("\nLaunch dashboard now? [Y/n]: ").strip().lower()
    if launch in ("", "y", "yes"):
        print("🚀 Launching Streamlit dashboard...")
        subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             os.path.join(BASE_DIR, "dashboard", "app.py")],
            cwd=BASE_DIR
        )
        time.sleep(3)
        webbrowser.open("http://localhost:8501")


if __name__ == "__main__":
    main()
