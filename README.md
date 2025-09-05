# Voice Command Monitor

A live terminal UI voice command monitor that listens for German keywords and executes corresponding scripts with visual feedback, similar to htop or nvtop.

## Features

- **Live Terminal UI**: Real-time monitoring with beautiful colored panels
- **Keyword Boxes**: Visual boxes for each keyword that highlight green when triggered
- **Counters**: Shows execution count for each keyword
- **Scrolling Text**: Displays all recognized words in a scrolling line
- **Execution Log**: Shows script executions with timestamps
- **Fuzzy Matching**: Recognizes similar words (e.g., "jupiter" → "jupyter" with 86% similarity)
- **German Speech Recognition**: Local processing with Vosk
- **Configurable Highlight Duration**: Customize how long keywords stay highlighted

## Prerequisites

- Python 3.7+
- Microphone
- German Vosk model

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Download German Vosk model:
   ```bash
   wget https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip
   unzip vosk-model-small-de-0.15.zip
   mv vosk-model-small-de-0.15 model-de
   ```

## Usage

### Live Monitoring
```bash
python main.py --keywords "browser:browser.sh" "jupyter:jupyter.sh" "update:update.sh"
```

### Demo Mode (without microphone)
```bash
python main.py --keywords "browser:browser.sh" "jupyter:jupyter.sh" "update:update.sh" --demo
```

### Test Mode (script execution test)
```bash
python main.py --keywords "browser:browser.sh" "jupyter:jupyter.sh" --test
```

## UI Layout

```
┌─ Keyword: browser ─┐  ┌─ Keyword: jupyter ─┐  ┌─ Keyword: update ──┐
│      browser       │  │      jupyter       │  │       update       │
│                    │  │                    │  │                    │
│         3          │  │         1          │  │         2          │
└────────────────────┘  └────────────────────┘  └────────────────────┘

┌───────────────────────────────────── Recognized Words ─────────────────────────────────────┐
│ hello world test browser jupyter update system                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────── Script Executions ─────────────────────────────────────┐
│ [10:15:23] browser -> SUCCESS | Opening browser...                                        │
│ [10:15:45] jupyter -> SUCCESS | Starting Jupyter...                                       │
│ [10:16:12] update -> SUCCESS | System updated                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Parameters

- `--keywords`: Keywords in format "keyword:script.sh" (multiple allowed)
- `--model`: Path to Vosk model (default: model-de)
- `--highlight-duration`: Highlight duration in seconds (default: 1.0)
- `--demo`: Demo mode showing UI without audio processing
- `--test`: Test mode for configuration and script execution

## Controls

- **Ctrl+C**: Exit the application
- **Ctrl+Q**: Exit the application

## Example Scripts

Create executable shell scripts like `browser.sh`:

```bash
#!/bin/bash
echo "Opening browser..."
google-chrome &
```

Make them executable:
```bash
chmod +x browser.sh
```

## Beendigung

- Ctrl+C: Beendet das Programm
- Ctrl+Q: Beendet das Programm (auf manchen Systemen Ctrl+\)

## Beispiel-Skripte

Erstelle einfache Shell-Skripte wie `discord.sh`:

```bash
#!/bin/bash
discord &
```

Mache sie ausführbar: `chmod +x discord.sh`