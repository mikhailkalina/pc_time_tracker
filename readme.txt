python --version
python -m pip install pyinstaller
python -m PyInstaller --version
python -m PyInstaller --noconsole --onefile --icon="clock.ico" --add-data "clock.ico;." worktime_tracker.py
