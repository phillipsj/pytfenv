import os
from html.parser import HTMLParser
from urllib import request

import hcl2
from semver import Version


class TerraformReleasesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_tag = None
        self.versions = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag == "a" and "terraform_" in data:
            clean_text = data.replace("terraform_", "")
            version = Version.parse(clean_text)
            if version.prerelease is None:
                self.versions.append(version)

    def get_versions(self) -> list[Version]:
        url = "https://releases.hashicorp.com/terraform/"
        response = request.urlopen(url)
        html = response.read().decode("utf-8")
        self.feed(html)
        return self.versions

    def find_terraform_tf() -> str:
        """Searches the current directory and any subdirectories for terraform.tf."""
        for root, _dirs, files in os.walk("."):
            if "terraform.tf" in files:
                return os.path.join(root, "terraform.tf")

    def get_terraform_version(file: str) -> str:
        with open(file) as file:
            hcl = hcl2.load(file)
            return hcl["terraform"][0]["required_version"]
