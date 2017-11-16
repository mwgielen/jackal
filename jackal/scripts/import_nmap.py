#!/usr/bin/env python3
from jackal import Core
from jackal.utils import import_nmap


def main():
    core = Core(use_pipe=False)
    if core.arguments.file:
        import_nmap(core.arguments.file)


if __name__ == '__main__':
   main()
