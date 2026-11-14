import os
from pathlib import Path
import subprocess
import sys
import time
import pytest

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from scripts.owned_process import run_owned


def running(pid):
    result=subprocess.run(['ps','-o','stat=','-p',str(pid)],text=True,capture_output=True)
    return result.returncode==0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith('Z')


def assert_stopped(pid):
    deadline=time.monotonic()+2
    while time.monotonic()<deadline:
        if not running(pid): return
        time.sleep(.02)
    assert not running(pid), 'The timed-out/interrupted CLI child is still running'


def sleeper(tmp_path):
    pidfile=tmp_path/'child.pid'
    program="import os,time; from pathlib import Path; Path("+repr(str(pidfile))+").write_text(str(os.getpid())); time.sleep(30)"
    # Actual time wrapper, matching validate_ml_lean's ownership shape.
    return ['/usr/bin/time',sys.executable,'-c',program],pidfile


def test_timeout_stops_the_wrapped_interpreter(tmp_path):
    command,pidfile=sleeper(tmp_path)
    with pytest.raises(subprocess.TimeoutExpired): run_owned(command,timeout=.5)
    assert pidfile.exists()
    assert_stopped(int(pidfile.read_text()))


def test_interruption_stops_the_wrapped_interpreter(tmp_path,monkeypatch):
    command,pidfile=sleeper(tmp_path)
    original=subprocess.Popen.communicate
    interrupted=False
    def communicate(process,*args,**kwargs):
        nonlocal interrupted
        if not interrupted:
            interrupted=True
            # Establish a real active child, then simulate caller interruption.
            deadline=time.monotonic()+2
            while not pidfile.exists() and time.monotonic()<deadline: time.sleep(.01)
            assert pidfile.exists()
            raise KeyboardInterrupt
        return original(process,*args,**kwargs)
    monkeypatch.setattr(subprocess.Popen,'communicate',communicate)
    with pytest.raises(KeyboardInterrupt): run_owned(command)
    assert_stopped(int(pidfile.read_text()))


def test_normal_completion_preserves_output_and_exit_status():
    result=run_owned([sys.executable,'-c','import sys; print(input()); print("diagnostic",file=sys.stderr); sys.exit(3)'],
                     input='hello\n')
    assert (result.returncode,result.stdout,result.stderr)==(3,'hello\n','diagnostic\n')
