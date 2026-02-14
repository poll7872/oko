import json
import sys
import typer
from rich.json import JSON
from rich.console import Console
from rich.prompt import Prompt
from oko.service.service_endpoint import (
    add_endpoint,
    run_endpoint,
    prepare_endpoint_request,
    list_endpoints,
    list_missing_variables,
    get_last_runtime_value,
    save_runtime_history,
)
from oko.service.service_docs import generate_api_readme
from oko.ui.formatters import format_http_method, format_status_code
from oko.ui.prints import (
    print_section,
    print_success,
    print_error,
    print_header,
    print_table,
    print_info_panel,
)
from oko.ui.theme import custom_theme

app = typer.Typer(help="Manage endpoints")

console = Console(theme=custom_theme)


@app.command("add")
def add_endpoint_cmd(
    collection: str = typer.Argument(..., help="Collection name"),
    alias: str = typer.Argument(..., help="Endpoint alias"),
    url: str = typer.Argument(..., help="Endpoint URL"),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method"),
):
    """
    Add a new endpoint to a collection
    """
    try:
        add_endpoint(collection, alias, url, method)
        docs_path = generate_api_readme()

        formatted_method = format_http_method(method)

        success_message = (
            f"Endpoint added successfully\n\n"
            f"[bold]Collection:[/bold] [primary]{collection}[/primary]\n"
            f"[bold]Alias:[/bold] [primary]{alias}[/primary]\n"
            f"[bold]Method:[/bold] {formatted_method}\n"
            f"[bold]URL:[/bold] [primary]{url}[/primary]"
        )

        print_success(success_message, title="Endpoint Created")
        console.print(f"[label]API docs:[/label] [value]{docs_path}[/value]")

    except Exception as e:
        print_error(str(e), title="Error")


def list_endpoints_cmd(collection: str = typer.Argument(..., help="Collection name")):
    """
    List endpoints in a collection.
    """
    try:
        endpoints = list_endpoints(collection)

        print_header(f"Endpoints · {collection}")

        if not endpoints:
            print_info_panel(
                "No endpoints found in this collection.\n"
                "Use [secondary]oko endpoint add[/secondary] to create one.",
                title="Empty",
            )
            return

        rows = [[ep["alias"], ep["method"], ep["url"]] for ep in endpoints]

        print_table(
            title="Defined Endpoints",
            columns=["Alias", "Method", "URL"],
            rows=rows,
        )

    except Exception as e:
        print_error(str(e), title="Endpoint Error")


def _parse_kv(items: list[str]) -> dict:
    """
    Parse key=value pairs from CLI.
    """
    parsed = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid format '{item}'. Expected key=value")
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed


def _parse_kv_csv(raw: str) -> dict:
    """
    Parse comma-separated key=value pairs from CLI.
    Example: "a=1,b=2,c=3"
    """
    parsed = {}

    for chunk in raw.split(","):
        item = chunk.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                f"Invalid format '{item}'. Expected key=value in --vars input"
            )
        key, value = item.split("=", 1)
        parsed[key] = value

    return parsed


