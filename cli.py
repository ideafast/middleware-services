import subprocess
import click


REGISTRY = 'ideafast/middleware'


def run_command(command: str) -> None:
    """Helper method to run shell commands"""
    subprocess.run([command], shell=True)


def git_tag_local(version: str) -> None:
    """Create a local git lightweight with version."""
    run_command(f"git tag {version}")


def git_push_tag_remote(version: str) -> None:
    """Push local tag to git remote."""
    run_command(f"git push origin {version}")


@click.group()
def cli():
    """CLI for building and deploying middleware in Docker."""


@cli.command()
@click.argument('version')
def build(version: str) -> None:
    """Build docker image."""
    git_tag_local(version)
    run_command(f"docker build -t {REGISTRY}:{version} .")


@cli.command()
@click.argument('version')
def publish(version: str) -> None:
    """Publish git tag and docker image."""
    run_command(f"docker push {REGISTRY}:{version}")
    git_push_tag_remote(version)


@cli.command()
def compose() -> None:
    """Run docker compose locally."""
    run_command("docker-compose up -d")


if __name__ == '__main__':
    cli()
