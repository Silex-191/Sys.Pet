# Sys.Pet

A cyberpunk-themed Tamagotchi pet that feeds on code! The pet's health is tied to your system's performance metrics (CPU, RAM), and you can feed it by submitting code with parity-checking algorithms.

## Features

### Enhanced Parity Analyzer
- **Multi-language support**: Detects parity checks in Python, C, and C++ code
- **Token-based analysis**: Fast, lightweight heuristic approach without heavy parsing
- **Smart fallback**: Automatically uses simpler regex scanning for large inputs (>10KB) to maintain performance
- **Pattern detection**: Recognizes various parity-checking patterns:
  - Modulo operations (`n % 2 == 0`)
  - Bitwise operations (`n & 1`)
  - String-based checks
  - Macros (C/C++)
  - Lambda functions (Python)
  - And more!

### Interactive UI
- **Keyboard shortcuts**:
  - `Enter` - Submit code
  - `Shift+Enter` - Insert new line
- **File upload**: Support for `.py`, `.c`, `.cpp`, `.h`, `.hpp`, `.txt`, `.md` files
- **Real-time stats**: Monitor your pet's HP, hunger, fatigue, happiness, and weight
- **System integration**: Pet's weight reflects RAM usage, fatigue reflects CPU usage

## Quick Start

### Setup
```bash
./setup.sh
```

### Run
```bash
./run.sh
```

Then open http://localhost:8000 in your browser.

## How to Play

1. **Feed your pet** with code containing parity checks
2. **Monitor stats** - keep your pet healthy by feeding it regularly
3. **Level up** - gain XP for better patterns and evolve your pet
4. **Upload files** - drag and drop or select code files to analyze

## Technical Details

- **Backend**: FastAPI with async game loop
- **Frontend**: Vanilla JavaScript with cyberpunk CSS
- **Analyzer**: Custom token-based pattern matching engine
- **Language detection**: Automatic Python/C/C++ identification
