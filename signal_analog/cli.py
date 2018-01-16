import click


class SignalAnalogConfig(object):

    def __init__(self):
        self.resources = None
        self.api_key = None


pass_config = click.make_pass_decorator(SignalAnalogConfig, ensure=True)


def invoke(resource, action, api_key, **kwargs):
    """Attempt to invoke the provided action on each resource.

    Returns:
        The response from the action taken.
    """
    res = resource.with_api_token(api_key)
    try:
        action_fn = getattr(res, action)
    except AttributeError:
        click.echo('You dun goofed')
        click.exit()

    return action_fn(**kwargs)


class CliBuilder(object):

    def __init__(self):
        self.resources = []

    def with_resources(self, *args):
        self.resources = args
        return self

    def build(self):

        @click.group()
        @click.option('--api-key', help='Your SignalFx API key')
        @pass_config
        def cli(ctx, api_key):
            ctx.resources = self.resources
            ctx.api_key = api_key

        @cli.command()
        @click.option('-f', '--force', type=bool, is_flag=True, default=False, help='Force the creation of a new dashboard')
        @click.option('-i', '--interactive', type=bool, is_flag=True, default=False, help='Interactive mode of creating a new dashboard')
        @pass_config
        def create(ctx, force, interactive):
            click.echo('create')
            for resource in ctx.resources:
                click.echo(invoke(resource, 'create', ctx.api_key, force=force, interactive=interactive))

        @cli.command()
        @click.option('--name', type=str, nargs=1, help='New Dashboard name')
        @click.option('--description', type=str, nargs=1, help='New Dashboard description')
        @pass_config
        def update(ctx, name, description):
            click.echo('update')
            for resource in ctx.resources:
                click.echo(invoke(resource, 'update', ctx.api_key, name=name, description=description))

        @cli.command()
        @pass_config
        def delete(ctx):
            raise NotImplementedError('lol')

        @cli.command()
        @pass_config
        def read(ctx):
            raise NotImplementedError('lol')

        return cli
