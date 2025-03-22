import argparse


def run_script3(arg1, arg2):
    print(f"Running Script 3 with {arg1} and {arg2}")


def main():
    parser = argparse.ArgumentParser(description="Script 3 command-line tool")
    parser.add_argument("--arg1", type=str, help="Argument 1")
    parser.add_argument("--arg2", type=int, help="Argument 2")
    args = parser.parse_args()

    run_script3(args.arg1, args.arg2)


if __name__ == "__main__":
    main()
