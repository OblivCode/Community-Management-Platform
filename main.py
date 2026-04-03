import subprocess

def main():
    print("Hello from fyp!")
    subprocess.run("uv run python -m src.app".split())

if __name__ == "__main__":
    main()
