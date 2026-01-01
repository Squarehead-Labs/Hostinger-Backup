import os
import random
import subprocess
import paramiko
import ftplib
import mysql.connector
from datetime import datetime
from config import settings
from colorama import init, Fore, Style
from term_image.image import ITerm2Image

TERMINAL_WIDTH = os.get_terminal_size().columns


def main() -> None:
    init(autoreset=True)
    print_line()
    print_banner()
    print_line()
    print(Style.BRIGHT + Fore.GREEN + ">> Starting backup process")
    os.makedirs("backup", exist_ok=True)
    backup_file = generate_backup()
    if not backup_file: return
    download_file_via_ftp(backup_file)

    if settings.database.enabled and settings.database.name:
        generate_database_backup()

    if settings.github.enabled and settings.github.repository:
        upload_to_github()


def generate_backup() -> str | None:
    print(Style.BRIGHT + Fore.GREEN + "1) Generating backup on remote server")
    print(Fore.YELLOW + "   - Connecting to remote server via SSH")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=settings.ssh.host,
        port=settings.ssh.port,
        username=settings.ssh.user,
        password=settings.ssh.password,

    )
    print(Fore.YELLOW + "   - Creating backup archive")
    backup_file_name = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.tar.gz"
    backup_file_path = f"{settings.ssh.backup_path}/{backup_file_name}"
    cmd = f'tar -czvf {backup_file_path} {settings.ssh.target_path}'
    _, _, stderr = client.exec_command(cmd)
    error = stderr.read().decode()

    if error:
        print(Style.BRIGHT + Fore.RED + "   - Error during backup creation:")
        print(Style.BRIGHT + Fore.RED + f"     {error}")
        return None

    client.close()
    print(Fore.GREEN + "   - Backup archive created successfully")
    return backup_file_name


def download_file_via_ftp(file_path: str) -> None:
    print(Style.BRIGHT + Fore.GREEN + "2) Downloading backup via FTP")
    print(Fore.YELLOW + "   - Connecting to FTP server")
    try:
        ftp = ftplib.FTP(settings.ftp.host)
        ftp.port = settings.ftp.port
        ftp.login(settings.ftp.user, settings.ftp.password)
        ftp.cwd("../backup")

        print(Fore.YELLOW + "   - Downloading backup file")
        with open(f"backup/app.tar.gz", "wb") as f:
            ftp.retrbinary(f"RETR {file_path}", f.write)

        ftp.close()
        print(Fore.GREEN + "   - Backup file downloaded successfully as " + Fore.YELLOW + '/backup/app.tar.gz')
    except Exception as e:
        print(Style.BRIGHT + Fore.RED + "   - Error during FTP download:")
        print(Style.BRIGHT + Fore.RED + f"     {str(e)}")


def generate_database_backup() -> str | None:
    print(Style.BRIGHT + Fore.GREEN + "3) Generating MySQL database backup")
    print(Fore.YELLOW + "   - Connecting to MySQL database")
    try:
        connection = mysql.connector.connect(
            host=settings.database.host,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.name,
            port=settings.database.port
        )

        if connection.is_connected():
            connection.close()
            print(Fore.YELLOW + "   - Successfully connected to MySQL database")

    except mysql.connector.Error as e:
        print(Style.BRIGHT + Fore.RED + "   - Error connecting to MySQL database:")
        return None


    print(Fore.YELLOW + "   - Generating database dump")

    command = [
        'mysqldump',
        '-h', settings.database.host,
        '-P', str(settings.database.port),
        '-u', settings.database.user,
        f'-p{settings.database.password}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--events',
        settings.database.name
    ]


    try:
        print(Fore.YELLOW + "   - Executing mysqldump command")
        with open('backup/data.sql', 'w') as output_file:
            process = subprocess.Popen(command, stdout=output_file, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(Fore.GREEN + "   - Database dump created successfully: data.sql")
                return 'data.sql'
            else:
                print(Style.BRIGHT + Fore.RED + "   - Error during database dump:")
                print(Style.BRIGHT + Fore.RED + f"     {stderr}")
                return None

    except FileNotFoundError:
        print(Style.BRIGHT + Fore.RED + "   - mysqldump command not found. Please ensure MySQL is installed and mysqldump is in your PATH.")
        return None
    except Exception as e:
        print(Style.BRIGHT + Fore.RED + "   - An unexpected error occurred during database dump:")
        print(Style.BRIGHT + Fore.RED + f"     {str(e)}")
        return None


def upload_to_github() -> None:
    print(Style.BRIGHT + Fore.GREEN + "4) Uploading backup files to GitHub repository")

    print(Fore.YELLOW + "   - Cloning GitHub repository")
    cmd = f"git clone {settings.github.repository} backup/repo"
    subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)

    print(Fore.YELLOW + "   - Moving backup files to repository folder")
    backup_dir = f"backup/repo/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir)
    cmd = f"mv backup/app.tar.gz {backup_dir}/app.tar.gz"
    subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
    cmd = f"mv backup/data.sql {backup_dir}/data.sql"
    subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)

    print(Fore.YELLOW + "   - Committing and pushing changes to GitHub")
    cmd = f"cd backup/repo && git add . && git commit -m 'Backup {datetime.now().strftime('%Y-%m-%d %H:%M')}' && git push"
    subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL)
    print(Fore.GREEN + "   - Backup files uploaded to GitHub successfully")


def select_random_banner() -> str:
    banner_numer = random.randint(1, 3)
    return f"assets/kg{banner_numer}.png"


def print_line() -> None:
    print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "=" * TERMINAL_WIDTH)


def print_banner() -> None:
    img = ITerm2Image.from_file(select_random_banner())
    img.height = 10
    img_str = str(img)
    img_lines = img_str.splitlines()

    text_lines = [
        f"{Fore.BLUE}✨ Project Name: {Style.BRIGHT}{Fore.WHITE}Hostinger Backup",
        f"{Fore.BLUE}🧃 Author: {Style.BRIGHT}{Fore.WHITE}Ariadne Rangel",
        f"{Fore.BLUE}📚 Version: {Style.BRIGHT}{Fore.WHITE}1.0.1",
        f"{Fore.BLUE}📝 Description:",
        "A tool to automate backups from a remote server",
        "via SSH and FTP, including MySQL database dumps.",
        f"{Style.BRIGHT}{Fore.YELLOW}! Ensure all configurations are set in the .secrets.toml file.",
    ]

    max_lines = max(len(img_lines), len(text_lines))
    img_lines += [""] * (max_lines - len(img_lines))
    text_lines += [""] * (max_lines - len(text_lines))
    gap = "   "

    for i, t in zip(img_lines, text_lines):
        print(f"{i}{gap}{t}")


if __name__ == "__main__":
    main()
