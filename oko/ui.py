from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from rich.table import Table
from rich.box import ROUNDED

LOGO_OKO = """
[bright_cyan]
█▓▒▒░░░-OKO-░░░▒▒▓█
[/bright_cyan]
"""

LOGO_OKO_INLINE = "[bright_cyan]OKO CLI[/bright_cyan]"


# Custom theme for consistent styling
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "primary": "blue",
        "secondary": "bright_cyan",
    }
)

console = Console(theme=custom_theme)


def print_logo():
    """Prints the OKO logo."""
    console.print(LOGO_OKO, justify="center")


def print_header(title: str):
    """Prints a section header."""
    console.rule(f"[secondary]{title}[/secondary]", style="secondary")
    console.print()


def print_section(title: str, content: str):
    """Prints a section panel."""
    console.print(
        Panel(
            content, title=f"[secondary]{title}[/secondary]", border_style="secondary"
        )
    )


def print_kv(key: str, value: str):
    """Print key-value information with consistent formatting."""
    console.print(f"[secondary]{key}: [/secondary]{value}")


def print_success(message: str, title: str = "✅ Success"):
    console.print(
        Panel(
            f"[success]{message}[/success]",
            title=title,
            border_style="success",
            expand=False,
        )
    )


def print_error(message: str, title: str = "❌ Error"):
    console.print(
        Panel(
            f"[error]{message}[/error]",
            title=title,
            border_style="error",
            expand=False,
        )
    )


def print_warning(message: str, title: str = "⚠️ Warning"):
    console.print(
        Panel(
            f"[warning]{message}[/warning]",
            title=title,
            border_style="warning",
            expand=False,
        )
    )


def print_info_panel(message: str, title: str = "📋 Info"):
    console.print(Panel(message, title=title, border_style="info", expand=False))


def get_table() -> Table:
    return Table(
        show_header=True, header_style="bold bright_cyan", box=ROUNDED, padding=(0, 2)
    )
