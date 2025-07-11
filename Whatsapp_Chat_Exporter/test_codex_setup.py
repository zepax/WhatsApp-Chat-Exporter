from pathlib import Path
import os

def test_setup_script_executable():
    script = Path('run/setup.sh')
    assert script.exists(), 'setup script missing'
    assert os.access(script, os.X_OK), 'setup script not executable'
