from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=["settings.toml", ".secrets.toml"],
)


whitelist = [config.guild for config in settings.bot.whitelist]

if __name__ == "__main__":
    from pprint import pprint

    pprint(dict(settings))
