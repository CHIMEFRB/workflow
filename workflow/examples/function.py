"""Sample CHIME/FRB Workflow Compatible Function."""

from pathlib import Path
from typing import Dict, List, Tuple, Union


def math(
    a: Union[float, int], b: Union[float, int]
) -> Tuple[Dict[str, float], List[str], List[str]]:
    """Sample CHIME/FRB Workflow Compatible Function.

    Args:
        a (Union[float, int]): A number
        b (Union[float, int]): Another number

    Raises:
        error: If the arguments are not

    Returns:
        Tuple[Dict[str, float], List[str], List[str]]:
            The results, products, and plots
    """
    try:
        assert isinstance(a, (float, int)), "a must be a number"
        assert isinstance(b, (float, int)), "b must be a number"
        results: Dict[str, float] = {
            "sum": a + b,
            "difference": a - b,
            "product": a * b,
            "quotient": a / b,
            "power": a**b,
            "root": a ** (1 / b),
            "log": a ** (1 / b),
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
