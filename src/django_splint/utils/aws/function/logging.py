"""Lambda logging helper.

Returns a Logger with log level set based on env variables.
"""
from aws_lambda_powertools import Logger as LambdaLogger


def format_extra_params(func):
    def wrapper(instance, msg, *args, stacklevel: int = 4, extra=None, **kwargs):
        # formating extra kwargs for avoid
        # Attempt to overwrite except
        extra = extra or {}
        extra = {**extra, **kwargs}
        module = extra.pop("module", "module_undefined")
        clazz = extra.pop("clazz", "class_undefined")
        method = extra.pop("method", "method_undefined")
        result = func(
            instance,
            msg,
            *args,
            stacklevel=stacklevel,
            extra={
                "_module": module,
                "_class": clazz,
                "_method": method,
                "data": extra,
            },
        )
        return result
    return wrapper


class Logger(LambdaLogger):
    @format_extra_params
    def info(self, msg, *args, **kwargs):
        return super().info(msg, *args, **kwargs)

    @format_extra_params
    def error(self, msg, *args, **kwargs):
        return super().error(msg, *args, **kwargs)

    @format_extra_params
    def debug(self, msg, *args, **kwargs):
        return super().debug(msg, *args, **kwargs)

    @format_extra_params
    def exception(self, msg, *args, **kwargs):
        return super().exception(msg, *args, **kwargs)

    @format_extra_params
    def warning(self, msg, *args, **kwargs):
        return super().warning(msg, *args, **kwargs)
