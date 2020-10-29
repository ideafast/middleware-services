import subprocess
import click


REGISTRY = 'ideafast/middleware'


def run_command(command: str, capture: bool = False) -> None:
    """Helper method to run shell commands"""
    return subprocess.run([command], shell=True, capture_output=capture)


def git_tag_local(version: str) -> None:
    """Create lightweight git tag with version against local branch."""
    run_command(f"git tag {version}")


def git_push_tag_remote(version: str) -> None:
    """Push local tag to git remote origin."""
    run_command(f"git push origin {version}")


def docker_image_exists(version: str) -> str:
    """Check if docker image exists based on version."""
    command = f'docker images -q {REGISTRY}:{version}'
    res = run_command(command, True)
    image_hash = res.stdout.decode('ascii').rstrip()
    return image_hash


@click.group()
def cli():
    """CLI for building and deploying middleware in Docker."""


@cli.command()
@click.argument('version')
def build(version: str) -> None:
    """Build docker image."""
    message = "THIS VERSION ALREADY EXISTS.\nDo you want to rebuild it?"
    if docker_image_exists(version):
        click.confirm(message, abort=True)
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
