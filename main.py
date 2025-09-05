#!/usr/bin/env python3
"""
Voice Command Monitor - Live Terminal UI
Monitors voice commands and executes scripts with visual feedback.
"""

import argparse
import difflib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from vosk import Model, KaldiRecognizer
import pyaudio

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

class VoiceCommandMonitor:
    def __init__(self, keywords, model_path, highlight_duration=1.0):
        self.keywords = keywords
        self.model_path = model_path
        self.highlight_duration = highlight_duration
        self.running = True
        self.console = Console()

        # UI State
        self.keyword_counts = {kw: 0 for kw in keywords.keys()}
        self.keyword_highlighted = {kw: 0.0 for kw in keywords.keys()}
        self.recognized_words = deque(maxlen=50)  # Last 50 recognized words
        self.script_log = deque(maxlen=20)  # Last 20 script executions

        # Audio components
        self.audio_queue = []
        self.audio_thread = None
        self.ui_thread = None

        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)

    def signal_handler(self, signum, frame):
        self.running = False

    def setup_recognizer(self):
        if not os.path.exists(self.model_path):
            self.console.print(f"[red]Model not found: {self.model_path}[/red]")
            self.console.print("[yellow]Please download a German Vosk model.[/yellow]")
            sys.exit(1)

        model = Model(self.model_path)
        rec = KaldiRecognizer(model, 16000)
        return rec

    def audio_worker(self):
        """Background thread for audio processing"""
        rec = self.setup_recognizer()
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=8000)

        while self.running:
            try:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").lower().strip()
                    if text:
                        # Add to recognized words for scrolling text
                        words = text.split()
                        for word in words:
                            self.recognized_words.append(word)

                        # Check for keyword matches
                        best_match = self.find_best_keyword_match(text)
                        if best_match:
                            keyword, script, confidence = best_match
                            self.keyword_counts[keyword] += 1
                            self.keyword_highlighted[keyword] = time.time()

                            # Execute script in background
                            threading.Thread(target=self.execute_script, args=(keyword, script)).start()

            except Exception as e:
                if self.running:
                    self.console.print(f"[red]Audio error: {e}[/red]")

        stream.stop_stream()
        stream.close()
        p.terminate()

    def find_best_keyword_match(self, text):
        """Find the best matching keyword using fuzzy matching"""
        best_match = None
        best_ratio = 0.0

        for keyword in self.keywords.keys():
            words = text.split()
            for word in words:
                ratio = difflib.SequenceMatcher(None, keyword.lower(), word.lower()).ratio()
                if ratio > best_ratio and ratio > 0.8:  # 80% similarity threshold
                    best_ratio = ratio
                    best_match = (keyword, self.keywords[keyword], ratio)

        return best_match

    def execute_script(self, keyword, script_path):
        """Execute script and log the result"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Correct relative paths
        if not os.path.isabs(script_path) and not script_path.startswith('./'):
            script_path = './' + script_path

        try:
            result = subprocess.run([script_path], check=True, capture_output=True, text=True, timeout=30)
            status = "SUCCESS"
            output = result.stdout.strip() if result.stdout else ""
        except subprocess.TimeoutExpired:
            status = "TIMEOUT"
            output = "Script timed out"
        except subprocess.CalledProcessError as e:
            status = "ERROR"
            output = e.stderr.strip() if e.stderr else str(e)
        except FileNotFoundError:
            status = "NOT_FOUND"
            output = f"Script not found: {script_path}"

        # Log the execution
        log_entry = f"[{timestamp}] {keyword} -> {status}"
        if output:
            log_entry += f" | {output[:50]}..."
        self.script_log.append(log_entry)

    def create_keyword_panels(self):
        """Create panels for each keyword"""
        panels = []
        current_time = time.time()

        for keyword in self.keywords.keys():
            count = self.keyword_counts[keyword]
            is_highlighted = (current_time - self.keyword_highlighted[keyword]) < self.highlight_duration

            if is_highlighted:
                style = "bold green on black"
                border_style = "green"
            else:
                style = "white on blue"
                border_style = "blue"

            panel = Panel(
                Align.center(f"[bold]{keyword}[/bold]\n\n[bold]{count}[/bold]"),
                title=f"Keyword: {keyword}",
                border_style=border_style,
                style=style,
                height=5
            )
            panels.append(panel)

        return Columns(panels, equal=True, expand=True)

    def create_scrolling_text(self):
        """Create scrolling text of recognized words"""
        if not self.recognized_words:
            text = "[dim]Waiting for speech...[/dim]"
        else:
            words = list(self.recognized_words)[-20:]  # Show last 20 words
            text = " ".join(words)

        return Panel(
            Text(text, overflow="ellipsis"),
            title="Recognized Words",
            border_style="yellow"
        )

    def create_script_log(self):
        """Create script execution log"""
        if not self.script_log:
            log_text = "[dim]No script executions yet[/dim]"
        else:
            log_text = "\n".join(self.script_log)

        return Panel(
            log_text,
            title="Script Executions",
            border_style="cyan",
            height=10
        )

    def create_layout(self):
        """Create the main layout"""
        layout = Layout()

        # Split into sections
        layout.split(
            Layout(name="keywords", size=8),
            Layout(name="scrolling", size=5),
            Layout(name="log", size=12)
        )

        # Populate sections
        layout["keywords"].update(self.create_keyword_panels())
        layout["scrolling"].update(self.create_scrolling_text())
        layout["log"].update(self.create_script_log())

        return layout

    def run(self):
        """Main run loop with live UI"""
        self.console.print("[green]Voice Command Monitor started[/green]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        # Start audio thread
        self.audio_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.audio_thread.start()

        # Live UI loop
        with Live(self.create_layout(), refresh_per_second=4, console=self.console) as live:
            while self.running:
                live.update(self.create_layout())
                time.sleep(0.25)

        self.console.print("\n[yellow]Shutting down...[/yellow]")

    def demo(self):
        """Demo mode - show UI with simulated data"""
        self.console.print("[green]Voice Command Monitor Demo[/green]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        # Add some demo data
        demo_words = ["hello", "world", "test", "browser", "jupyter", "update", "system"]
        for word in demo_words:
            self.recognized_words.append(word)

        # Simulate keyword triggers
        self.keyword_counts["browser"] = 3
        self.keyword_counts["jupyter"] = 1
        self.keyword_counts["update"] = 2

        # Add demo log entries
        self.script_log.append("[10:15:23] browser -> SUCCESS | Opening browser...")
        self.script_log.append("[10:15:45] jupyter -> SUCCESS | Starting Jupyter...")
        self.script_log.append("[10:16:12] update -> SUCCESS | System updated")

        # Live UI loop
        with Live(self.create_layout(), refresh_per_second=4, console=self.console) as live:
            while self.running:
                live.update(self.create_layout())
                time.sleep(0.25)

        self.console.print("\n[yellow]Demo ended...[/yellow]")

def parse_keywords(keywords_str):
    """Parse keywords from command line arguments"""
    keywords = {}
    for kw_str in keywords_str:
        if ":" not in kw_str:
            print(f"Invalid format: {kw_str}. Use 'keyword:script.sh'")
            continue
        keyword, script = kw_str.split(":", 1)
        script = script.strip()
        # Auto-correct relative paths
        if not os.path.isabs(script) and not script.startswith('./'):
            script = './' + script
        keywords[keyword.strip()] = script
    return keywords

def main():
    parser = argparse.ArgumentParser(description="Voice Command Monitor")
    parser.add_argument("--keywords", nargs="+", required=True,
                       help="Keywords in format 'keyword:script.sh'")
    parser.add_argument("--model", default="model-de",
                       help="Path to Vosk model (default: model-de)")
    parser.add_argument("--highlight-duration", type=float, default=1.0,
                       help="Highlight duration in seconds (default: 1.0)")
    parser.add_argument("--test", action="store_true",
                       help="Test mode: Show configuration and test script execution")
    parser.add_argument("--demo", action="store_true",
                       help="Demo mode: Show UI without audio processing")

    args = parser.parse_args()

    keywords = parse_keywords(args.keywords)
    if not keywords:
        print("No valid keywords specified.")
        sys.exit(1)

    print("Configured Keywords:")
    for kw, script in keywords.items():
        print(f"  '{kw}' -> {script}")

    if args.test:
        print("\nTest Mode: Testing script execution...")
        monitor = VoiceCommandMonitor(keywords, args.model, args.highlight_duration)
        for kw, script in keywords.items():
            print(f"Testing '{kw}' -> {script}")
            monitor.execute_script(kw, script)
            # Show log entries
            if monitor.script_log:
                print(f"  Result: {list(monitor.script_log)[-1]}")
        print("Test completed.")
        return

    monitor = VoiceCommandMonitor(keywords, args.model, args.highlight_duration)

    if args.demo:
        monitor.demo()
    else:
        monitor.run()

if __name__ == "__main__":
    main()