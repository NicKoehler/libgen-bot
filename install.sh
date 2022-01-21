# check if python3 is installed
if ! [ -x "$(command -v python3)" ]; then
  echo 'Error: python3 is not installed.' >&2
  exit 1
fi

# check if pip3 is installed
if ! [ -x "$(command -v pip3)" ]; then
  echo 'Error: pip3 is not installed.' >&2
  exit 1
fi

# creating a virtual environment and install the requirements
python3 -m venv venv
./venv/bin/pip3 install -r requirements.txt

clear

echo "Dependencies installed."
echo

# asking the env to run the app
read -p "Enter you Telegram API ID > " api_id
read -p "Enter you Telegram API Hash > " api_hash
read -p "Enter your Telegram Bot Token > " bot_token
read -p "Enter your Telegram ID > " owner_id

echo "API_ID=$api_id" >> .env
echo "API_HASH=$api_hash" >> .env
echo "BOT_TOKEN=$bot_token" >> .env
echo "OWNER_ID=$owner_id" >> .env

echo "./venv/bin/python3 libgen-bot/bot.py" > start.sh
chmod +x start.sh

echo "Installation complete."
echo "Run 'start.sh' to start the bot."

exit 0
