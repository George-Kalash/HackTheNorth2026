"""Run local API, worker and Vite together; stop child processes on exit."""

import subprocess
import sys
import time


def main():
    children = []
    try:
        for command, cwd in [
            (
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "prediction_terminal.api.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8010",
                    "--reload",
                ],
                None,
            ),
            ([sys.executable, "-m", "prediction_terminal.workers.main"], None),
            (["npm", "run", "dev"], "web"),
        ]:
            children.append(subprocess.Popen(command, cwd=cwd))
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    main()
