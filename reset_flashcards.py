import os

for fname in ['flashcard_data.json']:
    if os.path.exists(fname):
        os.remove(fname)
        print(f"Removed {fname}")
    else:
        print(f"{fname} does not exist")
