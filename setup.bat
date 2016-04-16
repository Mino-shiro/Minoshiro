@echo off
echo 'Installing requirements using pip!'
echo '1: Installing discord.py from git. If you do not have git installed or use it through the git bash this will not work. Follow the instructions in README.md instead!'
pip install git+https://github.com/Rapptz/discord.py@async
echo '2: Installing lxml wheel'
pip install http://jwolff52.github.io/Discordoragi/lxml-3.6.0-cp35-cp35m-win32.whl
echo '3: Installing pyquery wheel'
pip install http://jwolff52.github.io/Discordoragi/pyquery-1.2.13-py2-none-any.whl
echo '4: Installing pyscopg wheel'
pip install http://jwolff52.github.io/Discordoragi/psycopg2-2.6.1-cp35-cp35m-win32.whl
echo '5: Installing the rest of our requirements'
pip install -r requirements.txt
echo 'Instalation complete!'
pause