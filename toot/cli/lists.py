import click
import json as pyjson

from toot import api, config
from toot.cli import Context, cli, pass_context, json_option
from toot.output import print_list_accounts, print_lists, print_warning


@cli.group(invoke_without_command=True)
@click.pass_context
def lists(ctx: click.Context):
    """Display and manage lists"""
    if ctx.invoked_subcommand is None:
        print_warning("`toot lists` is deprecated in favour of `toot lists list`.\n" +
                      "Run `toot lists -h` to see other list-related commands.")

        user, app = config.get_active_user_app()
        if not user or not app:
            raise click.ClickException("This command requires you to be logged in.")

        lists = api.get_lists(app, user)
        if lists:
            print_lists(lists)
        else:
            click.echo("You have no lists defined.")


@lists.command()
@json_option
@pass_context
def list(ctx: Context, json: bool):
    """List all your lists"""
    lists = api.get_lists(ctx.app, ctx.user)

    if json:
        click.echo(pyjson.dumps(lists))
    else:
        if lists:
            print_lists(lists)
        else:
            click.echo("You have no lists defined.")


@lists.command()
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@json_option
@pass_context
def accounts(ctx: Context, title: str, id: str, json: bool):
    """List the accounts in a list"""
    list_id = _get_list_id(ctx, title, id)
    response = api.get_list_accounts(ctx.app, ctx.user, list_id)

    if json:
        click.echo(pyjson.dumps(response))
    else:
        print_list_accounts(response)


@lists.command()
@click.argument("title")
@click.option(
    "--replies-policy",
    type=click.Choice(["followed", "list", "none"]),
    default="none",
    help="Replies policy"
)
@json_option
@pass_context
def create(ctx: Context, title: str, replies_policy: str, json: bool):
    """Create a list"""
    response = api.create_list(ctx.app, ctx.user, title=title, replies_policy=replies_policy)
    if json:
        print(response.text)
    else:
        click.secho(f"✓ List \"{title}\" created.", fg="green")


@lists.command()
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@json_option
@pass_context
def delete(ctx: Context, title: str, id: str, json: bool):
    """Delete a list"""
    list_id = _get_list_id(ctx, title, id)
    response = api.delete_list(ctx.app, ctx.user, list_id)
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ List \"{title if title else id}\" deleted.", fg="green")


@lists.command()
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@json_option
@pass_context
def add(ctx: Context, title: str, account: str, id: str, json: bool):
    """Add an account to a list"""
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)

    try:
        response = api.add_accounts_to_list(ctx.app, ctx.user, list_id, [found_account["id"]])
        if json:
            click.echo(response.text)
        else:
            click.secho(f"✓ Added account \"{account}\"", fg="green")
    except Exception:
        # TODO: this is slow, improve
        # if we failed to add the account, try to give a
        # more specific error message than "record not found"
        my_accounts = api.followers(ctx.app, ctx.user, found_account["id"])
        found = False
        if my_accounts:
            for my_account in my_accounts:
                if my_account["id"] == found_account["id"]:
                    found = True
                    break
        if found is False:
            raise click.ClickException(f"You must follow @{account} before adding this account to a list.")
        raise


@lists.command()
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@json_option
@pass_context
def remove(ctx: Context, title: str, account: str, id: str, json: bool):
    """Remove an account from a list"""
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)
    response = api.remove_accounts_from_list(ctx.app, ctx.user, list_id, [found_account["id"]])
    if json:
        click.echo(response.text)
    else:
        click.secho(f"✓ Removed account \"{account}\"", fg="green")


# -- Deprecated commands -------------------------------------------------------


@cli.command(name="list_accounts", hidden=True)
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_accounts(ctx: Context, title: str, id: str):
    """List the accounts in a list"""
    print_warning("`toot list_accounts` is deprecated in favour of `toot lists accounts`")
    list_id = _get_list_id(ctx, title, id)
    response = api.get_list_accounts(ctx.app, ctx.user, list_id)
    print_list_accounts(response)


@cli.command(name="list_create", hidden=True)
@click.argument("title")
@click.option(
    "--replies-policy",
    type=click.Choice(["followed", "list", "none"]),
    default="none",
    help="Replies policy"
)
@pass_context
def list_create(ctx: Context, title: str, replies_policy: str):
    """Create a list"""
    print_warning("`toot list_create` is deprecated in favour of `toot lists create`")
    api.create_list(ctx.app, ctx.user, title=title, replies_policy=replies_policy)
    click.secho(f"✓ List \"{title}\" created.", fg="green")


@cli.command(name="list_delete", hidden=True)
@click.argument("title", required=False)
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_delete(ctx: Context, title: str, id: str):
    """Delete a list"""
    print_warning("`toot list_delete` is deprecated in favour of `toot lists delete`")
    list_id = _get_list_id(ctx, title, id)
    api.delete_list(ctx.app, ctx.user, list_id)
    click.secho(f"✓ List \"{title if title else id}\" deleted.", fg="green")


@cli.command(name="list_add", hidden=True)
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_add(ctx: Context, title: str, account: str, id: str):
    """Add an account to a list"""
    print_warning("`toot list_add` is deprecated in favour of `toot lists add`")
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)

    try:
        api.add_accounts_to_list(ctx.app, ctx.user, list_id, [found_account["id"]])
    except Exception:
        # if we failed to add the account, try to give a
        # more specific error message than "record not found"
        my_accounts = api.followers(ctx.app, ctx.user, found_account["id"])
        found = False
        if my_accounts:
            for my_account in my_accounts:
                if my_account["id"] == found_account["id"]:
                    found = True
                    break
        if found is False:
            raise click.ClickException(f"You must follow @{account} before adding this account to a list.")
        raise

    click.secho(f"✓ Added account \"{account}\"", fg="green")


@cli.command(name="list_remove", hidden=True)
@click.argument("title", required=False)
@click.argument("account")
@click.option("--id", help="List ID if not title is given")
@pass_context
def list_remove(ctx: Context, title: str, account: str, id: str):
    """Remove an account from a list"""
    print_warning("`toot list_remove` is deprecated in favour of `toot lists remove`")
    list_id = _get_list_id(ctx, title, id)
    found_account = api.find_account(ctx.app, ctx.user, account)
    api.remove_accounts_from_list(ctx.app, ctx.user, list_id, [found_account["id"]])
    click.secho(f"✓ Removed account \"{account}\"", fg="green")


def _get_list_id(ctx: Context, title, list_id):
    if not list_id and not title:
        raise click.ClickException("Please specify list title or ID")

    lists = api.get_lists(ctx.app, ctx.user)
    matched_ids = [
        list["id"] for list in lists
        if list["title"].lower() == title.lower() or list["id"] == list_id
    ]

    if not matched_ids:
        raise click.ClickException("List not found")

    if len(matched_ids) > 1:
        raise click.ClickException("Found multiple lists with the same title, please specify the ID instead")

    return matched_ids[0]
