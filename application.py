from app import create_app, db, cli, socketio
from app.models import Role, User, Job, TimeClock, ScheduleShift

application = create_app()
cli.register(application)

# run the app.
if __name__ == "__main__":
    socketio.run(application, host='0.0.0.0')


@application.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Job": Job,
        "TimeClock": TimeClock,
        "ScheduleShift": ScheduleShift,
        "Role": Role,
    }
