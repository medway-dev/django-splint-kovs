import boto3
from django.conf import settings


class AWSSQSHandler:
    """AWS ECS service handler."""

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_region_name=None):
        self.client = boto3.client(
            service_name=self.service_name,
            aws_access_key_id=aws_access_key_id or settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY,
            region_name=aws_region_name or settings.AWS_DEFAULT_REGION,
        )

    def send_message(self, **kwargs):
        attributes = kwargs.get("MessageAttributes")
        if attributes:
            self._sqs_attributes_cleaner(attributes)

        return self.client.send_message(**kwargs)

    def _sqs_attributes_cleaner(self, attributes):
        """Transform SQS attributes from Lambda event to SQS message."""
        d = dict.fromkeys(attributes)
        for k in d:
            if isinstance(attributes[k], dict):
                subd = dict.fromkeys(attributes[k])
                for subk in subd:
                    if not attributes[k][subk]:
                        del attributes[k][subk]
                    else:
                        attributes[k][
                            "".join(subk[:1].upper() + subk[1:])
                        ] = attributes[k].pop(subk)
