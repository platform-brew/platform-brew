#!/usr/bin/env python
import argparse
import contextlib
import os
import re
import subprocess


WHITESPACE_PATTERN = re.compile("[\s]+")
HOMEBREW_ROOT = os.environ.get("HOMEBREW_ROOT", os.path.join(os.path.expanduser("~"), ".linuxbrew"))
HOMEBREW_SCIENCE_ROOT = os.environ.get("HOMEBREW_SCIENCE_ROOT", os.path.join(HOMEBREW_ROOT, "Library", "Taps", "homebrew", "homebrew-science")) 


def main():
    parser = argparse.ArgumentParser(description='Versioned Brew.')
    versioned_install("tophat", "2.0.11")



class CommandLineException(Exception):

    def __init__(self, command, stdout, stderr):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.message = "Failed to execute command-line %s, stderr was %s" % (command, stderr)

    def __str__(self):
        return self.message


def versioned_install(package, version=None):
    with brew_changeset("master"):
        version_to_changeset = brew_version_info(package)
        if version is None:
            version = version_to_changeset[0][0]
        changeset = dict([(t[0], t[1]) for t in version_to_changeset])[version]
        with brew_changeset(changeset):
            deps = brew_deps(package)
            dep_to_version = {}
            for dep in deps:
                version_info = brew_version_info(dep)[0]
                version = version_info[0]
                dep_to_version[dep] = version
                versioned = version_info[2]
                if versioned:
                    dep_to_version[dep] = version
                    versioned_install(dep, version)
                else:
                    # Install latest.
                    dep_to_version[dep] = None
                    unversioned_install(dep)

            try:
                for dep in deps:
                    version = dep_to_version[dep]
                    if version:
                        brew_execute(["switch", dep, version])
                    else:
                        brew_execute(["link", dep])

                brew_execute(["install", package])
            finally:
                attempt_unlink_all(package, deps)


def unversioned_install(package):
    try:
        deps = brew_deps(package)
        for dep in deps:
            brew_execute(["link", dep])            
        brew_execute(["install", package])
    finally:
        attempt_unlink_all(package, deps)


def attempt_unlink_all(package, deps):
    for dep in deps:
        attempt_unlink(dep) 
    attempt_unlink(package)


def attempt_unlink(package):
    try:
        brew_execute(["link", package])
    except Exception:
        # TODO: warn
        pass


def brew_execute(args):
    cmds = ["brew"] + args
    return execute(cmds)


@contextlib.contextmanager
def brew_changeset(changeset):
    try:
        os.chdir(HOMEBREW_SCIENCE_ROOT)
        current_changeset = git_execute(["rev-parse", "HEAD"]).strip()
        try:
            git_execute(["checkout", changeset])
            yield
        finally:
            git_execute(["checkout", current_changeset])
    finally:
        # TODO: restore chdir
        pass

def git_execute(args):
    cmds = ["git"] + args
    return execute(cmds)


def execute(cmds):
    p = subprocess.Popen(cmds, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise CommandLineException(" ".join(cmds), stdout, stderr)
    return stdout


def brew_deps(package):
    stdout = brew_execute(["deps", package])
    return [p.strip() for p in stdout.split("\n") if p]


def brew_version_info(package):
    # TODO: could use tags instead - no big deal.
    stdout = brew_execute(["versions", package])
    version_parts = [WHITESPACE_PATTERN.split(l) for l in stdout.split("\n") if l and "git checkout" in l]
    info = [(p[0], p[3], HOMEBREW_SCIENCE_ROOT in p[4]) for p in version_parts]
    return info

if __name__ == "__main__":
    main()