def endpoint_run_cmd(
    collection: str = typer.Argument(..., help="Collection name"),
    alias: str = typer.Argument(..., help="Endpoint alias"),
    params: list[str] = typer.Option(
        None, "--param", "-p", help="Query parameters (key=value)"
    ),
    headers: list[str] = typer.Option(
        None, "--header", "-H", help="Headers (key=value)"
    ),
    json_body: str = typer.Option(None, "--json", help="JSON body as string"),
    variables: list[str] = typer.Option(
        None, "--var", help="Runtime variables (key=value)"
    ),
    variables_csv: str = typer.Option(
        None,
        "--vars",
        help="Runtime variables in one argument (key=value,key2=value2)",
    ),
    prompt_missing: bool = typer.Option(
        True,
        "--prompt-missing/--no-prompt-missing",
        help="Prompt for unresolved variables before running the request",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Resolve and show the final request without sending it",
    ),
):
    """
    Run an endpoint.
    """
    try:
        print_header("Details Endpoint")

        runtime_variables = {}
        if variables_csv:
            runtime_variables.update(_parse_kv_csv(variables_csv))
        if variables:
            runtime_variables.update(_parse_kv(variables))

        parsed_params = _parse_kv(params) if params else None
        parsed_headers = _parse_kv(headers) if headers else None
        parsed_json_body = json.loads(json_body) if json_body else None

        missing_variables = list_missing_variables(
            collection=collection,
            alias=alias,
            params=parsed_params,
            headers=parsed_headers,
            json_body=parsed_json_body,
            runtime_variables=runtime_variables,
        )

        if missing_variables:
            if prompt_missing and sys.stdin.isatty():
                print_section(
                    "Missing Variables",
                    (
                        f"[label]Collection:[/label] [value]{collection}[/value]\n"
                        f"[label]Endpoint:[/label] [value]{alias}[/value]\n"
                        f"[label]Required:[/label] [accent]{', '.join(missing_variables)}[/accent]\n\n"
                        "[prompt]Please enter the missing values:[/prompt]"
                    ),
                )

                for variable_name in missing_variables:
                    default_value = get_last_runtime_value(
                        collection, alias, variable_name
                    )
                    prompt_text = (
                        f"[label]Value for[/label] [accent]{variable_name}[/accent]"
                    )
                    if default_value is not None:
                        prompt_text += f" [verbose](default: {default_value})[/verbose]"

                    runtime_variables[variable_name] = Prompt.ask(
                        prompt_text,
                        default=default_value,
                        show_default=False,
                        console=console,
                    )
            else:
                suggestions = [
                    f"- Runtime: --var {name}=<valor>" for name in missing_variables
                ]
                suggestions.extend(
                    f"- Global: oko variable add {name}=<valor>"
                    for name in missing_variables
                )
                raise ValueError(
                    "Faltan variables: "
                    + ", ".join(missing_variables)
                    + "\n"
                    + "\n".join(suggestions)
                )

        request_data = prepare_endpoint_request(
            collection=collection,
            alias=alias,
            params=parsed_params,
            headers=parsed_headers,
            json_body=parsed_json_body,
            runtime_variables=runtime_variables or None,
        )

        if dry_run:
            method = format_http_method(request_data["method"])
            body_preview = (
                json.dumps(request_data["json"], indent=2)
                if request_data["json"] is not None
                else "(empty)"
            )
            print_section(
                "Dry Run",
                (
                    f"[label]Status:[/label] [status_info]Request not sent (--dry-run)[/status_info]\n"
                    f"[label]Method:[/label] {method}\n"
                    f"[label]URL:[/label] [value]{request_data['url']}[/value]\n"
                    f"[label]Params:[/label] [value]{request_data['params'] or {}}[/value]\n"
                    f"[label]Headers:[/label] [value]{request_data['headers'] or {}}[/value]\n"
                    f"[label]JSON Body:[/label]\n[value]{body_preview}[/value]"
                ),
            )
            return

        with console.status("[secondary]Sending request...[/secondary]", spinner="dots"):
            response = run_endpoint(
                collection=collection,
                alias=alias,
                params=parsed_params,
                headers=parsed_headers,
                json_body=parsed_json_body,
                runtime_variables=runtime_variables or None,
            )
            save_runtime_history(collection, alias, runtime_variables)

        # ── Metadata ───────────────────────────────
        status = format_status_code(response.status_code)
        method = format_http_method(response.request.method)
        print_section(
            "Response Metadata",
            (
                f"[label]Status:[/label] {status}\n"
                f"[label]Method:[/label] {method}\n"
                f"[label]URL:[/label] [value]{response.request.url}[/value]"
            ),
        )

        # ── Body ───────────────────────────────
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            console.print(JSON.from_data(response.json()))
        else:
            console.print(response.text)

    except Exception as e:
        print_error(str(e), title="Error")
