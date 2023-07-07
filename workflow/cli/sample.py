"""Sample CHIME/FRB Workflow Compatible Function."""

from typing import Dict, List, Tuple, Union


def fraction(
    numerator: float, denominator: Union[float, str]
) -> Tuple[Dict[str, float], List[str], List[str]]:
    """Sample CHIME/FRB Workflow Compatible Function.

    Args:
        numerator (float): Numerator of the fraction
        denominator (float): Denominator of the fraction

    Returns:
        Tuple[Dict[str, float], List[str], List[str]]:
            The fraction of the numerator and denominator as a dictionary.
    """
    denominator = float(denominator)
    fraction: float = numerator / denominator
    result = {"fraction": fraction}
    products: List[str] = ["/tmp/sample.csv"]
    plots: List[str] = ["/tmp/sample.png"]
    return result, products, plots
