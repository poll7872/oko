import typer

from oko.service.service_variable import (
    add_variable,
    delete_variable,
    load_variables,
)
from oko.service.service_docs import generate_api_readme
from oko.ui.prints import (
    print_header,
    print_success,
    print_error,
    print_info_panel,
    print_table,
    print_kv,
)

app = typer.Typer(help="Manage variables")


@app.command("add")
def variable_add(
    pair: str = typer.Argument(..., help="Variable in the format key=value"),
):
    """
    Add or update a variable.
    """
    try:
        if "=" not in pair:
            raise ValueError("Invalid format. Use key=value")

        key, value = pair.split("=", 1)

        add_variable(key.strip(), value.strip())
        docs_path = generate_api_readme()

        print_success(
            f"Variable [highlight]{key}[/highlight] saved successfully",
            title="Variable Added",
        )
        print_kv("API docs", str(docs_path))

    except Exception as e:
        print_error(str(e), title="Variable Error")


@app.command("list")
def variable_list():
    """
    List all variables.
    """
    try:
        variables = load_variables()

        print_header("Variables")

        if not variables:
            print_info_panel(
                "No variables defined.\n"
                "Use [secondary]oko variable add key=value[/secondary] to add one.",
                title="Empty",
            )
            return

        rows = [[str(key), str(value)] for key, value in variables.items()]
        print_table(
            title="Defined Variables",
            columns=["Key", "Value"],
            rows=rows,
        )

    except Exception as e:
        print_error(str(e), title="Variable Error")


@app.command("delete")
def variable_delete(
    key: str = typer.Argument(..., help="Variable key to delete"),
):
    """
    Delete a variable.
    """
    try:
        delete_variable(key)
        docs_path = generate_api_readme()

        print_success(
            f"Variable [highlight]{key}[/highlight] deleted successfully",
            title="Variable Deleted",
        )
        print_kv("API docs", str(docs_path))

    except KeyError as e:
        print_error(str(e), title="Variable Not Found")
    except Exception as e:
        print_error(str(e), title="Variable Error")
