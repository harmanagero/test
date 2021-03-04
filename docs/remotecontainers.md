# Remote Containers

The Visual Studio Code Remote - Containers extension lets you use a Docker container as a full-featured development environment. It allows you to open any folder inside (or mounted into) a container and take advantage of Visual Studio Code's full feature set.

## Prerequisite

1. Visual studio code should be installed on your machine.
2. Docker Desktop must be installed.

## System requirements

Local:

    Windows: Docker Desktop 2.0+ on Windows 10 Pro/Enterprise. Windows 10 Home (2004+) requires Docker Desktop 2.3+ and the WSL 2 back-end. (Docker Toolbox is not supported. Windows container images are not supported.)
    macOS: Docker Desktop 2.0+.
    Linux: Docker CE/EE 18.06+ and Docker Compose 1.21+. (The Ubuntu snap package is not supported.)

## Installation

To get started, follow these steps:

1. Install and configure Docker for your operating system.

    Windows / macOS:

        Install Docker Desktop for Windows/Mac.

    Linux:

        Follow the official install instructions for Docker CE/EE for your distribution. If you are using Docker Compose, follow the Docker Compose directions as well.

        Add your user to the docker group by using a terminal to run: sudo usermod -aG docker $USER

        Sign out and back in again so your changes take effect.

2. Install Visual Studio Code or Visual Studio Code Insiders.

3. Install the Remote Development extension pack.

## Structure

In Visual Studio Code, add Remote-containers extension if not already added. It will add devcontainer.json in .devcontainer folder.

### Devcontainer.json file

VS Code's container configuration is stored in a devcontainer.json file. This file is similar to the launch.json file for debugging configurations, but is used for launching (or attaching to) your development container instead. A devcontainer.json file in your project tells VS Code how to access (or create) a development container with a well-defined tool and runtime stack. This container can be used to run an application or to sandbox tools, libraries, or runtimes needed for working with a codebase. Following file is created for connected vehicle gateway project.

* [.devcontainer/devcontainer.json](/.devcontainer/devcontainer.json)

### Managing extensions#

You can also specify any extensions to install once the container is running or post-create commands to prepare the environment. The dev container configuration is either located under .devcontainer/devcontainer.json or stored as a .devcontainer.json file (note the dot-prefix) in the root of your project.

You can use any image, Dockerfile, or set of Docker Compose files as a starting point.

[remote-container](https://code.visualstudio.com/docs/remote/containers)
