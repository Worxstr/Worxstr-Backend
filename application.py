from app import create_app, db, cli
from app.models import User, Job, TimeClock, ScheduleShift

application = create_app()
cli.register(application)

# run the app.
if __name__ == "__main__":
    application.run()

@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job, 'TimeClock': TimeClock, 'ScheduleShift': ScheduleShift}