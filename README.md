# SkibidiMusic Bot 🎵

SkibidiMusic Bot is a feature-rich Discord music bot designed to bring high-quality audio streaming to your server. It supports playing music from multiple sources including YouTube, Spotify, and Deezer, ensuring you never run out of tunes.

## Features

-   **Multi-Source Support**: Play music seamlessly from YouTube, Spotify, and Deezer.
-   **Queue Management**: Add songs to a queue, view the queue, and manage playback order.
-   **Playback Control**: Pause, resume, skip, and stop tracks with ease.
-   **Smart Queueing**: Use `!playnext` to prioritize songs or `!shuffle` to mix things up.
-   **Auto-Disconnect**: Automatically leaves the voice channel when left alone to save resources.
-   **Docker Support**: Easily deployable using Docker and Docker Compose.

## Installation

### Prerequisites

-   Python 3.8+
-   [FFmpeg](https://ffmpeg.org/download.html) installed and added to your system PATH.
-   A Discord Bot Token.

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AngeloAL12/SkibidiMusic.git
    cd SkibidiMusicBot
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your Discord token:
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    ```

5.  **Run the bot:**
    ```bash
    python main.py
    ```

### Docker Setup

1.  **Ensure Docker and Docker Compose are installed.**

2.  **Configure `.env` as shown above.**

3.  **Build and run the container:**
    ```bash
    docker-compose up -d --build
    ```

## Commands

| Command | Alias | Description |
| :--- | :--- | :--- |
| `!play <query/url>` | `!p` | Plays a song from YouTube, Spotify, or Deezer. Adds to queue if playing. |
| `!playnext <query/url>` | `!pn` | Adds a song to the very next position in the queue. |
| `!skip` | `!s` | Skips the current song. |
| `!pause` | | Pauses the current playback. |
| `!resume` | `!r` | Resumes paused playback. |
| `!stop` | | Stops playback, clears the queue, and disconnects the bot. |
| `!queue` | `!q` | Displays the current music queue. |
| `!shuffle` | `!mix` | Shuffles the current queue randomly. |
| `!reset` | | Emergency command to reset the bot's state and disconnect. |
| `!help` | `!h` | Shows the list of available commands. |

## Project Structure

-   `main.py`: Entry point of the bot.
-   `cogs/`: Contains bot extensions (cogs).
    -   `music.py`: Handles all music-related logic and commands.
    -   `general.py`: General purpose commands.
-   `utils/`: Helper modules for different music services.
    -   `spotify.py`: Spotify API integration.
    -   `deezer.py`: Deezer API integration.
    -   `youtube.py`: YouTube search and extraction logic.
-   `config.py`: Configuration settings.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](issues).

## License

This project is licensed under the MIT License.
