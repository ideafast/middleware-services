import subprocess  # noqa
from typing import Any

import click
import uvicorn

REGISTRIES = {
    "consumer": "ideafast/middleware-consumer",
    "dtransfer": "ideafast/middleware-dtransfer",
}

DOCKER_FILES = {
    "consumer": "Dockerfile",
    "dtransfer": "Dtransfer.Dockerfile",
}


def run_command(command: str, capture: bool = False) -> subprocess.CompletedProcess:
    """Helper method to run shell commands"""
    return subprocess.run([command], shell=True, capture_output=capture)  # noqa


def git_tag_local(version: str) -> None:
    """Create lightweight git tag with version against local branch."""
    run_command(f"git tag {version}")


def git_push_tag_remote(version: str) -> None:
    """Push local tag to git remote origin."""
    run_command(f"git push origin {version}")


def docker_image_exists(version: str, repo: str) -> Any:
    """Check if docker image exists based on version."""
    command = f"docker images -q {REGISTRIES[repo]}:{version}"
    res = run_command(command, True)
    # The hash ID of the image if it exists
    return res.stdout.decode("ascii").rstrip()


def validate_repo_name(repo: str) -> None:
    """Ensures Docker arguments are valid, e.g., consumer or dtransfer."""
    if repo not in DOCKER_FILES:
        names = " or ".join(DOCKER_FILES.keys())
        raise click.ClickException(f"Repository name must be {names}")


def run_uvicorn(
    app: str, port: int, host: str = "0.0.0.0", reload: bool = True  # noqa
) -> None:
    """Run run_uvicorn for local development."""
    uvicorn.run(app, host=host, port=port, reload=reload)


@click.group()
def cli() -> None:
    """CLI for building and deploying middleware in Docker."""


@cli.command()
def consumer() -> None:
    """Run the consumer app for local development."""
    run_uvicorn("consumer.main:consumer", 8000)


@cli.command()
@click.argument("repo")
@click.argument("version")
def build(repo: str, version: str) -> None:
    """Build docker image."""
    validate_repo_name(repo)

    if docker_image_exists(version, repo):
        message = "THIS VERSION ALREADY EXISTS.\nDo you want to rebuild it?"
        click.confirm(message, abort=True)

    git_tag_local(version)

    run_command(
        f"docker build -f {DOCKER_FILES[repo]} -t {REGISTRIES[repo]}:{version} ."
    )


@cli.command()
@click.argument("repo")
@click.argument("version")
def publish(repo: str, version: str) -> None:
    """Publish git tag and docker image."""
    validate_repo_name(repo)
    run_command(f"docker push {REGISTRIES[repo]}:{version}")
    message = "Do you want to push this tag to GitHub too?"
    click.confirm(message, abort=True)
    git_push_tag_remote(version)


@cli.command()
def compose() -> None:
    """Run docker compose locally."""
    run_command("docker-compose up -d")


if __name__ == "__main__":
    cli()
