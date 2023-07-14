from django.conf import settings

import boto3


class AWSECSHandler:
    """AWS ECS service handler."""

    service_name = 'ecs'

    def __init__(self):
        """Constructor."""
        self.client = boto3.client(
            service_name=self.service_name,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
        )
        self.container_default_name = getattr(
            settings, 'ECS_CONTAINER_NAME', 'gunicorn')
        self.command_name = getattr(
            settings, 'COMMAND_NAME', 'run_task')

    def run_task(self, command=None, **kwargs):
        """Run Task definition on ECS Cluster."""
        run_kwargs = {
            'cluster': settings.AWS_CLUSTER,
            'launchType': settings.AWS_CLUSTER_LAUNCH,
            'taskDefinition': settings.AWS_TASK_DEFINITION,
            **kwargs,
        }

        if settings.AWS_CLUSTER_LAUNCH == 'FARGATE':
            run_kwargs['networkConfiguration'] = {
                'awsvpcConfiguration': {
                    'subnets': settings.AWS_EC2_SUBNETS,
                    'securityGroups': settings.AWS_EC2_SECURITY_GROUPS,
                    'assignPublicIp': 'DISABLED'
                }
            }

        if command:
            command = command.split() if isinstance(command, str) else command
            run_kwargs['overrides'] = {
                'containerOverrides': [
                    {
                        'name': self.container_default_name,
                        'command': command,
                    }
                ]
            }
        return self.client.run_task(**run_kwargs)
