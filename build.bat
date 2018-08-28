rd dist /q /s
pyinstaller main.py --noconsole
xcopy distribute dist\ /y /e /s /i
mkdir dist\json_only
mkdir dist\tilesets
