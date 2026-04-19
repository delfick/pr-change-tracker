import os

import click


class EnvSecret(click.ParamType):
    name = "env_secret"

    def convert(
        self, value: object, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
        if not isinstance(value, str):
            self.fail("Expect env value to be a str", param, ctx)
        if value.startswith("env:"):
            env_name = value[4:]
            from_env = os.environ.get(env_name)
            if from_env is None:
                raise self.fail(f"No value found for environment variable ${env_name}", param, ctx)
            value = from_env
        return value


class CLIOptions:
    postgres_url_option = click.option(
        "--postgres-url",
        help="The url for the postgres database",
        default="env:PR_CHANGE_TRACKER_ALEMBIC_DB_URL",
        type=EnvSecret(),
    )
    dev_logging_option = click.option(
        "--dev-logging",
        is_flag=True,
        help="Print out the logs as human readable",
    )
    github_api_token_option = click.option(
        "--github-api-token",
        default="env:PR_CHANGE_TRACKER_GITHUB_API_TOKEN",
        type=EnvSecret(),
        help="Auth token for the github API",
    )
    github_api_requester_option = click.option(
        "--github-api-requester",
        default="env:PR_CHANGE_TRACKER_GITHUB_API_REQUESTER",
        type=EnvSecret(),
        help="To be added to the headers sent to the github API",
    )
    github_webhook_secret_option = click.option(
        "--github-webhook-secret",
        help="The value of the secret for the github webhooks or 'env:NAME_OF_ENV_VAR'",
        default="env:PR_CHANGE_TRACKER_GITHUB_WEBHOOK_SECRET",
        type=EnvSecret(),
    )
    provide_git_webhook_debug_endpoint_option = click.option(
        "--provide-git-webhook-debug-endpoint",
        help="Used to enable an endpoint to print out full incoming http requests from the github webhook for test fixtures",
        is_flag=True,
    )
    port_option = click.option(
        "--port",
        help="The port to expose the app from. Defaults to $PR_CHANGE_TRACKER_SERVER_PORT or 3000",
        default=os.environ.get("PR_CHANGE_TRACKER_SERVER_PORT", 3000),
        type=int,
    )
