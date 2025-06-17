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

3. Click **Study** to begin practicing the cards currently in the study deck.
4. Click **Scan Files** to import or update cards from the markdown files.
5. Click **New Day** to start a fresh study session which moves new and review cards into the study deck.

Progress is stored in `flashcard_data.json`. To reset all progress, run:

```bash
python reset_flashcards.py
```

Configuration options are stored in `config.json`.
