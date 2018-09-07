import click

from signal_analog.util import pp_json


class SignalAnalogConfig(object):

    def __init__(self):
        self.resources = None
        self.api_key = None


pass_config = click.make_pass_decorator(SignalAnalogConfig, ensure=True)


def invoke(resource, action, api_key, **kwargs):
    """Attempt to invoke the provided action on each resource.

        Arguments:
            resource: Object defining a Sfx resource (chart, dashboard, dashboard group, etc)
            action: String to create, update, read, or delete a resource
            api_key: String

        Returns:
            The response from the action taken.
    """
    res = resource.with_api_token(api_key)
    try:
        action_fn = getattr(res, action)
    except AttributeError:
        msg = "Attempted to execute unsupported action '{0}' on resource '{1}'."
        click.echo(msg.format(action, resource.__get__('name')))
        exit()

    return action_fn(**kwargs)


class CliBuilder(object):

    def __init__(self):
        self.resources = []

    def with_resources(self, *args):
        """Resources to build with the CLI
        """
        self.resources = args
        return self

    def build(self):
        """CLI commands to define actions taken on resources such as create, update, read, or delete."""

        @click.group()
        @click.option('--api-key', help='Your SignalFx API key')
        @pass_config
        def cli(ctx, api_key):
            ctx.resources = self.resources
            ctx.api_key = api_key

        @cli.command()
        @click.option('-f', '--force', type=bool, is_flag=True, default=False,
                      help='Force the creation of new resources')
        @click.option('-i', '--interactive', type=bool, is_flag=True, default=False,
                      help='Interactive mode of creating new resources')
        @click.option('-d', '--dry-run', type=bool, is_flag=True, default=False,
                      help='Print the configuration that would be sent to SignalFx')
        @pass_config
        def create(ctx, force, interactive, dry_run):
            for resource in ctx.resources:
                res = invoke(resource, 'create', ctx.api_key,
                             force=force, interactive=interactive, dry_run=dry_run)
                pp_json(res)

        @cli.command()
        @click.option('--name', type=str, nargs=1, help='New Dashboard name')
        @click.option('--description', type=str, nargs=1,
                      help='New Dashboard description')
        @click.option('-d', '--dry-run', type=bool, is_flag=True, default=False,
                      help='Print the configuration that would be sent to SignalFx')
        @pass_config
        def update(ctx, name, description, dry_run):
            for resource in ctx.resources:
                res = invoke(resource, 'update', ctx.api_key,
                             name=name, description=description, dry_run=dry_run)
                pp_json(res)

        @cli.command()
        @pass_config
        def read(ctx):
            for resource in ctx.resources:
                click.echo(invoke(resource, 'read', ctx.api_key))

        @cli.command()
        @pass_config
        def delete(ctx):
            for resource in ctx.resources:
                click.echo(invoke(resource, 'delete', ctx.api_key))

        return cli
