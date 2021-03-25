import nox
from nox_poetry import session

package = "session", "data_transfer"
nox.options.sessions = "black", "lint", "mypy", "tests", "isort"
locations = "consumer", "data_transfer", "tests", "noxfile.py", "cli.py"


@session(python=["3.8"])
def black(session: nox.Session) -> None:
    """Automatic format code following black codestyle:
    https://github.com/psf/black
    """
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@session(python=["3.8"])
def isort(session: nox.Session) -> None:
    """Automatic order import statements"""
    args = session.posargs or locations
    session.install("isort")
    session.run("isort", *args)


@session(python=["3.8"])
def mypy(session: nox.Session) -> None:
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)


@session(python=["3.8"])
def lint(session: nox.Session) -> None:
    """Provide lint warnings to help enforce style guide."""
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-aaa",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
    )
    session.run("flake8", *args)


@session(python=["3.8"])
def tests(session: nox.Session) -> None:
    """Setup for automated testing with pytest"""
    session.run("poetry", "run", "pytest", "-vs")

    # NOTE: Old and perhaps proper approach below. But issues prevent it to be ran on
    # all dev's machines. Needs further investigation. Definitely a local issue.

    # args = session.posargs
    # session.run("poetry", "install", "--no-dev", external=True)
    # install_with_constraints(session, "pytest")
    # session.run("pytest", *args)
