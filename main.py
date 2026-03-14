import subprocess

def main():
    print("Hello from fyp!")
    subprocess.run("uv run src/app.py".split())

if __name__ == "__main__":
    main()
