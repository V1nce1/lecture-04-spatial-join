import time
import importlib.util
from copy import deepcopy
from data.util import load_uscities, load_cellular_towers

def benchmark(implementation_file, points_a, points_b):
    print('#' * 80)
    print(f"Running benchmark for implementation: {implementation_file}")
    # Dynamically load the implementation module
    spec = importlib.util.spec_from_file_location("implementation", implementation_file)
    impl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(impl)

    # Prepare data
    start_prep = time.perf_counter()
    prepared = impl.prepare(points_a, points_b)
    end_prep = time.perf_counter()

    # Run join
    start_join = time.perf_counter()
    results = impl.join(prepared)
    end_join = time.perf_counter()

    # Print benchmark results
    print("Benchmark results for implementation:", implementation_file)
    print(f"Preparation time: {end_prep - start_prep:.4f} seconds")
    print(f"Join time: {end_join - start_join:.4f} seconds")
    print(f"Total results: {len(results)} pairs")
    print()

def main(implementations: list, limit: int = None):
    # Load data
    points_a = list(load_uscities("data/uscities.csv"))
    points_b = list(load_cellular_towers("data/cellular_towers.csv"))
    if limit is not None:
        points_a = points_a[:limit]
        points_b = points_b[:limit]
    for impl_file in implementations:
        benchmark(impl_file, deepcopy(points_a), deepcopy(points_b))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark spatial join implementations")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of points loaded from each dataset")
    parser.add_argument("implementations", nargs="+", help="List of implementation files to benchmark")
    args = parser.parse_args()
    main(args.implementations, args.limit)
