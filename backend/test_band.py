import sys

try:
    import band
except ModuleNotFoundError:
    print("Error: 'band' module not found.")
    print("This project uses a virtual environment managed by 'uv'.")
    print("Please run this script with: uv run python test_band.py")
    sys.exit(1)

print("band module:", [x for x in dir(band) if not x.startswith('_')])
print()

try:
    from band import Agent
    print("band.Agent attributes:", [x for x in dir(Agent) if not x.startswith('_')])
except Exception as e:
    print("Error importing Agent from band:", e)
    sys.exit(1)

print()
print("All band-sdk tests passed!")