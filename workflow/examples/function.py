"""Sample CHIME/FRB Workflow Compatible Function."""

from pathlib import Path
from typing import Dict, List, Tuple, Union

import click
from click_params import FirstOf


def math(
    alpha: Union[float, int], beta: Union[float, int] = 1.0
) -> Tuple[Dict[str, float], List[str], List[str]]:
    """Sample CHIME/FRB Workflow Compatible Function.

    Args:
        a (Union[float, int]): A number
        b (Union[float, int]): Another number

    Raises:
        error: If the arguments are not numbers

    Returns:
        Tuple[Dict[str, float], List[str], List[str]]:
            The results, products, and plots
    """
    try:
        assert isinstance(alpha, (float, int)), "alpha must be a number"
        assert isinstance(beta, (float, int)), "beta must be a number"
        results: Dict[str, float] = {
            "sum": alpha + beta,
            "difference": alpha - beta,
            "product": alpha * beta,
            "quotient": alpha / beta,
            "power": alpha**beta,
            "root": alpha ** (1 / beta),
            "log": alpha ** (1 / beta),
        }
        # Make a csv file with results
        with open("/tmp/sample.csv", "w") as file:
            for key, value in results.items():
                file.write(f"{key},{value}\n")
        products: List[str] = ["/tmp/sample.csv"]
        # Get the directory of whereever this file is
        current: Path = Path(__file__).parent
        # Copy sample svg file to /tmp
        source: Path = current / "sample.svg"
        destination: Path = Path("/tmp/sample.svg")
        destination.write_text(source.read_text())
        plots: List[str] = [destination.as_posix()]
        return results, products, plots
    except AssertionError as error:
        raise error


@click.command("math", help="Sample CHIME/FRB Workflow Compatible Function.")
@click.option(
    "--alpha",
    "-a",
    default=1.0,
    type=FirstOf(click.FLOAT, click.INT),
    required=True,
    help="A number.",
)
@click.option(
    "--beta",
    "-b",
    default=2.0,
    type=FirstOf(click.FLOAT, click.INT),
    required=True,
    help="Another number.",
)
def cli(
    alpha: Union[float, int], beta: Union[float, int]
) -> Tuple[Dict[str, float], List[str], List[str]]:
    """Click command for the math function."""
    results, products, plots = math(alpha, beta)
    return results, products, plots


if __name__ == "__main__":
    cli()
