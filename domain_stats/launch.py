import pathlib
import os
import sys
from domain_stats.settings import setup_directory



def launch_from_config(tgt_folder):
    os.chdir(tgt_folder)
    launch_cmd = f"""{sys.executable} -m gunicorn.app.wsgiapp 'domain_stats.server:config_app("{tgt_folder}")' -c {tgt_folder}/gunicorn_config.py"""
    print(f"Running {launch_cmd}")
    os.system(launch_cmd)

def main():
    if len(sys.argv) != 2:
        typed_folder = input("Where do you want to store your domain_stats data and binaries? ")
    else:
        typed_folder = sys.argv[1]

    tgt_folder = pathlib.Path(typed_folder)
    if typed_folder.startswith("."):
        tgt_folder = pathlib.Path().cwd() / tgt_folder
    if not tgt_folder.is_dir():
        print("That directory does not exist. Please create it and/or try again.")
        sys.exit(1)
    if (tgt_folder / "domain_stats.yaml").is_file():
        print("Existing config found in directory. Using it.")
        launch_from_config(str(tgt_folder))
    elif input("Would you like to setup this directory now?").lower().startswith("y"):
        setup_directory(tgt_folder)


if __name__ == "__main__":
    main()

