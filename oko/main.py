import typer
from oko.commands.init_cmd import init_project
from oko.commands.collection_cmd import add_collection

app = typer.Typer(help="OKO - API testing made simple", no_args_is_help=True)
add_app = typer.Typer(help="Add resources to OKO")

# ── Root commands ────────────────────────────────


@app.command("init")
def init():
    """Initialize a new project"""
    init_project()


# ── Add subcommands ───────────────────────────────


@add_app.command("collection")
def collection(name: str = typer.Argument(..., help="Collection name")):
    """
    Create a new collection
    """
    add_collection(name)


# Registrar subcomando add
app.add_typer(add_app, name="add")


if __name__ == "__main__":
    app()
