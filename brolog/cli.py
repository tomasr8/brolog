import sys
from io import TextIOWrapper

import click

import brolog
from brolog.lex import LexerError
from brolog.objects import Rule
from brolog.parse import ParseError, Parser
from brolog.solver import get_variable_assignments, query


@click.group(invoke_without_command=True)
@click.argument("input_file", type=click.File("r"), required=False)
@click.option("--version", is_flag=True)
@click.pass_context
def cli(ctx, input_file: TextIOWrapper, version: bool) -> None:  # noqa: ANN001, FBT001
    """Brolog REPL. Run `brolog input_file.pl` to load a program"""
    if ctx.invoked_subcommand is None:
        if input_file:
            repl(input_file)
        elif version:
            click.echo(brolog.__version__)
        else:
            click.echo(ctx.get_help())


def repl(input_file: TextIOWrapper) -> None:
    source = input_file.read()
    if (rules := try_parse(source)) is None:
        sys.exit(1)

    while True:
        try:
            query_str = input(click.style("?- ", fg="yellow"))
            if (q := try_parse(query_str, head_only=True)) is None:
                continue

            if proofs := list(query(rules, q)):
                for proof in proofs:
                    assignments = get_variable_assignments(q, proof)
                    if not assignments:
                        click.secho("true.\n", bold=True)
                        continue

                    output = ",\n".join(f"{variable} = {value}" for variable, value in assignments.items()) + ".\n"
                    click.echo(output)
            else:
                click.secho("false.", fg="red", bold=True)

        except EOFError:
            break


def try_parse(source: str, **kwargs) -> list[Rule] | Rule | None:
    try:
        return Parser(source).parse(**kwargs)
    except LexerError as e:
        click.secho(f"Error at line {e.line} column {e.column}: {e}", fg="red", bold=True)
    except ParseError as e:
        if e.token:
            click.secho(f"Error at line {e.token.line} column {e.token.column}: {e}", fg="red", bold=True)
        else:
            click.secho(f"Error: {e}", fg="red", bold=True)
