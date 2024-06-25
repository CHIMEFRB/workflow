import os
from pathlib import Path
from typing import Dict, List

from workflow.examples.function import math


def test_math_function():

    a: int = 5
    b: int = 2
    results, products, plots = math(5, 2)
    # Check the results
    assert isinstance(results, Dict)
    assert isinstance(products, List)
    assert isinstance(plots, List)

    assert results["sum"] == a + b
    assert results["difference"] == a - b
    assert results["product"] == a * b
    assert results["quotient"] == a / b
    assert results["power"] == a**b
    assert results["root"] == a ** (1 / b)
    assert results["log"] == a ** (1 / b)

    # Check the files in /tmp
    assert len(products) == 1
    assert len(plots) == 1

    product_file = products[0]
    plot_file = plots[0]

    assert os.path.isfile(product_file)
    assert os.path.isfile(plot_file)

    assert Path(product_file).exists()
    assert Path(plot_file).exists()

    # Clean up
    os.remove(product_file)
    os.remove(plot_file)
