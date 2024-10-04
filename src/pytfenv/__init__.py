import os
import platform
import shutil
import stat
import sys
import zipfile
from urllib import request

from semver import Version
from terraform_parser import TerraformReleasesParser

BASE_DIR = os.path.dirname(__file__)
TERRAFORM_EXECUTABLE_NAME_NIX = "terraform"
TERRAFORM_EXECUTABLE_NAME_WIN = "terraform.exe"
TERRAFORM_EXECUTABLE_NAME = (
    TERRAFORM_EXECUTABLE_NAME_NIX if platform.system().lower() != "Windows" else TERRAFORM_EXECUTABLE_NAME_WIN
)
TERRAFORM_EXECUTABLE = os.path.join(BASE_DIR, f"lib/{TERRAFORM_EXECUTABLE_NAME}")


def download(version: str):
    download_directory = "downloads"
    extract_directory = "lib"

    if os.path.exists(download_directory):
        shutil.rmtree(
            download_directory,
        )

    platform_name = platform.system().lower()
    architecture = platform.machine().lower()
    arch = "amd64" if architecture == "x86_64" else architecture
    file_name = f"terraform_{version}_{platform_name}_{arch}.zip"
    download_url = f"https://releases.hashicorp.com/terraform/{version}/{file_name}"

    os.makedirs(download_directory, exist_ok=True)
    os.makedirs(extract_directory, exist_ok=True)

    target_file = f"{download_directory}/{file_name}"
    request.urlretrieve(download_url, target_file)

    with zipfile.ZipFile(target_file) as archive:
        archive.extractall(extract_directory)

    shutil.rmtree(download_directory)
    executable_path = f"{extract_directory}/{TERRAFORM_EXECUTABLE_NAME}"
    executable_stat = os.stat(executable_path)
    os.chmod(executable_path, executable_stat.st_mode | stat.S_IEXEC)


def main() -> None:
    terraform_parser = TerraformReleasesParser()
    terraform_file = terraform_parser.find_terraform_tf()
    terraform_version = terraform_parser.get_terraform_version(terraform_file)
    if "," in terraform_version:
        raise ValueError(
            "Greater than, but less than constraints are not supported. See https://developer.hashicorp.com/terraform/tutorials/configuration-language/versions#terraform-version-constraints"
        )

    version = terraform_version.strip()

    versions = terraform_parser.get_versions()

    if "~>" in terraform_version:
        version = terraform_version.split("~>")[1].strip()
        parsed_version = Version.parse(version)
        matched_versions = []
        for v in versions:
            if v.is_compatible(parsed_version):
                matched_versions.append(v)
        version = max(matched_versions)
        print(version)
    elif ">=" in terraform_version:
        max_version = max(versions)
        if max_version.match(terraform_version.replace(" ", "")):
            print(max_version)
            version = max_version

    download(version)

    args = [] if len(sys.argv) < 2 else sys.argv[1:]
    os.execv(TERRAFORM_EXECUTABLE, ["terraform"] + args)
