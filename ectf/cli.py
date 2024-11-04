"""
MIT License

Copyright (c) 2024 - "Rising Edge" Group

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

import click
from pathlib import Path
from .session import echoSession
from .notification_alerts import FlagAlerts
from . import utils


@click.group()
@click.option(
    "--config", default="~/.echoctf.json", help="Path to the JSON configuration file."
)
@click.pass_context
def main(ctx: click.Context, config: str) -> None:
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


@main.command()
@click.argument("target_id", type=int)
@click.pass_obj
def spin(session: echoSession, target_id: int) -> None:
    """
    Spins the target specified by `TARGET_ID`.
    """
    click.echo(f"Spinning target with ID: {target_id}")
    session.spin_target(target_id)


@main.command()
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
    main()
