@echo off

: check if python is installed
where python
if %errorlevel% NEQ 0 (
	echo python is not installed
	pause
	exit
)

: check if pip is installed
where pip
if %errorlevel% NEQ 0 (
	echo pip is not installed
	pause
	exit
)

: creating a virtual environment and install the requirements
python -m venv venv
venv\Scripts\pip install -r requirements.txt

cls

echo Dependencies installed.
echo

: asking the env to run the app
set /p api_id="Enter you Telegram API ID > "
set /p api_hash="Enter you Telegram API Hash > "
set /p bot_token="Enter your Telegram Bot Token > "
set /p owner_id="Enter your Telegram ID > "

echo API_ID=%api_id% >> .env
echo API_HASH=%api_hash% >> .env
echo BOT_TOKEN=%bot_token% >> .env
echo OWNER_ID=%owner_id% >> .env

echo venv\Scripts\python libgen-bot\bot.py >> start.bat

echo Installation complete.
echo Run start.bat to start the bot.
