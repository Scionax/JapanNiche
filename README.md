# Japanese Flashcard Learning System

This is a simple spaced repetition flashcard application for learning Japanese words. Flashcards are stored as markdown files in the `flashcards/` directory. Running `python main.py` now opens a PyQt5 graphical interface to study, rescan files, or start a new day.

## Usage

1. Place your markdown files inside `flashcards/` following the format:

```markdown
# Category
- japaneseword: English translation. [pronunciation] [hiragana]
```

2. Run the program:

```bash
python main.py
```

3. Click the icons along the top of the window to **Study**, **Scan Files**, start a **New Day**, or **Quit** the program.
4. During study, press **Space** to reveal the answer and **A**, **S**, **D**, or **F** to grade the card.

Progress is stored in `flashcard_data.json`. Older data files can be
converted to the new unified format by running:

```bash
python convert_flashcard_data.py
```

To reset all progress, run:

```bash
python reset_flashcards.py
```

Configuration options are stored in `config.json`.
