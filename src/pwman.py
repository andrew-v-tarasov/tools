#!/usr/bin/env python3

import click
# from os import system
# from prompt_toolkit import prompt

import re
import sys
import libpwman


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        try:
            cmd_name = ALIASES[cmd_name].name
        except KeyError:
            pass
        return click.Group.get_command(self, ctx, cmd_name)


# @click.group()
# invoke_without_command = True, context_settings = dict(ignore_unknown_options = True, allow_extra_args = True))
@click.command(cls=AliasedGroup)
@click.option("--db-fname", default="/home/andrew/VaultDocuments/pwman.db")
@click.pass_context
def cli(ctx, db_fname):
    ctx.ensure_object(dict)
    ctx.obj['compiledPtn'] = re.compile(".*echo \"(.+)\" \| ([a-z0-9]+) \| cut -c +([0-9]+)\-([0-9]+)(.*)")
    ctx.obj['db_fname'] = db_fname


'''
    if ctx.invoked_subcommand is None:
        cmdList = comlist(cli)
        while True:
            cmd = prompt("-> ").split()
            print(ctx)
            print(cli.list_commands(ctx))
            print(cli.get_command(ctx, cmd[0]))
            print(cmdList[cmd[0]])
#            if cmd[0] == "list":
#                listInt(cmd[1])
            ctx.invoke(cmdList[cmd[0]], name=cmd[1])
'''


@cli.command(help="List table contents. If no table name specified, list existing tables.")
@click.pass_context
@click.option("-t", "--table", default="", help="table name")
def list(ctx, table):
    try:
        ret_list = libpwman.list(ctx.obj['db_fname'], table)
        if table == "":
            [click.echo(line[0]) for line in ret_list]
        else:
            [click.echo(line) for line in ret_list]
    except ValueError as e:
        click.echo("Oops, " + str(e))
        if "no such table" in str(e):
            click.echo("Available tables:")
            tables = libpwman.list(ctx.obj['db_fname'], "")
            [click.echo("  " + table[0]) for table in tables]
        exit(1)


@cli.command(help="Add table")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
def addtable(ctx, table):
    libpwman.addtable(ctx.obj['db_fname'], table)


@cli.command(help="Remove table")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
def rmtable(ctx, table):
    if click.confirm("Remove table " + table + "?", abort=False):
        libpwman.rmtable(ctx.obj['db_fname'], table)


@cli.command(help="Rename table")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
@click.option("-n", "--name", required=True, help="table new name")
def movetable(ctx, table, name):
    libpwman.mvtable(ctx.obj['db_fname'], table, name)


@cli.command(help="Add pw line.")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
@click.option("-n", "--name", required=True, help="pw name")
@click.option("-c", "--cipher", help="cipher name", default="")
@click.option("-b", "--nbeg", help="cut from", default="1")
@click.option("-e", "--nend", help="cut to", default="10")
@click.option("-s", "--salt", help="add in the end", default="")
@click.option("-x", "--text", help="commentary", default="")
def add(ctx, table, name, cipher, nbeg, nend, salt, text):
    try:
        libpwman.adduser(ctx.obj['db_fname'], table, name, cipher, nbeg, nend, salt, text)
    except ValueError as e:
        click.echo("Error!\n" + str(e))
        exit(1)
    users = libpwman.searchusers(ctx.obj['db_fname'], table, name, "", "", "")
    [click.echo(user) for user in users]


@cli.command(help="Remove pw line.")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
@click.option("-n", "--name", required=True, help="pw name")
def remove(ctx, table, name):
    users = libpwman.searchusers(ctx.obj['db_fname'], table, name, "", "", "")
    if not users:
        click.echo("Nothing found.")
        return
    [click.echo(user) for user in users]
    if click.confirm("Delete this line(s)?", abort=False):
        for line in users:
            libpwman.rmuser(ctx.obj['db_fname'], table, line[0])
            click.echo("User " + line[0] + " removed.")
    else:
        click.echo("Abort.")


