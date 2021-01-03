from app import create_app, db, cli
from app.models import User, Job, TimeClock, ScheduleShift

app = create_app()
cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Job': Job, 'TimeClock': TimeClock, 'ScheduleShift': ScheduleShift}