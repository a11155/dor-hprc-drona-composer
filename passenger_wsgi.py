from app import app

application = app

if __name__ == '__main__':
    socketio.run(application)

