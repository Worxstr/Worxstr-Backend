from app import create_app, db, cli, socketio
from app.models import User, Job, TimeClock, ScheduleShift

application = create_app()
cli.register(application)

# run the app.
if __name__ == "__main__":
    socketio.run(application)


@application.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Job": Job,
        "TimeClock": TimeClock,
        "ScheduleShift": ScheduleShift,
    }
