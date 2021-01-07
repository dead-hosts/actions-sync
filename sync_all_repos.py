#!/usr/bin/env python3
"""
Dead Hosts's actions sync

Author:
    Nissar Chababy, @funilrys, contactTATAfunilrysTODTODcom

Project link:
    https://github.com/dead-hosts/actions-sync

License:
::
    MIT License
    Copyright (c) 2019, 2020, 2021 Dead Hosts
    Copyright (c) 2019, 2020, 2021 Nissar Chababy
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import os

from github import Github
from PyFunceble.helpers.command import CommandHelper
from PyFunceble.helpers.directory import DirectoryHelper
from PyFunceble.helpers.environment_variable import EnvironmentVariableHelper
from PyFunceble.helpers.file import FileHelper

USER_TOKEN = EnvironmentVariableHelper("GITHUB_TOKEN").get_value()
USER_GIT_EMAIL = EnvironmentVariableHelper("GIT_EMAIL").get_value()
USER_GIT_NAME = EnvironmentVariableHelper("GIT_NAME").get_value()

ORG_NAME = "dead-hosts"
CLONE_TEMPLATE = f"https://{USER_TOKEN}@github.com/%slug%.git"

DEPLOYMENT_DIR = "to_deploy"
CLONE_DIR = "clones"
DEPLOY_FILES_TO_IGNORE = []
COMMIT_MESSAGE = "Sync actions."

REPOS_TO_IGNORE = [
    ".github",
    "template",
    "actions-sync",
    "infrastructure-launcher",
    "infrastructure-monitoring",
    "dev-center",
]

if __name__ == "__main__":
    dir_helper = DirectoryHelper()
    file_helper = FileHelper()

    gh = Github(USER_TOKEN)

    if not dir_helper.set_path(CLONE_DIR).exists():
        dir_helper.create()

    dir_helper.set_path(DEPLOYMENT_DIR)

    CommandHelper(f"git config --global user.email {USER_GIT_EMAIL!r}").run_to_stdout(
    )
    CommandHelper(f"git config --global user.name {USER_GIT_NAME!r}").run_to_stdout(
    )
    CommandHelper("git config --global push.default simple").run_to_stdout(
    )
    CommandHelper("git config --local pull.rebase false").run_to_stdout()

    for repo in gh.get_organization(ORG_NAME).get_repos():
        if repo.name in REPOS_TO_IGNORE:
            continue


        print("Starting to handle:", repo.name)

        repo_slug = f"{ORG_NAME}/{repo.name}"
        clone_url = CLONE_TEMPLATE.replace("%slug%", repo_slug)
        clone_destination = f"{CLONE_DIR}/{repo.name}"

        response = CommandHelper(f"git clone {clone_url} {clone_destination}").run()

        for line in response:
            print(line)

        for root, _, files in os.walk(dir_helper.path):
            unformatted_root = root
            root = root.replace(dir_helper.path, "")

            if root.startswith("/"):
                root = root[1:]

            local_dir_helper = DirectoryHelper(os.path.join(clone_destination, root))

            if not local_dir_helper.exists():
                local_dir_helper.create()

            for file in files:
                file_helper.set_path(os.path.join(dir_helper.path, root, file)).copy(
                    os.path.join(local_dir_helper.path, file)
                )

        response =CommandHelper(
            f"cd {clone_destination} && git add --all && git commit -a "
            f"{COMMIT_MESSAGE!r} && git push && cd -"
        ).run()

        for line in response:
            print(line)

        DirectoryHelper(clone_destination).delete()
        print("Finished to handle:", repo.name)
