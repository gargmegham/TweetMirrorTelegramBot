# Tweet Mirror Telegram Bot

This repository contains a Telegram bot that fetches tweets from a specified Twitter user and posts them to a Telegram chat. Additionally, it tracks the chats the bot is in, greets new chat members, and handles errors gracefully.

## Features

- **Tweet Fetching**: The bot periodically fetches tweets from a specified Twitter user using the Twitter API.
- **Chat Tracking**: It tracks the chats the bot is in, including private chats, groups, and channels.
- **Greeting Messages**: The bot greets new members who join chats where it is present.
- **Error Handling**: Errors encountered during bot operation are logged and sent to the developer via Telegram.

## Usage

1. **Setup Environment**:

   - Install the necessary dependencies using `pip install -r requirements.txt`.
   - Add your Telegram bot API token and other secrets to `secrets.json`.

2. **Run the Bot**:
   - Execute `python main.py` to start the bot.
   - The bot will periodically fetch tweets and perform other specified tasks.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. Make sure to follow the [contribution guidelines](CONTRIBUTING.md).

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any questions or inquiries, please contact [meghamgarg@gmail.com](mailto:meghamgarg@gmail.com).
