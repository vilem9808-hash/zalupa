"""Windows setup helper; can itself run under a newer Python such as 3.15."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SUPPORTED = {(3, minor) for minor in (10, 11, 12, 13)}
PROBE = 'import json,sys,struct; print(json.dumps([sys.version_info[0],sys.version_info[1],struct.calcsize("P")*8]))'


def find_python():
    candidates = []
    if shutil.which('py'):
        candidates.extend([['py', '-3.' + str(v)] for v in (13, 12, 11, 10)])
    candidates.append([sys.executable])
    if shutil.which('python'):
        candidates.append(['python'])
    for command in candidates:
        try:
            result = subprocess.run(command + ['-c', PROBE], capture_output=True, text=True, timeout=20)
            if result.returncode:
                continue
            major, minor, bits = json.loads(result.stdout.strip())
            if (major, minor) in SUPPORTED and bits == 64:
                return command, f'{major}.{minor}'
        except (OSError, ValueError, subprocess.TimeoutExpired):
            continue
    return None, None


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    command, version = find_python()
    if command is None:
        print('\nPython 3.10-3.13 (64-bit) is required for this package.')
        print('Recommended: install Python 3.13 for Windows (64-bit):')
        print('https://www.python.org/downloads/windows/')
        print('Python 3.15 can remain installed. Then run start.bat again.')
        print('Do not install Visual C++ or build Pygame from source.\n')
        return 1
    print('Using Python', version, flush=True)
    # A version-specific folder avoids reusing an old environment made by 3.15.
    env_dir = ROOT / ('.venv-game-' + version)
    python = env_dir / 'Scripts' / 'python.exe'
    if not python.exists():
        run(command + ['-m', 'venv', str(env_dir)])
    probe = subprocess.run([str(python), '-c', PROBE], capture_output=True, text=True)
    if probe.returncode or json.loads(probe.stdout) != [3, int(version.split('.')[1]), 64]:
        print('The game environment is damaged. Rename folder', env_dir.name, 'and try again.')
        return 1
    run([str(python), '-m', 'pip', 'install', '--only-binary=:all:', '-r', 'requirements.txt'])
    if '--build' in sys.argv:
        run([str(python), '-m', 'pip', 'install', '--only-binary=:all:', 'pyinstaller'])
        run([str(python), '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir',
             '--name', 'WolfVsRabbit', '--add-data', 'assets;assets', 'main.py'])
        print('Ready: dist\\WolfVsRabbit\\WolfVsRabbit.exe')
    else:
        run([str(python), 'main.py'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError) as exc:
        print('Setup or launch failed:', exc)
        print('If pip failed, check your Internet connection. Source builds are disabled.')
        sys.exit(1)