@cli.command(help="Move pw line.")
@click.pass_context
@click.option("-f", "--from-table", 'from_table', required=True, help="table name")
@click.option("-t", "--to-table", 'to_table', required=True, help="table name")
@click.option("-n", "--name", required=True, help="pw name")
def move(ctx, from_table, to_table, name):
    users = libpwman.searchusers(ctx.obj['db_fname'], from_table, name, "", "", "")
    if users:
        [click.echo(line) for line in users]
        if click.confirm("Move this line(s) to table " + to_table + "?", abort=False):
            for line in users:
                name = str(line[0])
                cipher = str(line[1])
                nbeg = str(line[2])
                nend = str(line[3])
                salt = str(line[4])
                text = str(line[5])
                libpwman.adduser(ctx.obj['db_fname'], to_table, name, cipher, nbeg, nend, salt, text)
                libpwman.rmuser(ctx.obj['db_fname'], from_table, name)
        return
    click.echo("Nothing found.")


@cli.command(help="Search pw lines.")
@click.pass_context
@click.option("-t", "--table", default="", help="table name")
@click.option("-n", "--name", default="", help="pw name")
@click.option("-c", "--cipher", default="", help="cipher name")
@click.option("-b", "--nbeg", default="", help="cut from")
@click.option("-e", "--nend", default="", help="cut to")
@click.option("-s", "--salt", help="add in the end", default="")
@click.option("-x", "--text", help="commentary", default="")
def search(ctx, table, name, cipher, nbeg, nend, salt, text):
    tables = [(table, "")]
    if table == "":
        tables = libpwman.list(ctx.obj['db_fname'], "")
    for cur_table in tables:
        try:
            curLines = libpwman.searchusers(ctx.obj['db_fname'], cur_table[0], name, cipher, nbeg, nend, salt, text)
            if curLines:
                click.echo("Table: " + cur_table[0])
                [click.echo("   " + str(line)) for line in curLines]
        except ValueError as e:
            click.echo("Oops, " + str(e))
            if "no such table" in str(e):
                click.echo("Available tables:")
                tables = libpwman.list(ctx.obj['db_fname'], "")
                [click.echo("  " + line[0]) for line in tables]
            exit(1)


@cli.command(help="Show passwords.")
@click.pass_context
@click.option("-t", "--table", required=True, help="table name")
@click.option("-n", "--name", required=True, help="pw name")
def password(ctx, table, name):
    for (user, passwd) in libpwman.pwusers(ctx.obj['db_fname'], table, name):
        click.echo(user + ": " + passwd)


@cli.command(help="Import new names from file.")
@click.pass_context
@click.option("-f", "--filename", required=True, help="file with new names.")
@click.option("-n", "--tablename", help="Table name. If no name given, use file name as table name.")
def addfile(ctx, filename, tablename):
    if tablename is None:
        click.echo("no bale name")
    with open(filename) as f:
        for cLine in f:
            print("-----------------------------------")
            print(cLine)
            myMatch = ctx.obj["compiledPtn"].findall(cLine)
            if myMatch is None or myMatch == []:
                print("Nothing found")
                print(cLine, file=sys.stderr)
            else:
                print(myMatch)
                myMatch = myMatch[0]
                print(myMatch)
                ctx.invoke(
                    add, table=tablename, name=myMatch[0], cipher=myMatch[1].replace('sum', ''),
                    nbeg=myMatch[2], nend=myMatch[3], salt=myMatch[4], text="")
            print("-----------------------------------")


@cli.command()
def quit():
    exit(0)


def comlist(obj):
    return {name: value for name, value in obj.commands.items()}


ALIASES = {
    "ls": list,
    "mv": move,
    "pw": password,
    "rm": remove,
    "se": search
}

if __name__ == '__main__':
    cli()
