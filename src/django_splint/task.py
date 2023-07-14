from django_splint.utils.aws.ecs import AWSECSHandler


class SplintTask(AWSECSHandler):

    def __init__(self):
        """Constructor."""
        self.module = self.__class__.__module__
        self.clazz = self.__class__.__name__
        super().__init__()

    def run_task(self, *args, **kwargs):
        """Run task in AWS ECS."""
        return super().run_task(
            command=f'python manage.py {self.command_name} {self.module} {self.clazz} ' +
            ' '.join(map(str, args)), **kwargs)

    def run(self, *args):
        """Execute task."""
        raise NotImplementedError('Task not implemented.')
