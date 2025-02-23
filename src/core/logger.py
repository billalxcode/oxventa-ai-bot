import sys
from rich.console import Console

class Logger(Console):
    def exit(self, code: int = 1):
        sys.exit(code)
    
    def warn(self, message: str):
        self.log(f"[yellow]WARN:[/yellow] {message}")

    def info(self, message: str):
        self.log(f"[blue]INFO:[/blue] {message}")

    def error(self, message: str):
        self.log(f"[red]ERROR:[/red] {message}")

    def debug(self, message: str):
        self.log(f"[green]DEBUG:[/green] {message}")

    def divide(self, width: int = 32):
        self.log(f"[bold magenta]{'-' * width}[/bold magenta]")
        
console = Logger()