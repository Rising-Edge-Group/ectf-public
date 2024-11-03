import click
from pathlib import Path
from session import echoSession
from notification_alerts import FlagAlerts
import utils


@click.group()
@click.option(
    "--config", default="~/.echoctf.json", help="Path to the JSON configuration file."
)
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """
    Command Line Interface (CLI) for interacting with echoCTF.RED\n
    Default configuration file: ~/.echoctf.json
    """
    config_path = Path(
        config
    ).expanduser()  # Expands `~` to the current user's home directory
    settings = utils.load_configuration(config_path)

    instance_url = settings.get("instance_url") or click.prompt(
        "echoCTF.RED instance URL"
    )
    identity_cookie = settings.get("_identity-red") or click.prompt(
        "Identity-RED Cookie: ", hide_input=True
    )

    ctx.obj = echoSession(instance_url, identity_cookie)


@cli.command()
@click.argument("target_id", type=int)
@click.pass_obj
def spin(session: echoSession, target_id: int) -> None:
    """
    Spins the target specified by `TARGET_ID`.
    """
    click.echo(f"Spinning target with ID: {target_id}")
    session.spin_target(target_id)


@cli.command()
@click.argument("flag", type=str)
@click.pass_obj
def claim(session: echoSession, flag: str) -> None:
    """
    Attempts to claim the specified `FLAG`.
    """
    click.echo("Attempting to claim the given flag...")
    claim_result = session.claim_flag(flag)
    default_message = (
        "(?) UNKNOWN Response. This is PROBABLY a bug and should be reported."
    )

    messages = {
        FlagAlerts.FLAG_DOES_NOT_EXIST: "(!) The specified flag does not exist.",
        FlagAlerts.FLAG_CLAIMED_BEFORE: "(!) This flag has already been claimed.",
        FlagAlerts.FLAG_CLAIMED_FOR_POINTS: "Flag claimed successfully!",
        FlagAlerts.SERVICE_DISCOVERY_REQUIRED: "(!) You need to discover at least one service before claiming this flag.",
        FlagAlerts.ACCESS_DENIED: "(!) You don't have access to the network to which this flag's target belongs.",
        FlagAlerts.UNKNOWN: default_message,
    }

    click.echo(messages.get(claim_result, default_message))


if __name__ == "__main__":
    cli()
