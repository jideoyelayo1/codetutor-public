"""Own a trusted CLI process group and release it on timeout or interruption."""
import os
import signal
import subprocess


def run_owned(command, *, cwd=None, env=None, timeout=30, input=None):
    if os.name != 'posix':
        raise OSError('This development check requires POSIX process-group ownership')
    process=subprocess.Popen(command,cwd=cwd,env=env,text=True,
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             start_new_session=True)
    try:
        stdout,stderr=process.communicate(input=input,timeout=timeout)
        return subprocess.CompletedProcess(command,process.returncode,stdout,stderr)
    except BaseException:
        # Killing just a time/bash wrapper can leave its compiler/interpreter alive.
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate()
        raise
    finally:
        for stream in [process.stdin,process.stdout,process.stderr]:
            if stream is not None: stream.close()
